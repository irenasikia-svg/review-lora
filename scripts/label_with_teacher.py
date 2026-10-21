"""第 2 步：让大模型（老师）给每条评论写出标准答案。

这叫"知识蒸馏"：大模型效果好但又大又慢，我们用它批量标注数据，
再拿这些数据去训练一个小模型（学生），让小模型在这个任务上接近老师的水平。
企业里人工标注很贵，这是现在非常常见的做法。

输出：data/teacher_labels.jsonl（支持中断后继续跑）
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import parse_output  # noqa: E402
from gen import extract, load_model  # noqa: E402

TEACHER = "mlx-community/Qwen3-30B-A3B-Instruct-2507-4bit"
IN_PATH = "data/sampled.jsonl"
OUT_PATH = "data/teacher_labels.jsonl"
SAVE_EVERY = 64


def main():
    # 可选参数：只标前 N 条，用来在全量标注前试标、检查规则
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = [json.loads(line) for line in open(IN_PATH)]
    done = set()
    if os.path.exists(OUT_PATH):
        done = {json.loads(line)["id"] for line in open(OUT_PATH)}
    todo = [r for r in rows if r["id"] not in done][:limit]
    print(f"共 {len(rows)} 条，已完成 {len(done)}，待标注 {len(todo)}")
    if not todo:
        return

    model, tokenizer = load_model(TEACHER)
    with open(OUT_PATH, "a") as f:
        for i in range(0, len(todo), SAVE_EVERY):
            chunk = todo[i:i + SAVE_EVERY]
            raws = extract(model, tokenizer, [r["text"] for r in chunk], batch_size=16, log_every=99,
                           with_examples=True)
            for r, raw in zip(chunk, raws):
                r = dict(r, teacher_raw=raw, teacher=parse_output(raw))
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            print(f"已保存 {len(done) + i + len(chunk)}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
