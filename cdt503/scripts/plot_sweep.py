"""画调参对比图，可以直接放进 IEEE 报告（PDF + PNG，英文标签）。

图的尺寸就是论文里的实际尺寸（双栏宽 7.16 英寸），所以字号就是印出来的字号，不会被缩小。

输出（--smoke 时写到 cdt503/results/smoke/figures/）：
  sweep_val_curves   三个面板（rank / 学习率 / 层数）的验证损失曲线
  sweep_metrics      三个面板的验证集方面 F1，灰色带 = 只换随机种子时的波动范围
  sweep_cost         可训练参数量、训练时间 vs 方面 F1
  sweep_table.csv / sweep_table.tex   汇总表
用法：uv run python cdt503/scripts/plot_sweep.py [--smoke]
"""
import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "pdf.fonttype": 42, "ps.fonttype": 42,
    "axes.spines.top": False, "axes.spines.right": False,
})

# 每个面板：标题、要比较的组、图例里怎么写
FACTORS = [
    ("LoRA rank", ["rank4", "rank8", "baseline", "rank32"], lambda s: f"r={s['rank']}"),
    ("Learning rate", ["lr5e-5", "baseline", "lr2e-4"], lambda s: f"lr={s['learning_rate']:.0e}".replace("e-0", "e-")),
    ("LoRA layers", ["layers8", "layers16", "baseline"],
     lambda s: "all 28" if s["num_layers"] == -1 else f"top {s['num_layers']}"),
]
BASE_COLOR = "#222222"
OTHER_COLORS = ["#4C72B0", "#55A868", "#C44E52"]


def color_of(names, n):
    """基准固定黑色；其他组按它在面板里的固定位置取色，某组还没跑完也不会让后面的颜色错位。"""
    if n == "baseline":
        return BASE_COLOR
    return OTHER_COLORS[[x for x in names if x != "baseline"].index(n)]


def load(kind):
    base = os.path.join(ROOT, f"cdt503/results/{kind}")
    runs = {}
    for name in os.listdir(base):
        s_path = os.path.join(base, name, "summary.json")
        if os.path.exists(s_path):
            runs[name] = json.load(open(s_path))
            runs[name]["curve"] = json.load(open(os.path.join(base, name, "curve.json")))
    return runs


def save(fig, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out_dir, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("已保存", os.path.relpath(os.path.join(out_dir, name), ROOT) + ".{pdf,png}")


def ordered(runs, names):
    return [n for n in names if n in runs]


def plot_curves(runs, out_dir):
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.3), sharey=True)
    for ax, (title, names, label) in zip(axes, FACTORS):
        for n in names:
            if n not in runs:
                continue
            s, color = runs[n], color_of(names, n)
            steps, vals = zip(*[(x, y) for x, y in s["curve"]["val"] if x > 1])  # 第 1 步（未训练）的损失太大，不画
            lw = 2.0 if n == "baseline" else 1.3
            ax.plot(steps, vals, color=color, lw=lw, label=label(s))
            ax.scatter([s["best_step"]], [s["best_val_loss"]], color=color, s=18, zorder=3)
        ax.set_title(title)
        ax.set_xlabel("Training step")
        ax.legend(frameon=False)
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Validation loss")
    fig.tight_layout()
    save(fig, out_dir, "sweep_val_curves")


