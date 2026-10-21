"""第 1 步：从 6 万条原始评论里抽出一份干净、均衡的小样本。

为什么不用全部 6 万条？
  - 后面要让老师模型逐条标注，条数越多越慢；
  - LoRA 微调通常几千条高质量数据就够了，质量比数量重要。

输出：data/sampled.jsonl，每行 {"id", "cat", "label", "text", "split"}
"""
import json
import random
import re

import pandas as pd

SEED = 42
# 每个类别每种情感抽多少条（10 类 × 2 种情感 × N）
PER_CAT_LABEL = {"train": 100, "valid": 8, "test": 15}
MIN_LEN, MAX_LEN = 12, 160


def clean(text: str) -> str:
    text = text.replace("﻿", "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def main():
    df = pd.read_parquet("data/raw/online_shopping.parquet")
    df = df.dropna(subset=["text"])
    df["text"] = df["text"].map(clean)
    df = df[df["text"].str.len().between(MIN_LEN, MAX_LEN)]
    df = df.drop_duplicates("text")
    print(f"清洗后剩 {len(df)} 条")

    rng = random.Random(SEED)
    rows = []
    for (cat, label), group in df.groupby(["cat", "label"]):
        idx = list(group.index)
        rng.shuffle(idx)
        start = 0
        for split, n in PER_CAT_LABEL.items():
            for i in idx[start:start + n]:
                rows.append({"cat": cat, "label": int(label), "text": df.at[i, "text"], "split": split})
            start += n

    rng.shuffle(rows)
    for i, r in enumerate(rows):
        r["id"] = i
    with open("data/sampled.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    counts = pd.DataFrame(rows).groupby("split").size()
    print(counts.to_string())


if __name__ == "__main__":
    main()
