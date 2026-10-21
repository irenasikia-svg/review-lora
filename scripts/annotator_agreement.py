"""衡量标签定义清不清楚：让"第二个标注者"独立把测试集再标一遍，和老师的结果比。

这叫"标注者间一致性"。定义清晰时，两个标注者自然会标得一样；
定义有重叠（"有点卡"既像质量又像性能）时，两人会各按各的理解来。

两种用法：
  --model 换一个模型当第二标注者（推荐，能暴露定义的歧义）
  --temp  同一个老师带随机性再标一遍（自我一致性。实测作用不大：同一个模型偏好固定，
          定义再模糊它也每次选同一种理解）

输出追加到 results/annotator_agreement.jsonl
"""
import argparse
import json
import os
import sys

import mlx.core as mx
from mlx_lm.sample_utils import make_sampler

TEACHER = "mlx-community/Qwen3-30B-A3B-Instruct-2507-4bit"

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--model", default=TEACHER)
ap.add_argument("--temp", type=float, default=0.0)
# 用存档的旧版规则和旧版老师标注来测，例如 --rules-dir runs/v1 --labels runs/v1/data/teacher_labels.jsonl
ap.add_argument("--rules-dir", default=None)
ap.add_argument("--labels", default="data/teacher_labels.jsonl")
# 不给第二标注者看示例：用来区分一致性的提升来自"定义改清楚了"还是"多了示例"
ap.add_argument("--no-examples", action="store_true")
args = ap.parse_args()

# 规则目录要排在最前面，这样 import common 时拿到的是那一版的规则
sys.path.insert(0, os.path.dirname(__file__))
if args.rules_dir:
    sys.path.insert(0, args.rules_dir)
from common import parse_output, score  # noqa: E402
from gen import extract, load_model  # noqa: E402


def main():
    rows = [json.loads(line) for line in open(args.labels)]
    rows = [r for r in rows if r["split"] == "test"]
    first = [r["teacher"] for r in rows]

    mx.random.seed(0)
    model, tokenizer = load_model(args.model)
    sampler = make_sampler(temp=args.temp) if args.temp > 0 else None
    # 第二标注者和老师拿到同样的规则和示例，才算公平
    raws = extract(model, tokenizer, [r["text"] for r in rows], log_every=5, sampler=sampler,
                   with_examples=not args.no_examples)
    second = [parse_output(raw) for raw in raws]

    # 只在两边都合格的样本上比较方面是否一致
    pairs = [(s, f) for s, f in zip(second, first) if s and f]
    agree = score([s for s, _ in pairs], [f for _, f in pairs], [1] * len(pairs))
    result = {
        "name": args.name,
        "第二标注者": args.model,
        "temp": args.temp,
        "给示例": not args.no_examples,
        "n": len(rows),
        "老师格式不合格": sum(f is None for f in first) / len(rows),
        "第二标注者格式不合格": sum(s is None for s in second) / len(rows),
        "一致_方面F1": agree["方面F1"],
        "一致_只看方面名": agree["方面F1_只看方面名"],
        "整体情感一致": sum(s["整体情感"] == f["整体情感"] for s, f in pairs) / len(pairs),
    }
    os.makedirs("results", exist_ok=True)
    with open("results/annotator_agreement.jsonl", "a") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")
    with open(f"results/agreement_{args.name}.jsonl", "w") as f:
        for r, raw, s in zip(rows, raws, second):
            f.write(json.dumps({"id": r["id"], "text": r["text"], "teacher": r["teacher"],
                                "second": s, "raw": raw}, ensure_ascii=False) + "\n")
    for k, v in result.items():
        print(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")


if __name__ == "__main__":
    main()
