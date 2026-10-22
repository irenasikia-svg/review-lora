"""评论价值识别 · 第 4 步：用人工标注检验两种方法。

两个角度：
  - 五分类：每一类分得对不对（精确率、召回率、混淆矩阵）
  - 二分类（商家视角）：只问"这条值不值得看"，有效评论 vs 其余四类
另外单独报告"随机"那一层的结果：分层抽样里多抽了疑似样本，只有随机层能反映真实分布下的效果。
"全部判为有效评论"作为最简单的对照：打不过它的方法就没有实用价值。

用法：uv run python scripts/value_eval.py --split test
"""
import argparse
import json

import pandas as pd

VALUES = ["有效评论", "模板重复", "套话好评", "无信息量", "空洞差评"]


def per_class(gold, pred):
    rows = []
    for v in VALUES:
        tp = ((pred == v) & (gold == v)).sum()
        n_pred, n_gold = (pred == v).sum(), (gold == v).sum()
        # 一次都没预测过某类：精确率按 0 算，否则"全判有效"会因为别的类是空值而虚高
        p = tp / n_pred if n_pred else 0.0
        r = tp / n_gold if n_gold else float("nan")
        # 人工一条都没标的类不计入宏平均
        f1 = float("nan") if not n_gold else (2 * p * r / (p + r) if p + r else 0.0)
        rows.append({"分类": v, "人工条数": int((gold == v).sum()), "精确率": p, "召回率": r, "F1": f1})
    return pd.DataFrame(rows).set_index("分类")


def binary(gold, pred):
    g, p = gold != "有效评论", pred != "有效评论"
    tp = (g & p).sum()
    return {"低价值_精确率": tp / p.sum() if p.sum() else float("nan"), "低价值_召回率": tp / g.sum(),
            "准确率": (g == p).mean()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    args = ap.parse_args()
    gold = {r["gid"]: r["value"] for r in map(json.loads, open(f"data/value_{args.split}.jsonl"))}
    df = pd.read_json(f"results/value_{args.split}_preds.jsonl", lines=True)
    df = df[df["gid"].isin(gold)].copy()
    df["gold"] = df["gid"].map(gold)
    df["llm"] = df["llm"].fillna("有效评论")
    df["baseline"] = "有效评论"
    print(f"已标注 {len(df)} 条；人工分布：{df['gold'].value_counts().to_dict()}\n")

    summary = {}
    methods = [("baseline", "对照_全判有效"), ("rule", "方法A_规则统计"), ("llm", "方法B_大模型"), ("combo", "方法C_组合")]
    for m, name in methods:
        macro = per_class(df["gold"], df[m])["F1"].mean()
        rnd = df[df["stratum"] == "随机"]
        summary[name] = {"五分类准确率": (df[m] == df["gold"]).mean(), "五分类宏平均F1": macro,
                         **binary(df["gold"], df[m]), "随机层五分类准确率": (rnd[m] == rnd["gold"]).mean()}
        if m == "baseline":
            continue
        print(f"== {name}")
        print(per_class(df["gold"], df[m]).round(2).to_string())
        print("混淆矩阵（行=人工，列=模型）：")
        print(pd.crosstab(df["gold"], df[m]).reindex(index=VALUES, columns=VALUES, fill_value=0).to_string(), "\n")
    out = pd.DataFrame(summary).round(3)
    print(out.to_string())
    out.to_json(f"results/value_{args.split}_scores.json", force_ascii=False, indent=2)


if __name__ == "__main__":
    main()
