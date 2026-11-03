"""B3：最终配置（r=16, lr=5e-5）在三个随机种子下的结果——平均值和最小–最大范围。

种子 42 就是原来的 lr5e-5 组（验证集结果在 results/sweep/lr5e-5，测试集在 results/final_test/lr5e-5_best），
种子 43、44 由 sweep.py 新训练。每个种子都按验证损失选检查点，再在验证集和测试集上各评估一次。

用法：
  uv run python cdt503/scripts/seed_summary.py --eval-test   # 给还没测过的种子跑测试集（每个约 3 分钟），再汇总
  uv run python cdt503/scripts/seed_summary.py               # 只汇总
输出：cdt503/results/final_test_seeds/summary.json
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "cdt503/results/final_test_seeds")
SEEDS = {
    42: {"run": "lr5e-5", "test": os.path.join(ROOT, "cdt503/results/final_test/lr5e-5_best")},
    43: {"run": "lr5e-5_seed43", "test": os.path.join(OUT, "lr5e-5_seed43")},
    44: {"run": "lr5e-5_seed44", "test": os.path.join(OUT, "lr5e-5_seed44")},
}
KEYS = [("JSON合格率", "json_valid"), ("整体情感准确率", "sentiment_acc"), ("方面F1", "aspect_f1")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-test", action="store_true")
    args = ap.parse_args()

    rows = {}
    for seed, s in SEEDS.items():
        summ = os.path.join(ROOT, "cdt503/results/sweep", s["run"], "summary.json")
        if not os.path.exists(summ):
            print(f"种子 {seed}：还没训练完（{s['run']}），跳过")
            continue
        test_metrics = os.path.join(s["test"], "test_metrics.json")
        if args.eval_test and not os.path.exists(test_metrics):
            adapter = os.path.join(ROOT, "cdt503/runs/sweep", s["run"], "best")
            print(f"种子 {seed}：在测试集上评估 {os.path.relpath(adapter, ROOT)}", flush=True)
            subprocess.run([sys.executable, os.path.join(ROOT, "cdt503/scripts/eval_split.py"), "--split", "test",
                            "--adapter", adapter, "--out", s["test"]], check=True, cwd=ROOT)
        summary = json.load(open(summ))
        row = {"best_step": summary["best_step"], "best_val_loss": summary["best_val_loss"],
               "valid": {new: summary["valid"][old] for old, new in KEYS}}
        if os.path.exists(test_metrics):
            t = json.load(open(test_metrics))
            row["test"] = {new: t[old] for old, new in KEYS}
        rows[seed] = row

    agg = {}
    for split in ("valid", "test"):
        have = [r[split] for r in rows.values() if split in r]
        if have:
            agg[split] = {k: {"mean": float(np.mean([h[k] for h in have])), "min": float(min(h[k] for h in have)),
                              "max": float(max(h[k] for h in have)), "n_seeds": len(have)} for _, k in KEYS}
    os.makedirs(OUT, exist_ok=True)
    json.dump({"per_seed": rows, "aggregate": agg}, open(os.path.join(OUT, "summary.json"), "w"),
              ensure_ascii=False, indent=2)
    for seed, r in rows.items():
        t = r.get("test", {})
        print(f"种子 {seed}：最优第 {r['best_step']} 步，验证 F1 {r['valid']['aspect_f1']:.3f}，"
              f"测试 F1 {t.get('aspect_f1', float('nan')):.3f}")
    for split, a in agg.items():
        f = a["aspect_f1"]
        print(f"{split}（{f['n_seeds']} 个种子）方面 F1 平均 {f['mean']:.3f}，范围 {f['min']:.3f}–{f['max']:.3f}")


if __name__ == "__main__":
    main()
