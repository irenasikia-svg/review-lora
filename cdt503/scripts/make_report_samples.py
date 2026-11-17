"""商品评论报告的内置样例：每个类目从"从没用过的评论"里随机抽 150 条，存成 CSV。

排除所有用过的评论（训练/验证/测试的 2,425 条、价值标注的 250 条、方面人工标注的 100 条，以及它们的近似重复），
所以样例对模型来说都是新的。label 列是数据集自带的人工好评(1)/差评(0)标签，报告里用来对照。

注意：原数据集每个类目都是人为凑成好评、差评各半，所以样例的好评率接近 50%，不代表真实商品。

用法：uv run python cdt503/scripts/make_report_samples.py
输出：cdt503/demo/samples/{hotel,tablet,fruit}.csv
"""
import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "cdt503/scripts"))
from sample_aspect_gold import MAX_LEN, MIN_LEN, clean, norm  # noqa: E402

SAMPLES = {"hotel": "酒店", "tablet": "平板", "fruit": "水果"}
N, SEED = 150, 2026


def main():
    df = pd.read_parquet(os.path.join(ROOT, "data/raw/online_shopping.parquet")).dropna(subset=["text"])
    df = df.reset_index(drop=True)
    df["text"] = df["text"].map(clean)
    df["norm"] = df["text"].map(norm)

    used_text = {json.loads(line)["text"] for line in open(os.path.join(ROOT, "data/sampled.jsonl"))}
    used_text |= {json.loads(line)["text"] for line in open(os.path.join(ROOT, "cdt503/data/aspect_gold_todo.jsonl"))}
    used_idx = set()
    for split in ("dev", "test"):
        used_idx |= {json.loads(line)["idx"] for line in open(os.path.join(ROOT, f"data/value_{split}_todo.jsonl"))}
    used_norm = set(df.loc[df["text"].isin(used_text) | df.index.isin(used_idx), "norm"])
    pool = df[~df["norm"].isin(used_norm) & df["text"].str.len().between(MIN_LEN, MAX_LEN)].drop_duplicates("norm")

    out_dir = os.path.join(ROOT, "cdt503/demo/samples")
    os.makedirs(out_dir, exist_ok=True)
    for name, cat in SAMPLES.items():
        s = pool[pool["cat"] == cat].sample(N, random_state=SEED)[["text", "label"]]
        s.to_csv(os.path.join(out_dir, f"{name}.csv"), index=False)
        print(f"{name}: {len(s)} 条，人工标签好评 {s['label'].mean():.0%}")


if __name__ == "__main__":
    main()
