"""CDT503 第 2 阶段：用组员的人工标注评估三个模型，并做错误分析。

1. 合并人工标注：同一条评论有多人标时，(方面, 情感) 超过半数人选了才算；正好一半时听第一位标注者的
2. 组员之间的一致性：在共同标注的那些评论上，两两算方面 F1（衡量"任务本身有多模糊"，是模型分数的天花板参考）
3. 三个模型 vs 人工：JSON 合格率、方面 F1、只看方面名的 F1、整体情感准确率（对数据集自带的人工标签），
   方面 F1 附自助法（bootstrap）95% 区间
4. 错误分析（学生 vs 人工）：
   - 换错方面：同一条评论里，人工有、模型没有的方面恰好一个，模型多出来的也恰好一个 → 记一次"人工 A → 模型 B"
   - 方面对了但情感反了
   - 每个方面的漏标、多标次数

用法：uv run python cdt503/scripts/eval_human.py
     （测试用：--data-dir / --pred-dir / --out-dir / --fig-dir 指到别的目录）
输出：cdt503/results/human_eval/metrics.json、*.tex；cdt503/figures/human_*.{pdf,png}
"""
import argparse
import itertools
import json
import os
import sys
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "cdt503/scripts"))
from aspects_en import en  # noqa: E402
from common import ASPECTS  # noqa: E402

MODELS = [("base", "Base Qwen3-1.7B"), ("student", "LoRA student (1.7B)"), ("teacher", "Teacher Qwen3-30B")]
COLORS = {"base": "#999999", "student": "#4C72B0", "teacher": "#55A868"}
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "legend.fontsize": 8, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})


def pairs(aspects):
    return {(a["方面"], a["情感"]) for a in aspects}


def names(aspects):
    return {a["方面"] for a in aspects}


def f1_counts(gold_sets, pred_sets):
    tp = sum(len(g & p) for g, p in zip(gold_sets, pred_sets))
    fp = sum(len(p - g) for g, p in zip(gold_sets, pred_sets))
    fn = sum(len(g - p) for g, p in zip(gold_sets, pred_sets))
    return tp, fp, fn


def f1(gold_sets, pred_sets):
    tp, fp, fn = f1_counts(gold_sets, pred_sets)
    return 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 1.0


