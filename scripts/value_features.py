"""评论价值识别 · 第 1 步：在全部 6.2 万条评论上计算两个"统计特征"。

不需要模型、不需要 GPU，只靠"这条评论和其他评论比起来怎么样"：

1. 重复度：有多少条别的评论和它几乎一模一样（字符相似度 ≥ 0.85）。
   一模一样的长评论出现在很多人、甚至很多类目下，多半是刷单或"返现好评"的模板。
2. 套话程度：评论里有多大比例的片段在几乎所有类目下都常见。
   "质量很好""非常满意"在衣服、水果、酒店评论里都出现 → 通用套话；
   "火龙果叶子""风扇声音"只在某个类目出现 → 具体细节。

输出：data/value_features.parquet（每条评论一行）
"""
import re
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer

DUP_SIM = 0.85
# 通用片段：在至少 GENERIC_CATS 个类目里，都出现在 ≥ GENERIC_FRAC 的评论中
GENERIC_CATS, GENERIC_FRAC = 6, 0.001


def normalize(text: str) -> str:
    """去掉标点空格、压缩重复：'不错。。。。' 和 '不错！！' 应该看成同一条。"""
    t = re.sub(r"[\W_]+", "", text.lower())
    t = re.sub(r"(.{1,6}?)\1+", r"\1", t)  # "很好很好很好" → "很好"
    return t


def trigrams(s: str):
    return {s[i:i + 3] for i in range(len(s) - 2)}


def main():
    df = pd.read_parquet("data/raw/online_shopping.parquet").dropna(subset=["text"]).reset_index(drop=True)
    df["text"] = df["text"].str.replace("﻿", "").str.strip()
    df["norm"] = df["text"].map(normalize)
    df["nlen"] = df["norm"].str.len()

    # —— 重复度 ——
    # 字符 2~4 元组的 TF-IDF 向量，两条评论向量夹角的余弦就是相似度
    X = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), min_df=2).fit_transform(df["norm"])
    rows, cols = [], []
    for start in range(0, X.shape[0], 2000):
        sims = (X[start:start + 2000] @ X.T).tocoo()
        keep = (sims.data >= DUP_SIM) & (sims.row + start != sims.col)
        rows.append(sims.row[keep] + start)
        cols.append(sims.col[keep])
    rows, cols = np.concatenate(rows), np.concatenate(cols)
    df["dup_count"] = np.bincount(rows, minlength=len(df))
    # 把互相相似的评论连成"模板群"，看每个群有多大、横跨几个类目
    from scipy.sparse import coo_matrix
    graph = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(df), len(df)))
    _, group = connected_components(graph, directed=False)
    df["dup_group"] = group
    g = df.groupby("dup_group")
    df["group_size"] = g["text"].transform("size")
    df["group_cats"] = g["cat"].transform("nunique")

    # —— 套话程度 ——
    cats = sorted(df["cat"].unique())
    ci = {c: i for i, c in enumerate(cats)}
    cat_n = df["cat"].value_counts()[cats].values
    grams = df["norm"].map(trigrams)
    counts = defaultdict(lambda: np.zeros(len(cats)))
    for gs, c in zip(grams, df["cat"]):
        for x in gs:
            counts[x][ci[c]] += 1
    generic = {x for x, v in counts.items() if ((v / cat_n) >= GENERIC_FRAC).sum() >= GENERIC_CATS}
    df["generic_ratio"] = [len(gs & generic) / len(gs) if gs else 1.0 for gs in grams]

    df.drop(columns=["norm"]).to_parquet("data/value_features.parquet")
    long = df[df["nlen"] >= 12]
    print(f"共 {len(df)} 条；通用片段 {len(generic)} 个")
    print(f"有近似重复的评论 {(df.dup_count > 0).mean():.1%}；其中长评论（≥12 字）{(long.dup_count > 0).mean():.1%}")
    print(f"横跨 ≥2 个类目的长评论模板群：{long[long.group_cats >= 2].dup_group.nunique()} 个，"
          f"涉及 {(long.group_cats >= 2).sum()} 条")
    print("套话程度分布（≥12 字）：", long["generic_ratio"].describe(percentiles=[.5, .9, .95, .99]).round(2).to_dict())


if __name__ == "__main__":
    main()