def plot_metrics(runs, out_dir):
    noise = None
    if "baseline" in runs and "baseline_seed43" in runs:
        a = runs["baseline"]["valid"]["方面F1"]
        b = runs["baseline_seed43"]["valid"]["方面F1"]
        noise = (min(a, b), max(a, b))
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.2), sharey=True)
    for ax, (title, names, label) in zip(axes, FACTORS):
        names = ordered(runs, names)
        f1 = [runs[n]["valid"]["方面F1"] for n in names]
        colors = ["#222222" if n == "baseline" else "#4C72B0" for n in names]
        bars = ax.bar(range(len(names)), f1, color=colors, width=0.6)
        if noise:
            ax.axhspan(*noise, color="#999999", alpha=0.3, lw=0, label="Seed variation (baseline, 2 seeds)")
        for b, v in zip(bars, f1):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.005, f"{v:.3f}", ha="center", va="bottom", fontsize=7.5)
        ax.set_xticks(range(len(names)), [label(runs[n]) for n in names])
        ax.set_title(title)
        lo = min(f1 + ([noise[0]] if noise else []))
        ax.set_ylim(max(0, lo - 0.08), min(1, max(f1) + 0.05))
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Aspect F1 (validation)")
    fig.tight_layout()
    if noise:
        # 图例放在图的上方，不挡柱子上的数字
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, frameon=False, loc="lower right", bbox_to_anchor=(1.0, 0.98))
    save(fig, out_dir, "sweep_metrics")


def plot_cost(runs, out_dir):
    names = [n for n in runs if n != "baseline_seed43"]
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.3), sharey=True)
    for ax, key, xlabel in [(axes[0], "trainable_M", "Trainable parameters (M)"),
                            (axes[1], "train_minutes", "Training time (min)")]:
        for n in names:
            s = runs[n]
            ax.scatter(s[key], s["valid"]["方面F1"], color="#222222" if n == "baseline" else "#4C72B0", s=22)
            ax.annotate(n, (s[key], s["valid"]["方面F1"]), textcoords="offset points", xytext=(4, 3), fontsize=7)
        ax.set_xlabel(xlabel)
        ax.grid(alpha=0.25)
    axes[0].set_xscale("log")
    axes[0].set_ylabel("Aspect F1 (validation)")
    fig.tight_layout()
    save(fig, out_dir, "sweep_cost")


def write_table(runs, out_dir):
    order = ["baseline", "baseline_seed43", "rank4", "rank8", "rank32", "lr5e-5", "lr2e-4", "layers8", "layers16"]
    rows = []
    for n in ordered(runs, order):
        s, v = runs[n], runs[n]["valid"]
        rows.append([n, s["rank"], f"{s['learning_rate']:.0e}", "all" if s["num_layers"] == -1 else s["num_layers"],
                     s["seed"], f"{s.get('trainable_M', float('nan')):.1f}", s["best_step"], f"{s['best_val_loss']:.3f}",
                     f"{v['JSON合格率']:.3f}", f"{v['整体情感准确率']:.3f}", f"{v['方面F1']:.3f}",
                     f"{v['sec_per_item']:.2f}", f"{s['train_minutes']:.0f}"])
    header = ["run", "rank", "lr", "layers", "seed", "params_M", "best_step", "best_val_loss",
              "json_valid", "sentiment_acc", "aspect_f1", "sec_per_item", "train_min"]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sweep_table.csv"), "w") as f:
        f.write(",".join(header) + "\n" + "\n".join(",".join(map(str, r)) for r in rows) + "\n")
    # LaTeX 表：报告里直接 \input
    tex = ["\\begin{tabular}{lrrrrrr}", "\\toprule",
           "Run & Rank & LR & Layers & Best step & Val loss & Aspect F1 \\\\", "\\midrule"]
    for r in rows:
        tex.append(f"{r[0].replace('_', '-')} & {r[1]} & {r[2]} & {r[3]} & {r[6]} & {r[7]} & {r[10]} \\\\")
    tex += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(out_dir, "sweep_table.tex"), "w").write("\n".join(tex) + "\n")
    print("已保存", os.path.relpath(os.path.join(out_dir, "sweep_table.{csv,tex}"), ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    kind = "smoke" if args.smoke else "sweep"
    runs = load(kind)
    out_dir = os.path.join(ROOT, "cdt503/results/smoke/figures" if args.smoke else "cdt503/figures")
    print(f"读到 {len(runs)} 组：{sorted(runs)}")
    plot_curves(runs, out_dir)
    plot_metrics(runs, out_dir)
    plot_cost(runs, out_dir)
    write_table(runs, out_dir if args.smoke else os.path.join(ROOT, "cdt503/results/sweep"))


if __name__ == "__main__":
    main()
