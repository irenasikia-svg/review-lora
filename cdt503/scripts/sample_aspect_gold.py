"""CDT503 第 2 阶段：抽 100 条"从没用过"的评论，给组员人工标注方面和情感。

为什么不从现有测试集里抽：
  1. 测试集只保留了老师和人工情感标签一致的样本，用它比较"老师 vs 人工"会偏向老师；
  2. 设计第二版标签时看过第一版测试集上的错误，测试集已经不算完全没见过。
所以从 6.2 万条里、排除所有用过的评论（训练/验证/测试的 2425 条、价值标注的 250 条，
以及和它们几乎相同的评论）之后重新抽，这 100 条对所有模型和规则来说都是全新的。

分层：10 个类目 × 正面 5 条 + 负面 5 条（正负按数据集自带的人工标签）。

分配：--annotators 给出组员名字，前 --overlap 条所有人都标（用来算组员之间的一致性），
其余平均分给每个人。

用法：uv run python cdt503/scripts/sample_aspect_gold.py --annotators A B C D --overlap 20
输出：cdt503/data/aspect_gold_todo.jsonl、cdt503/data/aspect_assign.json
"""
import argparse
import json
import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "cdt503/data")
SEED = 503
PER_CAT_LABEL = 5
MIN_LEN, MAX_LEN = 12, 160  # 和 scripts/prepare_data.py 一致


def clean(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("﻿", "").strip())


def norm(t: str) -> str:
    """去标点、压缩重复，用来判断两条评论是不是"同一条"。和 scripts/value_features.py 一致"""
    t = re.sub(r"[\W_]+", "", t.lower())
    return re.sub(r"(.{1,6}?)\1+", r"\1", t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotators", nargs="+", default=["A"])
    ap.add_argument("--overlap", type=int, default=20)
    ap.add_argument("--reassign", action="store_true", help="只重新分配，不重新抽样（已开始标注后改人数用）")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    todo_path = os.path.join(OUT_DIR, "aspect_gold_todo.jsonl")

    if not args.reassign:
        df = pd.read_parquet(os.path.join(ROOT, "data/raw/online_shopping.parquet")).dropna(subset=["text"])
        df = df.reset_index(drop=True)  # 和 value_features.parquet 的行号对齐
        df["text"] = df["text"].map(clean)
        df["norm"] = df["text"].map(norm)

        used = {json.loads(line)["text"] for line in open(os.path.join(ROOT, "data/sampled.jsonl"))}
        used_idx = set()
        for split in ("dev", "test"):
            used_idx |= {json.loads(line)["idx"] for line in open(os.path.join(ROOT, f"data/value_{split}_todo.jsonl"))}
        used_norm = set(df.loc[df["text"].isin(used) | df.index.isin(used_idx), "norm"])
        pool = df[~df["norm"].isin(used_norm) & df["text"].str.len().between(MIN_LEN, MAX_LEN)]
        # 有重复度特征文件时，再排除和用过评论同一个"近似重复群"的
        feats_path = os.path.join(ROOT, "data/value_features.parquet")
        if os.path.exists(feats_path):
            feats = pd.read_parquet(feats_path)
            used_rows = df.index[df["norm"].isin(used_norm)]
            bad_groups = set(feats.loc[feats.index.isin(used_rows) & (feats["group_size"] > 1), "dup_group"])
            pool = pool[~feats.loc[pool.index, "dup_group"].isin(bad_groups).values]
        pool = pool.drop_duplicates("norm")
        print(f"可用评论 {len(pool)} 条（已排除用过的 {len(used_norm)} 种文本及其近似重复）")

        picked = []
        cats = sorted(pool["cat"].unique())
        for cat in cats:
            for label in (0, 1):
                g = pool[(pool["cat"] == cat) & (pool["label"] == label)]
                picked.append(g.sample(min(PER_CAT_LABEL, len(g)), random_state=SEED))
        out = pd.concat(picked)
        # 某个类目某种情感不够（热水器的负面评论只有 100 条，之前全用过了）：从同情感的其他类目补齐，保持正负各半
        for label in (0, 1):
            short = PER_CAT_LABEL * len(cats) - (out["label"] == label).sum()
            if short > 0:
                rest = pool[(pool["label"] == label) & ~pool.index.isin(out.index)]
                out = pd.concat([out, rest.sample(short, random_state=SEED)])
                print(f"{'负面' if label == 0 else '正面'}不够，从其他类目补了 {short} 条")
        out = out.sample(frac=1, random_state=SEED)
        with open(todo_path, "w") as f:
            for gid, (idx, r) in enumerate(out.iterrows()):
                f.write(json.dumps({"gid": gid, "raw_idx": int(idx), "cat": r["cat"], "label": int(r["label"]),
                                    "text": r["text"]}, ensure_ascii=False) + "\n")
        print(out.groupby(["cat", "label"]).size().unstack().to_string())

    n = sum(1 for _ in open(todo_path))
    overlap = list(range(min(args.overlap, n)))
    rest = list(range(len(overlap), n))
    assign = {a: overlap + rest[i::len(args.annotators)] for i, a in enumerate(args.annotators)}
    json.dump({"overlap": overlap, "assign": assign}, open(os.path.join(OUT_DIR, "aspect_assign.json"), "w"),
              ensure_ascii=False, indent=1)
    for a, items in assign.items():
        print(f"{a}: {len(items)} 条（含共同标注 {len(overlap)} 条）")


if __name__ == "__main__":
    main()