def bootstrap(gold_sets, pred_sets, n=2000, seed=0):
    """按评论重抽样，得到 F1 的 95% 区间。"""
    rng = np.random.default_rng(seed)
    idx = np.arange(len(gold_sets))
    vals = []
    for _ in range(n):
        s = rng.choice(idx, len(idx))
        vals.append(f1([gold_sets[i] for i in s], [pred_sets[i] for i in s]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def bootstrap_diff(gold_sets, a_sets, b_sets, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(gold_sets))
    vals = []
    for _ in range(n):
        s = rng.choice(idx, len(idx))
        g = [gold_sets[i] for i in s]
        vals.append(f1(g, [a_sets[i] for i in s]) - f1(g, [b_sets[i] for i in s]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def merge(labels_by_annotator, order):
    """多人标同一条时按多数票合并。labels_by_annotator: {名字: {gid: aspects}}"""
    merged = {}
    all_gids = set().union(*[set(v) for v in labels_by_annotator.values()])
    for gid in all_gids:
        who = [a for a in order if gid in labels_by_annotator[a]]
        votes = Counter(p for a in who for p in pairs(labels_by_annotator[a][gid]))
        primary = pairs(labels_by_annotator[who[0]][gid])
        keep = {p for p, c in votes.items() if 2 * c > len(who) or (2 * c == len(who) and p in primary)}
        # 同一方面两种情感都过半是不可能的；正好打平时上面已按第一位标注者取舍
        merged[gid] = [{"方面": a, "情感": s} for a, s in sorted(keep)]
    return merged


def error_analysis(gold, preds):
    subs, flips, misses, extras = Counter(), Counter(), Counter(), Counter()
    for gid, g in gold.items():
        p = preds.get(gid)
        p = p["方面"] if p else []
        gn, pn = {a["方面"]: a["情感"] for a in g}, {a["方面"]: a["情感"] for a in p}
        for a in gn.keys() & pn.keys():
            if gn[a] != pn[a]:
                flips[a] += 1
        miss, extra = gn.keys() - pn.keys(), pn.keys() - gn.keys()
        if len(miss) == 1 and len(extra) == 1:
            subs[(next(iter(miss)), next(iter(extra)))] += 1
        else:
            misses.update(miss)
            extras.update(extra)
    return subs, flips, misses, extras


def save(fig, fig_dir, name):
    os.makedirs(fig_dir, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(fig_dir, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("已保存", os.path.join(os.path.relpath(fig_dir, ROOT), name) + ".{pdf,png}")


def fair_comparison(labels, order, preds_by_model, out_dir, n_boot=2000, seed=0):
    """公平的人机对比：只在两人都标过的评论上，用每个人的原始标注（不用复核结果）当参照。

    这样"模型 vs 人"和"人 vs 人"是同一种比法——都是拿一个人的标注去比另一方，
    不会出现"模型拿复核后的答案比、人却拿原始标注比"这种不对等。
    """
    if len(order) != 2:
        return None
    a, b = order
    common = sorted(set(labels[a]) & set(labels[b]))
    if not common:
        return None
    refs = {a: [pairs(labels[a][g]) for g in common], b: [pairs(labels[b][g]) for g in common]}
    systems = {f"annotator {b}": [pairs(labels[b][g]) for g in common]}  # B 当"系统"去比 A，比 B 时是自己，跳过
    for key, label in MODELS:
        if key in preds_by_model:
            p = preds_by_model[key]
            systems[label] = [pairs(p[g]["方面"]) if p.get(g) else set() for g in common]
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(common), (n_boot, len(common)))
    rows = []
    for name, sys_sets in systems.items():
        row = {"system": name}
        for who in (a, b):
            if name == f"annotator {who}":
                continue
            row[f"vs_{who}"] = f1(refs[who], sys_sets)
        cols = [k for k in row if k.startswith("vs_")]
        row["mean"] = float(np.mean([row[k] for k in cols]))
        # 两个参照的平均 F1 的 95% 区间（按评论重抽样）
        boots = [np.mean([f1([refs[k[3:]][i] for i in s], [sys_sets[i] for i in s]) for k in cols]) for s in idx]
        row["mean_ci95"] = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
        rows.append(row)
    out = {"n_shared": len(common), "annotators": [a, b], "rows": rows,
           "note": "References are each annotator's ORIGINAL labels (before adjudication). "
                   "The other 80 of 100 reviews were labelled by one annotator only."}
    os.makedirs(out_dir, exist_ok=True)
    json.dump(out, open(os.path.join(out_dir, "fair_20.json"), "w"), ensure_ascii=False, indent=2)
    tex = ["\\begin{tabular}{lccc}", "\\toprule",
           f"Compared with & Annotator {a} & Annotator {b} & Mean (95\\% CI) \\\\", "\\midrule"]
    for r in rows:
        va = f"{r[f'vs_{a}']:.3f}" if f"vs_{a}" in r else "--"
        vb = f"{r[f'vs_{b}']:.3f}" if f"vs_{b}" in r else "--"
        tex.append(f"{r['system'].replace('annotator', 'Annotator')} & {va} & {vb} & "
                   f"{r['mean']:.3f} ({r['mean_ci95'][0]:.2f}--{r['mean_ci95'][1]:.2f}) \\\\")
    tex += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(out_dir, "fair_20_table.tex"), "w").write("\n".join(tex) + "\n")
    print(f"\n== 公平对比：{len(common)} 条双人标注的评论，参照 = 各人的原始标注（复核前）")
    for r in rows:
        cells = "  ".join(f"vs {w} {r[f'vs_{w}']:.3f}" if f"vs_{w}" in r else f"vs {w}   --  " for w in (a, b))
        print(f"  {r['system']:22s} {cells}  平均 {r['mean']:.3f} [{r['mean_ci95'][0]:.2f}, {r['mean_ci95'][1]:.2f}]")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(ROOT, "cdt503/data"))
    ap.add_argument("--pred-dir", default=os.path.join(ROOT, "cdt503/results/human_eval"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "cdt503/results/human_eval"))
    ap.add_argument("--fig-dir", default=os.path.join(ROOT, "cdt503/figures"))
    ap.add_argument("--no-adjudication", action="store_true", help="不用复核结果，算复核前的版本")
    ap.add_argument("--fair-dir", default=os.path.join(ROOT, "cdt503/results/human_eval_fair"),
                    help="公平人机对比（20 条双人标注）的输出目录")
    args = ap.parse_args()

    todo = {r["gid"]: r for r in map(json.loads, open(os.path.join(args.data_dir, "aspect_gold_todo.jsonl")))}
    assign = json.load(open(os.path.join(args.data_dir, "aspect_assign.json")))
    order = list(assign["assign"])
    labels = {}
    for a in order:
        path = os.path.join(args.data_dir, f"aspect_gold_{a}.jsonl")
        labels[a] = {r["gid"]: r["aspects"] for r in map(json.loads, open(path))} if os.path.exists(path) else {}
    order = [a for a in order if labels[a]]
    gold = merge(labels, order)
    # 复核过的评论用两人商量后的最终答案（cdt503/scripts/adjudicate_server.py）；原始标注不变
    adj_path = os.path.join(args.data_dir, "aspect_gold_adjudicated.jsonl")
    adjudicated = {}
    if os.path.exists(adj_path) and not args.no_adjudication:
        adjudicated = {r["gid"]: r["aspects"] for r in map(json.loads, open(adj_path))}
        gold.update(adjudicated)
    suffix = "" if adjudicated else "_pre_adjudication"
    gids = sorted(gold)
    print(f"标注者 {order}；已有人工标注 {len(gids)} / {len(todo)} 条；复核过 {len(adjudicated)} 条"
          f"{'' if adjudicated else '（复核前版本）'}")

    # —— 组员之间的一致性 ——
    iaa = []
    for a, b in itertools.combinations(order, 2):
        common = sorted(set(labels[a]) & set(labels[b]))
        if common:
            iaa.append({"pair": [a, b], "n": len(common),
                        "aspect_f1": f1([pairs(labels[a][g]) for g in common], [pairs(labels[b][g]) for g in common]),
                        "aspect_name_f1": f1([names(labels[a][g]) for g in common], [names(labels[b][g]) for g in common])})
    iaa_mean = float(np.mean([x["aspect_f1"] for x in iaa])) if iaa else None
    # 每位标注者和最终答案的吻合程度：复核后能看出每个人原来错了多少
    vs_final = {a: f1([pairs(gold[g]) for g in sorted(labels[a])], [pairs(labels[a][g]) for g in sorted(labels[a])])
                for a in order}

    # —— 三个模型 vs 人工 ——
    gold_pairs = [pairs(gold[g]) for g in gids]
    gold_names = [names(gold[g]) for g in gids]
    results, pred_sets, preds_by_model = {}, {}, {}
    for key, _ in MODELS:
        path = os.path.join(args.pred_dir, f"preds_{key}.jsonl")
        if not os.path.exists(path):
            continue
        preds = {r["gid"]: r["pred"] for r in map(json.loads, open(path))}
        preds_by_model[key] = preds
        ps = [pairs(preds[g]["方面"]) if preds.get(g) else set() for g in gids]
        pred_sets[key] = ps
        # 格式不合格（pred 为 None）算答错
        senti = [bool(preds.get(g)) and preds[g]["整体情感"] == ("正面" if todo[g]["label"] == 1 else "负面")
                 for g in gids]
        per_aspect = {}
        for asp in ASPECTS:
            g_ = [{p for p in s if p[0] == asp} for s in gold_pairs]
            p_ = [{p for p in s if p[0] == asp} for s in ps]
            tp, fp, fn = f1_counts(g_, p_)
            if tp + fn:  # 人工至少标过一次的方面才统计
                per_aspect[asp] = {"f1": 2 * tp / (2 * tp + fp + fn), "support": tp + fn}
        results[key] = {
            "json_valid": float(np.mean([preds.get(g) is not None for g in gids])),
            "aspect_f1": f1(gold_pairs, ps), "aspect_f1_ci95": bootstrap(gold_pairs, ps),
            "aspect_name_f1": f1(gold_names, [{p[0] for p in s} for s in ps]),
            "sentiment_acc": float(np.mean(senti)), "per_aspect": per_aspect,
        }
    diffs = {}
    for a, b in [("student", "base"), ("student", "teacher")]:
        if a in pred_sets and b in pred_sets:
            diffs[f"{a}_minus_{b}"] = bootstrap_diff(gold_pairs, pred_sets[a], pred_sets[b])
    # 公平对比只依赖原始标注，和是否复核无关，所以只在默认（复核后）那次运行里输出一次
    if adjudicated:
        fair_comparison(labels, order, preds_by_model, args.fair_dir)

    os.makedirs(args.out_dir, exist_ok=True)
    out = {"n_items": len(gids), "n_adjudicated": len(adjudicated), "annotators": order, "inter_annotator": iaa,
           "inter_annotator_mean_f1": iaa_mean, "annotator_vs_final_f1": vs_final,
           "models": results, "f1_diff_ci95": diffs}
    json.dump(out, open(os.path.join(args.out_dir, f"metrics{suffix}.json"), "w"), ensure_ascii=False, indent=2)

    print(f"\n组员一致性（方面 F1，两两平均）：{iaa_mean if iaa_mean is None else round(iaa_mean, 3)}")
    print("每位标注者 vs 最终答案：" + "，".join(f"{a} {v:.3f}" for a, v in vs_final.items()))
    for key, label in MODELS:
        if key in results:
            r = results[key]
            print(f"{label:22s} JSON {r['json_valid']:.2f}  方面F1 {r['aspect_f1']:.3f} "
                  f"[{r['aspect_f1_ci95'][0]:.3f}, {r['aspect_f1_ci95'][1]:.3f}]  只看方面名 {r['aspect_name_f1']:.3f}  "
                  f"情感 {r['sentiment_acc']:.2f}")
    for k, (lo, hi) in diffs.items():
        print(f"{k}: 方面 F1 差 95% 区间 [{lo:+.3f}, {hi:+.3f}]{'（不含 0，差异显著）' if lo > 0 or hi < 0 else '（含 0）'}")

    # —— LaTeX 主结果表 ——
    tex = ["\\begin{tabular}{lcccc}", "\\toprule",
           "Model & JSON valid & Aspect F1 (95\\% CI) & Aspect-name F1 & Sentiment acc. \\\\", "\\midrule"]
    for key, label in MODELS:
        if key in results:
            r = results[key]
            tex.append(f"{label} & {r['json_valid']:.2f} & {r['aspect_f1']:.3f} "
                       f"({r['aspect_f1_ci95'][0]:.2f}--{r['aspect_f1_ci95'][1]:.2f}) & "
                       f"{r['aspect_name_f1']:.3f} & {r['sentiment_acc']:.2f} \\\\")
    if iaa_mean is not None:
        tex += ["\\midrule", f"Annotator vs.\\ annotator & -- & {iaa_mean:.3f} & -- & -- \\\\"]
    tex += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(args.out_dir, f"human_eval_table{suffix}.tex"), "w").write("\n".join(tex) + "\n")

    # —— 图 1：每个方面的 F1 ——
    if results:
        asp_order = sorted({a for r in results.values() for a in r["per_aspect"]},
                           key=lambda a: -max(r["per_aspect"].get(a, {"support": 0})["support"] for r in results.values()))
        fig, ax = plt.subplots(figsize=(7.16, 2.4))
        width = 0.8 / len(results)
        for i, (key, label) in enumerate([m for m in MODELS if m[0] in results]):
            vals = [results[key]["per_aspect"].get(a, {"f1": 0})["f1"] for a in asp_order]
            ax.bar(np.arange(len(asp_order)) + (i - (len(results) - 1) / 2) * width, vals, width,
                   label=label, color=COLORS[key])
        support = [max(r["per_aspect"].get(a, {"support": 0})["support"] for r in results.values()) for a in asp_order]
        # 标签写成一行 "Service (14)"：括号里是人工标过这个方面的次数，次数少的方面 F1 波动大
        ax.set_xticks(range(len(asp_order)), [f"{en(a)} ({s})" for a, s in zip(asp_order, support)],
                      rotation=40, ha="right", rotation_mode="anchor")
        ax.set_ylabel("F1 vs. human")
        ax.set_ylim(0, 1.0)
        ax.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
        ax.grid(axis="y", alpha=0.25)
        save(fig, args.fig_dir, f"human_per_aspect_f1{suffix}")

    # —— 图 2：学生最常见的错误 ——
    if "student" in preds_by_model:
        subs, flips, misses, extras = error_analysis({g: gold[g] for g in gids}, preds_by_model["student"])
        items = [(f"{en(a)} → {en(b)}", c, "#C44E52") for (a, b), c in subs.most_common(8)]
        items += [(f"{en(a)}: sentiment flipped", c, "#8172B2") for a, c in flips.most_common(3)]
        items += [(f"{en(a)}: missed", c, "#999999") for a, c in misses.most_common(4)]
        items += [(f"{en(a)}: spurious", c, "#DD8452") for a, c in extras.most_common(4)]
        items = sorted(items, key=lambda x: x[1])[-14:]
        if items:
            fig, ax = plt.subplots(figsize=(3.5, 0.22 * len(items) + 0.6))
            ax.barh(range(len(items)), [c for _, c, _ in items], color=[col for _, _, col in items])
            ax.set_yticks(range(len(items)), [t for t, _, _ in items])
            ax.set_xlabel("Count (student vs. human)")
            ax.grid(axis="x", alpha=0.25)
            save(fig, args.fig_dir, f"human_error_analysis{suffix}")
        json.dump({"substitutions": [[a, b, c] for (a, b), c in subs.most_common()],
                   "sentiment_flips": flips.most_common(), "misses": misses.most_common(),
                   "spurious": extras.most_common()},
                  open(os.path.join(args.out_dir, f"error_analysis{suffix}.json"), "w"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
