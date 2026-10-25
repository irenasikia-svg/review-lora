"""CDT503 第 2 阶段：让三个模型给人工标注的 100 条评论做抽取，之后和人工标注比。

  base     原始 Qwen3-1.7B（不挂 LoRA），和学生用同样的提示词
  student  LoRA 微调后的学生（默认用调参选出的最优配置，见 --adapter）
  teacher  老师 Qwen3-30B-A3B，和标注训练数据时一样带上 4 个示例

每个模型在单独的子进程里跑：跑完进程退出，GPU 内存一定会释放，不会和下一个模型叠加（老师约 17GB）。
用 GPU，预计总共约 5 分钟。

用法：uv run python cdt503/scripts/predict_aspect_gold.py --adapter cdt503/runs/sweep/<最优组>/best
输出：cdt503/results/human_eval/preds_<model>.jsonl
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TODO = os.path.join(ROOT, "cdt503/data/aspect_gold_todo.jsonl")
OUT = os.path.join(ROOT, "cdt503/results/human_eval")
STUDENT = "mlx-community/Qwen3-1.7B-bf16"
TEACHER = "mlx-community/Qwen3-30B-A3B-Instruct-2507-4bit"


def run_one(model_key, adapter):
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from common import parse_output
    from gen import extract, load_model

    rows = [json.loads(line) for line in open(TODO)]
    if model_key == "teacher":
        model, tok = load_model(TEACHER)
        kwargs = {"batch_size": 8, "with_examples": True}  # 带示例的提示词长，8 条一批避免内存不足
    else:
        model, tok = load_model(STUDENT, adapter_path=adapter if model_key == "student" else None)
        kwargs = {"batch_size": 16}
    start = time.time()
    raws = extract(model, tok, [r["text"] for r in rows], log_every=5, **kwargs)
    sec = (time.time() - start) / len(rows)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"preds_{model_key}.jsonl"), "w") as f:
        for r, raw in zip(rows, raws):
            f.write(json.dumps({"gid": r["gid"], "raw": raw, "pred": parse_output(raw)}, ensure_ascii=False) + "\n")
    meta = {"model": model_key, "adapter": adapter if model_key == "student" else None, "sec_per_item": sec}
    json.dump(meta, open(os.path.join(OUT, f"preds_{model_key}.meta.json"), "w"), ensure_ascii=False, indent=2)
    print(f"{model_key}: {sec:.2f} 秒/条")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default=os.path.join(ROOT, "adapters_best"))
    ap.add_argument("--models", nargs="+", default=["base", "student", "teacher"])
    ap.add_argument("--_one", help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args._one:
        return run_one(args._one, args.adapter)
    for m in args.models:
        subprocess.run([sys.executable, __file__, "--_one", m, "--adapter", args.adapter], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
