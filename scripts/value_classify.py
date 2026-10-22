"""评论价值识别 · 第 3 步：用两种方法给待标注的 150 条评论自动分类。

方法 A（规则 + 统计）：
  1. 去掉标点后 ≥ 12 字，且至少 4 条评论互相几乎一样 → 模板重复
  2. 让微调好的抽取模型抽方面；一个方面都没抽到 → 整体负面为空洞差评，否则为无信息量
  3. 整体正面、所有方面都是正面、套话程度 ≥ 0.4 → 套话好评
  4. 其余 → 有效评论

方法 B（大模型直接判断）：把定义、判断规则、重复提示交给老师模型，让它直接选一类。

方法 C（组合）：用 B 的结果，但 B 判成空洞差评/无信息量、而抽取模型抽到了具体方面时，改判为有效评论。

第二轮的阈值和规则是看了开发集（dev，第一轮的 150 条）之后改的：
  - 只有 2 条一样的多半是同一人重复提交，人工 28 条里 22 条标为有效 → 模板门槛从"≥2 条"提到"≥4 条"
  - 大模型常把"卡！严重卡！垃圾！"这类语气激烈但有具体问题的差评判成空洞差评 → 加规则，并加组合方法 C
  - 人工的实际标准是"内容具体就算有效" → 有效评论的优先级提到套话、空洞之前
测试集（test）上的分数才是可信的。

用法：uv run python scripts/value_classify.py --split test
输出：results/value_<split>_preds.jsonl
"""
import argparse
import gc
import json
import os
import sys

import mlx.core as mx
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import parse_output  # noqa: E402
from gen import extract, load_model  # noqa: E402

STUDENT, ADAPTER = "mlx-community/Qwen3-1.7B-bf16", "adapters_best"
TEACHER = "mlx-community/Qwen3-30B-A3B-Instruct-2507-4bit"
MIN_TEMPLATE_LEN = 12
MIN_TEMPLATE_GROUP = 4
GENERIC_THRESHOLD = 0.4

VALUES = {
    "有效评论": "提到了具体方面或细节，商家能知道好在哪、差在哪",
    "模板重复": "很多人发了几乎一模一样的内容，像复制粘贴、刷单、返现好评",
    "套话好评": "好评，但放在任何商品下都成立（质量好、发货快、非常满意），没有这个商品特有的细节",
    "无信息量": "没有具体内容的好评或中性评价（不错、还行、好好好）",
    "空洞差评": "表达不满，但没说具体哪里不好（垃圾、差评、不要买）",
}
JUDGE_RULES = [
    "按这个顺序选第一个符合的：模板重复 → 有效评论 → 套话好评 → 空洞差评 / 无信息量",
    "只有出现\"系统提示：数据里共有 N 条几乎相同的评论\"时才可能是模板重复，没有这个提示就不要选模板重复",
    "短评论和别人重复不算模板重复：大家都可能写\"不错\"",
    "只要说出了具体的问题或细节，就算有效评论，哪怕很短、哪怕语气激烈或骂人："
    "\"卡！严重卡！垃圾！\"\"口袋缝到裤子上了，次品\"\"没收到货\"都是有效评论",
    "空洞差评只用于完全没说具体哪里不好的：\"垃圾\"\"差评\"\"不怎么样\"\"大家不要买\"\"与描述不符\"",
    "套话好评：只有\"质量不错、很满意、发货快、下次还来、支持京东\"这类放到任何商品下都成立的好话",
    "系统文字、和商品无关的内容（新闻、口号、凑字数）算无信息量",
]
JUDGE_SYSTEM = (
    "你是电商平台的评论质量审核员。判断一条用户评论对商家的参考价值，从下面五类里选一类：\n"
    + "\n".join(f"- {k}：{v}" for k, v in VALUES.items())
    + "\n判断规则：\n" + "\n".join(f"- {r}" for r in JUDGE_RULES)
    + "\n只输出一个 JSON：{\"分类\": 类名}"
)


def rule_classify(r, extraction):
    if r["nlen"] >= MIN_TEMPLATE_LEN and r["group_size"] >= MIN_TEMPLATE_GROUP:
        return "模板重复"
    if extraction is None:  # 抽取失败时按"有效"兜底，宁可漏判也不误伤
        return "有效评论"
    if not extraction["方面"]:
        return "空洞差评" if extraction["整体情感"] == "负面" else "无信息量"
    all_positive = extraction["整体情感"] == "正面" and all(a["情感"] == "正面" for a in extraction["方面"])
    if all_positive and r["generic_ratio"] >= GENERIC_THRESHOLD:
        return "套话好评"
    return "有效评论"


