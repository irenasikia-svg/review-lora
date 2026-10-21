"""老师标注、学生训练、评估都要用的公共部分：任务说明、输出格式、解析和打分。

把这些放在一个文件里，可以保证三个环节用的是同一套规则。
"""
import json
import re

# 固定的"方面"列表。限定成固定选项，模型输出才能和标准答案逐项比对、算分。
ASPECTS = {
    "质量": "做工、材质、耐用、真假、故障",
    "价格": "价格、性价比、优惠",
    "物流": "快递、发货、送货速度",
    "服务": "客服、售后、商家态度、酒店前台",
    "外观": "颜色、款式、设计、颜值",
    "尺寸": "大小、尺码、重量、分量",
    "性能": "速度、续航、屏幕、配置、声音、使用效果",
    "口味": "味道、新鲜度、口感",
    "包装": "包装、外箱、破损",
    "内容": "书籍或作品的内容、观点、文笔、印刷",
    "环境": "卫生、设施、位置、早餐、隔音",
    "其他": "以上都不合适的方面",
}
SENTIMENTS = ("正面", "负面")

SYSTEM_PROMPT = (
    "你是电商评论分析助手。阅读一条中文用户评论，抽取结构化信息，只输出一个 JSON 对象，不要输出其他文字。\n"
    "JSON 格式：{\"整体情感\": \"正面\"或\"负面\", \"方面\": [{\"方面\": 方面名, \"观点\": 评论原文中的短语, \"情感\": \"正面\"或\"负面\"}]}\n"
    "方面名只能从下面选：\n"
    + "\n".join(f"- {k}：{v}" for k, v in ASPECTS.items())
    + "\n规则：每个方面最多出现一次；\"观点\"尽量摘自原文，不超过 15 个字；评论没有具体评价任何方面时，\"方面\"为空列表 []。"
)


def build_messages(text: str, with_examples: bool = False):  # with_examples 是第二版加的参数，第一版没有示例，忽略即可
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"评论：{text}"},
    ]


def parse_output(raw: str):
    """把模型输出解析成合法的结果；格式不对就返回 None。"""
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.S).strip()
    match = re.search(r"\{.*\}", raw, flags=re.S)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if obj.get("整体情感") not in SENTIMENTS or not isinstance(obj.get("方面"), list):
        return None
    aspects, seen = [], set()
    for a in obj["方面"]:
        if not isinstance(a, dict):
            return None
        name, opinion, senti = a.get("方面"), a.get("观点"), a.get("情感")
        if name not in ASPECTS or senti not in SENTIMENTS or not isinstance(opinion, str):
            return None
        if name in seen:
            continue
        seen.add(name)
        aspects.append({"方面": name, "观点": opinion, "情感": senti})
    return {"整体情感": obj["整体情感"], "方面": aspects}


def to_target_json(result) -> str:
    """训练时学生要学会输出的那段文字（紧凑写法，省 token）。"""
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


def score(preds, golds, human_labels):
    """
    preds/golds: 解析后的结果列表（pred 可能为 None，表示格式错误）
    human_labels: 数据集自带的人工情感标签（1=正面，0=负面）

    返回四个指标：
      - JSON 合格率：输出能否被程序直接使用
      - 整体情感准确率：和人工标签比（真正的人工标准答案）
      - 方面 F1：(方面, 情感) 二元组和标准答案比对
      - 方面 F1（只看方面名）：不管情感对不对，只看找没找对方面
    """
    n = len(golds)
    valid = sum(p is not None for p in preds)
    senti_ok = sum(
        p is not None and p["整体情感"] == ("正面" if h == 1 else "负面")
        for p, h in zip(preds, human_labels)
    )

    def f1(key):
        tp = fp = fn = 0
        for p, g in zip(preds, golds):
            gs = {key(a) for a in g["方面"]}
            ps = {key(a) for a in p["方面"]} if p else set()
            tp += len(ps & gs)
            fp += len(ps - gs)
            fn += len(gs - ps)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        return 2 * prec * rec / (prec + rec) if prec + rec else 0.0

    return {
        "JSON合格率": valid / n,
        "整体情感准确率": senti_ok / n,
        "方面F1": f1(lambda a: (a["方面"], a["情感"])),
        "方面F1_只看方面名": f1(lambda a: a["方面"]),
    }
