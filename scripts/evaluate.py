"""第 4 步 / 第 6 步：在测试集上给模型打分。

用法：
  uv run python scripts/evaluate.py --name 原始模型
  uv run python scripts/evaluate.py --name LoRA微调后 --adapter adapters/
  uv run python scripts/evaluate.py --name 老师模型 --model mlx-community/Qwen3-30B-A3B-Instruct-2507-4bit

结果追加到 results/scores.jsonl，每个模型的逐条输出存到 results/<name>_preds.jsonl。
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from common import parse_output, score  # noqa: E402
from gen import extract, load_model  # noqa: E402

STUDENT = "mlx-community/Qwen3-1.7B-bf16"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--model", default=STUDENT)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--split", default="test")
    args = ap.parse_args()

    rows = [json.loads(line) for line in open(f"data/sft/{args.split}_meta.jsonl")]
    model, tokenizer = load_model(args.model, adapter_path=args.adapter)

    start = time.time()
    raws = extract(model, tokenizer, [r["text"] for r in rows], batch_size=16, log_every=5)
    elapsed = time.time() - start
    preds = [parse_output(raw) for raw in raws]

    result = score(preds, [r["teacher"] for r in rows], [r["label"] for r in rows])
    result = {"name": args.name, "model": args.model, "adapter": args.adapter,
              "n": len(rows), "秒每条": elapsed / len(rows), **result}

    os.makedirs("results", exist_ok=True)
    with open(f"results/{args.name}_preds.jsonl", "w") as f:
        for r, raw, p in zip(rows, raws, preds):
            f.write(json.dumps({"id": r["id"], "text": r["text"], "gold": r["teacher"],
                                "raw": raw, "pred": p}, ensure_ascii=False) + "\n")
    with open("results/scores.jsonl", "a") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    for k, v in result.items():
        print(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")


if __name__ == "__main__":
    main()