def combine(llm, extraction):
    """方法 C：大模型说"没内容"，但抽取模型抽到了具体方面 → 以抽取模型为准。"""
    concrete = extraction and any(a["方面"] != "其他" for a in extraction["方面"])
    if llm in ("空洞差评", "无信息量") and concrete:
        return "有效评论"
    return llm or "有效评论"


# 示例是新写的，不是开发集里的原句，免得开发集上的分数虚高
JUDGE_EXAMPLES = [
    ("平板", "屏幕清楚，玩游戏不卡，就是充电有点慢", "有效评论"),
    ("衣服", "领口线头很多，洗一次就起球，垃圾！！", "有效评论"),
    ("水果", "质量不错，很满意，下次还来", "套话好评"),
    ("洗发水", "京东发货就是快，东西不错，支持京东", "套话好评"),
    ("计算机", "不怎么样，大家别买", "空洞差评"),
    ("酒店", "还行吧", "无信息量"),
]


def user_message(cat, text, hint=""):
    return {"role": "user", "content": f"商品类目：{cat}\n评论：{text}{hint}"}


def judge_prompt(tokenizer, r):
    # 重复够不够多由代码判断：只有达到模板门槛才告诉模型，不让它自己权衡"2 条算不算多"
    dup = ""
    if r["group_size"] >= MIN_TEMPLATE_GROUP:
        dup = (f"\n（系统提示：数据里共有 {r['group_size']} 条和它几乎相同的评论"
               + (f"，横跨 {r['group_cats']} 个商品类目" if r["group_cats"] > 1 else "") + "）")
    msgs = [{"role": "system", "content": JUDGE_SYSTEM}]
    for cat, text, value in JUDGE_EXAMPLES:
        msgs += [user_message(cat, text), {"role": "assistant", "content": json.dumps({"分类": value}, ensure_ascii=False)}]
    msgs.append(user_message(r["cat"], r["text"], dup))
    return tokenizer.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False)


def parse_judge(raw):
    try:
        v = json.loads(raw[raw.index("{"):raw.rindex("}") + 1]).get("分类")
    except ValueError:
        return None
    return v if v in VALUES else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    args = ap.parse_args()
    todo = pd.read_json(f"data/value_{args.split}_todo.jsonl", lines=True)
    feats = pd.read_parquet("data/value_features.parquet")
    rows = todo.join(feats[["nlen", "generic_ratio", "group_size"]], on="idx")

    # 方法 A 需要抽取结果：用第二版微调后的学生模型
    model, tok = load_model(STUDENT, adapter_path=ADAPTER)
    extractions = [parse_output(raw) for raw in extract(model, tok, rows["text"].tolist(), log_every=5)]
    # 先把学生模型从 GPU 内存里清掉，再加载 17GB 的老师，否则两份加起来会内存不足
    del model
    gc.collect()
    mx.clear_cache()

    # 方法 B：老师模型直接判断
    from mlx_lm import batch_generate
    model, tok = load_model(TEACHER)
    prompts = [judge_prompt(tok, r) for _, r in rows.iterrows()]
    judged = []
    # 每批 8 条：提示词带了示例比较长，16 条一批会超出 GPU 内存
    for i in range(0, len(prompts), 8):
        judged += batch_generate(model, tok, prompts[i:i + 8], max_tokens=32).texts

    os.makedirs("results", exist_ok=True)
    out_path = f"results/value_{args.split}_preds.jsonl"
    with open(out_path, "w") as f:
        for (_, r), ex, raw in zip(rows.iterrows(), extractions, judged):
            f.write(json.dumps({
                "gid": int(r["gid"]), "stratum": r["stratum"], "cat": r["cat"], "text": r["text"],
                "dup_count": int(r["dup_count"]), "group_size": int(r["group_size"]), "nlen": int(r["nlen"]),
                "generic_ratio": round(float(r["generic_ratio"]), 3), "extraction": ex,
                "rule": rule_classify(r, ex), "llm": parse_judge(raw), "combo": combine(parse_judge(raw), ex), "llm_raw": raw,
            }, ensure_ascii=False) + "\n")
    preds = pd.read_json(out_path, lines=True)
    for m, name in [("rule", "A"), ("llm", "B"), ("combo", "C")]:
        print(f"方法 {name} 分布：", preds[m].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    main()
