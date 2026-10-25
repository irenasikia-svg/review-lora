"""在验证集或测试集上给一个 LoRA 检查点打分（CDT503 用，结果只写到 cdt503/ 下，不碰原有 results/）。

调参阶段只用 --split valid；测试集只在选定最终配置后跑一次。

用法：
  uv run python cdt503/scripts/eval_split.py --split valid --adapter cdt503/runs/r4/best --out cdt503/results/sweep/r4
  uv run python cdt503/scripts/eval_split.py --split valid --out cdt503/results/sweep/base_model   # 不加 --adapter 即原始模型
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from common import parse_output, score  # noqa: E402
from gen import extract, load_model  # noqa: E402

STUDENT = "mlx-community/Qwen3-1.7B-bf16"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["valid", "test"])
    ap.add_argument("--adapter", default=None, help="含 adapter_config.json 和 adapters.safetensors 的目录")
    ap.add_argument("--out", required=True, help="结果目录：写入 <split>_metrics.json 和 <split>_preds.jsonl")
    ap.add_argument("--limit", type=int, default=None, help="只评估前 N 条（冒烟测试用）")
    args = ap.parse_args()

    rows = [json.loads(line) for line in open(os.path.join(ROOT, f"data/sft/{args.split}_meta.jsonl"))]
    rows = rows[:args.limit]
    model, tokenizer = load_model(STUDENT, adapter_path=args.adapter)

    start = time.time()
    # 和 v1/v2 的评估一致：每批 16 条一起生成，所以"秒/条"是批量吞吐，不是单条延迟
    raws = extract(model, tokenizer, [r["text"] for r in rows], batch_size=16, log_every=5)
    elapsed = time.time() - start
    preds = [parse_output(raw) for raw in raws]

    metrics = score(preds, [r["teacher"] for r in rows], [r["label"] for r in rows])
    metrics = {"split": args.split, "adapter": args.adapter, "n": len(rows),
               "sec_per_item": elapsed / len(rows), **metrics}

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, f"{args.split}_preds.jsonl"), "w") as f:
        for r, raw, p in zip(rows, raws, preds):
            f.write(json.dumps({"id": r["id"], "text": r["text"], "gold": r["teacher"], "label": r["label"],
                                "raw": raw, "pred": p}, ensure_ascii=False) + "\n")
    with open(os.path.join(args.out, f"{args.split}_metrics.json"), "w") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    for k, v in metrics.items():
        print(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")


if __name__ == "__main__":
    main()
