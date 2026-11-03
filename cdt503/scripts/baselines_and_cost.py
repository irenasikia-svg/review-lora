"""B2 少样本对照 + B4 成本表：四种设置在验证集（142 条）上、同样的批大小下各跑一次。

  teacher_fewshot  老师 Qwen3-30B-A3B（4-bit），带 4 个示例——就是标注训练数据时的用法
  base_zeroshot    原始 Qwen3-1.7B，不带示例（和 LoRA 学生用同一个提示词）
  base_fewshot     原始 Qwen3-1.7B，带同样的 4 个示例——"给小模型几个例子行不行"
  lora             LoRA 学生（调参选出的 lr=5e-5），不带示例

只用验证集，不碰测试集。每种设置在单独的子进程里跑，测到的峰值内存不会互相叠加。
记录：JSON 合格率、整体情感准确率、方面 F1（参照 = 老师标注；老师自己那一行只作参考）、
每条耗时（批大小统一为 8）、加载后的权重内存、生成过程中的峰值内存、参数量。

用法：
  uv run python cdt503/scripts/baselines_and_cost.py --limit 8   # 冒烟测试
  uv run python cdt503/scripts/baselines_and_cost.py              # 正式跑，约 10 分钟
输出：cdt503/results/baselines_cost/<设置>/{valid_preds.jsonl,metrics.json}、summary.json、cost_table.tex
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STUDENT = "mlx-community/Qwen3-1.7B-bf16"
TEACHER = "mlx-community/Qwen3-30B-A3B-Instruct-2507-4bit"
LORA = os.path.join(ROOT, "cdt503/runs/sweep/lr5e-5/best")
BATCH = 8  # 老师带示例的提示词很长，批大小 16 会内存不足；四种设置统一用 8，耗时才可比

SETTINGS = {
    "teacher_fewshot": {"model": TEACHER, "adapter": None, "examples": True},
    "base_zeroshot": {"model": STUDENT, "adapter": None, "examples": False},
    "base_fewshot": {"model": STUDENT, "adapter": None, "examples": True},
    "lora": {"model": STUDENT, "adapter": LORA, "examples": False},
}
# 老师是 4-bit 量化 + 混合专家，按存储的权重数没法数出真实参数量，用官方公布的数字（Qwen3 技术报告）
REPORTED_PARAMS = {TEACHER: {"total_B": 30.5, "active_B": 3.3}}


def count_params(model):
    from mlx.utils import tree_flatten
    return sum(v.size for _, v in tree_flatten(model.parameters()))


def run_one(name, limit, out_root):
    import mlx.core as mx

    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from common import parse_output, score
    from gen import extract, load_model

    cfg = SETTINGS[name]
    rows = [json.loads(line) for line in open(os.path.join(ROOT, "data/sft/valid_meta.jsonl"))][:limit]
    mx.reset_peak_memory()
    model, tok = load_model(cfg["model"], adapter_path=cfg["adapter"])
    mx.eval(model.parameters())
    weights_gb = mx.get_active_memory() / 1e9
    start = time.time()
    raws = extract(model, tok, [r["text"] for r in rows], batch_size=BATCH, log_every=99,
                   with_examples=cfg["examples"])
    sec = (time.time() - start) / len(rows)
    peak_gb = mx.get_peak_memory() / 1e9
    preds = [parse_output(raw) for raw in raws]
    metrics = score(preds, [r["teacher"] for r in rows], [r["label"] for r in rows])

    if cfg["model"] in REPORTED_PARAMS:
        params = REPORTED_PARAMS[cfg["model"]]
    else:
        n = count_params(model) / 1e9  # 挂了 LoRA 时包含适配器参数
        params = {"total_B": n, "active_B": n}  # 稠密模型：每个词都用到全部参数
    out = {"setting": name, **cfg, "n": len(rows), "batch_size": BATCH, "sec_per_item": sec,
           "weights_gb": weights_gb, "peak_gb": peak_gb, **params, **metrics}
    d = os.path.join(out_root, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "valid_preds.jsonl"), "w") as f:
        for r, raw, p in zip(rows, raws, preds):
            f.write(json.dumps({"id": r["id"], "raw": raw, "pred": p}, ensure_ascii=False) + "\n")
    json.dump(out, open(os.path.join(d, "metrics.json"), "w"), ensure_ascii=False, indent=2)
    print(f"{name:16s} JSON {metrics['JSON合格率']:.3f}  情感 {metrics['整体情感准确率']:.3f}  "
          f"方面F1 {metrics['方面F1']:.3f}  {sec:.2f} 秒/条  权重 {weights_gb:.1f} GB  峰值 {peak_gb:.1f} GB", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="只跑前 N 条（冒烟测试）")
    ap.add_argument("--only", nargs="*", default=list(SETTINGS))
    ap.add_argument("--_one", help=argparse.SUPPRESS)
    args = ap.parse_args()
    out_root = os.path.join(ROOT, "cdt503/results", "baselines_cost_smoke" if args.limit else "baselines_cost")
    if args._one:
        return run_one(args._one, args.limit, out_root)
    for name in args.only:
        cmd = [sys.executable, __file__, "--_one", name] + (["--limit", str(args.limit)] if args.limit else [])
        subprocess.run(cmd, check=True, cwd=ROOT)

    res = {n: json.load(open(os.path.join(out_root, n, "metrics.json"))) for n in SETTINGS
           if os.path.exists(os.path.join(out_root, n, "metrics.json"))}
    json.dump(res, open(os.path.join(out_root, "summary.json"), "w"), ensure_ascii=False, indent=2)
    labels = {"teacher_fewshot": "Teacher 30B-A3B, 4-shot", "base_zeroshot": "Base 1.7B, zero-shot",
              "base_fewshot": "Base 1.7B, 4-shot", "lora": "LoRA student 1.7B"}
    tex = ["\\begin{tabular}{lcccccc}", "\\toprule",
           "Setting & Params (total/active) & Peak mem. & s/review & JSON & Sent. & Aspect-F1 \\\\", "\\midrule"]
    for n, r in res.items():
        f1 = f"{r['方面F1']:.3f}" + ("$^*$" if n == "teacher_fewshot" else "")
        tex.append(f"{labels[n]} & {r['total_B']:.1f}B / {r['active_B']:.1f}B & {r['peak_gb']:.1f} GB & "
                   f"{r['sec_per_item']:.2f} & {r['JSON合格率']:.3f} & {r['整体情感准确率']:.3f} & {f1} \\\\")
    tex += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(out_root, "cost_table.tex"), "w").write("\n".join(tex) + "\n")
    print("已保存", os.path.relpath(out_root, ROOT))


if __name__ == "__main__":
    main()
