"""第 3 步：把老师的标注整理成训练集，并过滤掉不可靠的样本。

质量过滤规则：
  1. 老师输出的 JSON 格式不合格 → 丢掉
  2. 老师判断的整体情感和数据集自带的人工标签不一致 → 丢掉
     （说明老师可能理解错了，或者评论本身有歧义，这种数据会教坏学生）

输出 mlx-lm 认的对话格式：data/sft/{train,valid,test}.jsonl
  每行 {"messages": [system, user, assistant]}，assistant 就是要学生学会输出的答案。
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from common import build_messages, to_target_json  # noqa: E402

IN_PATH = "data/teacher_labels.jsonl"
OUT_DIR = "data/sft"


def main():
    rows = [json.loads(line) for line in open(IN_PATH)]
    os.makedirs(OUT_DIR, exist_ok=True)
    stats = Counter()
    aspect_counts = Counter()
    kept = {"train": [], "valid": [], "test": []}

    for r in rows:
        t = r["teacher"]
        if t is None:
            stats["格式不合格"] += 1
            continue
        human = "正面" if r["label"] == 1 else "负面"
        if t["整体情感"] != human:
            stats["情感与人工标签不一致"] += 1
            continue
        stats["保留"] += 1
        aspect_counts.update(a["方面"] for a in t["方面"])
        kept[r["split"]].append(r)

    for split, items in kept.items():
        with open(f"{OUT_DIR}/{split}.jsonl", "w") as f:
            for r in items:
                msgs = build_messages(r["text"]) + [
                    {"role": "assistant", "content": to_target_json(r["teacher"])}
                ]
                f.write(json.dumps({"messages": msgs}, ensure_ascii=False) + "\n")
        # 评估要用到原文和人工标签，单独存一份
        with open(f"{OUT_DIR}/{split}_meta.jsonl", "w") as f:
            for r in items:
                f.write(json.dumps({k: r[k] for k in ("id", "cat", "label", "text", "teacher")}, ensure_ascii=False) + "\n")

    print("过滤结果：", dict(stats))
    print("各划分条数：", {k: len(v) for k, v in kept.items()})
    print("方面出现次数：", dict(aspect_counts.most_common()))


if __name__ == "__main__":
    main()
