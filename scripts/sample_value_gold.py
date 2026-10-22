"""评论价值识别 · 第 2 步：抽评论给人工标注。

两份人工标注：
  dev（开发集，150 条）：第一轮标的。用来找规则的问题、改规则，可以反复看
  test（测试集，100 条）：改完规则后新抽的。只在最后打一次分，不能拿来改规则

如果纯随机抽，约 8 成都是"有效评论"，低价值的每类只有几条，没法衡量识别效果。
所以分层抽样：一部分随机（反映真实分布），一部分从"疑似"的候选里多抽一些。
标注页不会显示这条来自哪一层，避免影响标注者判断。

用法：uv run python scripts/sample_value_gold.py --split test
输出：data/value_<split>_todo.jsonl
"""
import argparse
import json
import os

import pandas as pd

STRATA = {
    "dev": {"随机": 60, "疑似重复": 30, "疑似套话": 30, "短评论": 30},
    # 测试集把"疑似重复"拆成大群和小群：开发集发现两者的性质完全不同
    "test": {"随机": 40, "大模板群": 10, "小重复": 10, "疑似套话": 20, "短评论": 20},
}
SEEDS = {"dev": 7, "test": 11}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=STRATA)
    args = ap.parse_args()

    df = pd.read_parquet("data/value_features.parquet")
    df = df[df["nlen"] > 0]
    # 排除其他划分已经抽过的评论，以及和它们同一个模板群的评论，保证测试集是"没见过的"
    used = set()
    for other in STRATA:
        path = f"data/value_{other}_todo.jsonl"
        if other != args.split and os.path.exists(path):
            used |= {r["idx"] for r in map(json.loads, open(path))}
    used_groups = set(df.loc[df.index.isin(used), "dup_group"])
    df = df[~df.index.isin(used) & ~(df["dup_group"].isin(used_groups) & (df["group_size"] > 1))]

    picked = []

    def take(pool, n, stratum):
        pool = pool[~pool.index.isin([p["idx"] for p in picked])]
        for idx, _ in pool.sample(min(n, len(pool)), random_state=SEEDS[args.split]).iterrows():
            picked.append({"idx": int(idx), "stratum": stratum})

    long = df[df.nlen >= 12]
    plan = STRATA[args.split]
    take(df, plan["随机"], "随机")
    if "疑似重复" in plan:
        take(long[long.dup_count > 0].drop_duplicates("dup_group"), plan["疑似重复"], "疑似重复")
    if "大模板群" in plan:
        take(long[long.group_size >= 4].drop_duplicates("dup_group"), plan["大模板群"], "大模板群")
        take(long[long.group_size.between(2, 3)].drop_duplicates("dup_group"), plan["小重复"], "小重复")
    take(long[(long.generic_ratio >= 0.3) & (long.dup_count == 0)], plan["疑似套话"], "疑似套话")
    take(df[df.nlen < 12], plan["短评论"], "短评论")

    out = pd.DataFrame(picked).sample(frac=1, random_state=SEEDS[args.split])
    with open(f"data/value_{args.split}_todo.jsonl", "w") as f:
        for i, p in enumerate(out.itertuples()):
            r = df.loc[p.idx]
            f.write(json.dumps({
                "gid": i, "idx": p.idx, "stratum": p.stratum, "cat": r["cat"], "label": int(r["label"]),
                "text": r["text"], "dup_count": int(r["dup_count"]), "group_cats": int(r["group_cats"]),
            }, ensure_ascii=False) + "\n")
    print(out["stratum"].value_counts().to_string())


if __name__ == "__main__":
    main()
