"""汇总测试集上的最终结果：原始模型 / 调参前的 LoRA（v2 基准）/ 调参后的 LoRA（lr=5e-5）。

测试集只用于报告：最优配置是按验证集选的（lr5e-5，验证集方面 F1 0.793），这里每个模型只评估一次。
方面 F1 的 95% 区间用自助法（按评论重抽样 2000 次）；"调参后 − 调参前"用成对重抽样，
区间不含 0 才能说调参带来的提升不是运气。

用法：uv run python cdt503/scripts/final_test_summary.py
输出：cdt503/results/final_test/summary.json、main_results.tex
"""
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR = os.path.join(ROOT, "cdt503/results/final_test")
MODELS = [("base_model_no_lora", "Base Qwen3-1.7B (no LoRA)"),
          ("baseline_best", "LoRA, default config (r=16, lr=1e-4)"),
          ("lr5e-5_best", "LoRA, tuned (r=16, lr=5e-5)")]


def pair_sets(path):
    sets = []
    for r in map(json.loads, open(path)):
        p = r["pred"]
        g = {(a["方面"], a["情感"]) for a in r["gold"]["方面"]}
        sets.append((g, {(a["方面"], a["情感"]) for a in p["方面"]} if p else set()))
    return sets


def f1(sets):
    tp = sum(len(g & p) for g, p in sets)
    fp = sum(len(p - g) for g, p in sets)
    fn = sum(len(g - p) for g, p in sets)
    return 2 * tp / (2 * tp + fp + fn)


def main():
    rng = np.random.default_rng(0)
    data = {k: pair_sets(os.path.join(DIR, k, "test_preds.jsonl")) for k, _ in MODELS}
    n = len(next(iter(data.values())))
    idx = rng.integers(0, n, (2000, n))
    out = {"n": n, "models": {}, "diffs": {}}
    for key, label in MODELS:
        m = json.load(open(os.path.join(DIR, key, "test_metrics.json")))
        boots = [f1([data[key][i] for i in s]) for s in idx]
        out["models"][key] = {"label": label, "json_valid": m["JSON合格率"], "sentiment_acc": m["整体情感准确率"],
                              "aspect_f1": m["方面F1"], "aspect_f1_ci95": list(np.percentile(boots, [2.5, 97.5])),
                              "aspect_name_f1": m["方面F1_只看方面名"], "sec_per_item": m["sec_per_item"]}
    for a, b in [("lr5e-5_best", "baseline_best"), ("baseline_best", "base_model_no_lora")]:
        d = [f1([data[a][i] for i in s]) - f1([data[b][i] for i in s]) for s in idx]
        out["diffs"][f"{a}_minus_{b}"] = {"point": f1(data[a]) - f1(data[b]), "ci95": list(np.percentile(d, [2.5, 97.5]))}
    json.dump(out, open(os.path.join(DIR, "summary.json"), "w"), ensure_ascii=False, indent=2)

    tex = ["\\begin{tabular}{lcccc}", "\\toprule",
           "Model & JSON valid & Sentiment acc. & Aspect F1 (95\\% CI) & Aspect-name F1 \\\\", "\\midrule"]
    for key, label in MODELS:
        r = out["models"][key]
        lo, hi = r["aspect_f1_ci95"]
        tex.append(f"{label} & {r['json_valid']:.3f} & {r['sentiment_acc']:.3f} & "
                   f"{r['aspect_f1']:.3f} ({lo:.3f}--{hi:.3f}) & {r['aspect_name_f1']:.3f} \\\\")
    tex += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(DIR, "main_results.tex"), "w").write("\n".join(tex) + "\n")

    print(f"测试集 {n} 条")
    for key, _ in MODELS:
        r = out["models"][key]
        print(f"  {key:20s} JSON {r['json_valid']:.3f}  情感 {r['sentiment_acc']:.3f}  方面F1 {r['aspect_f1']:.3f} "
              f"[{r['aspect_f1_ci95'][0]:.3f}, {r['aspect_f1_ci95'][1]:.3f}]  {r['sec_per_item']:.2f} 秒/条")
    for k, d in out["diffs"].items():
        lo, hi = d["ci95"]
        print(f"  {k}: {d['point']:+.3f}，95% 区间 [{lo:+.3f}, {hi:+.3f}]{'，不含 0' if lo > 0 or hi < 0 else '，含 0'}")


if __name__ == "__main__":
    main()
