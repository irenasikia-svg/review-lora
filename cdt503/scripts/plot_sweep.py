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
    ("LoRA rank", ["rank4", "rank8", "baseline", "rank32", "rank32_scale10"],
     lambda s: f"r={s['rank']}" + (f"\ns={s['scale']:g}" if s.get("scale", 20.0) != 20.0 else "")),
    ("Learning rate", ["lr5e-5", "baseline", "lr2e-4"], lambda s: f"lr={s['learning_rate']:.0e}".replace("e-0", "e-")),
    ("LoRA layers", ["layers8", "layers16", "baseline"],
     lambda s: "all 28" if s["num_layers"] == -1 else f"top {s['num_layers']}"),
]
BASE_COLOR = "#222222"
# 验证损失大于这个值就算训练发散（正常的组都在 0.12–0.18）。发散组在图里只标注文字，不让它把坐标轴撑大
DIVERGED_LOSS = 1.0
CURVE_YLIM = (0.10, 0.40)
OTHER_COLORS = ["#4C72B0", "#55A868", "#C44E52", "#8172B2"]


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


def diverged(s):
    return s["best_val_loss"] > DIVERGED_LOSS


def plot_curves(runs, out_dir):
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.3), sharey=True)
    for ax, (title, names, label) in zip(axes, FACTORS):
        for n in names:
            if n not in runs:
                continue
            s, color = runs[n], color_of(names, n)
            if diverged(s):
                ax.text(0.97, 0.95, f"{label(s)}: diverged\n(val loss > {s['best_val_loss']:.1f})",
                        transform=ax.transAxes, ha="right", va="top", color=color, fontsize=7.5)
                continue
            steps, vals = zip(*[(x, y) for x, y in s["curve"]["val"] if x > 1])  # 第 1 步（未训练）的损失太大，不画
            lw = 2.0 if n == "baseline" else 1.3
            ax.plot(steps, vals, color=color, lw=lw, label=label(s).replace("\n", ", "))
            ax.scatter([s["best_step"]], [s["best_val_loss"]], color=color, s=18, zorder=3)
        ax.set_ylim(*CURVE_YLIM)
        ax.set_title(title)
        ax.set_xlabel("Training step")
        ax.legend(frameon=False, loc="upper right" if title != "Learning rate" else "center right")
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
    # 三个面板共用 y 轴，所以范围要按所有面板里没发散的组一起算
    ok_all = [n for _, names, _ in FACTORS for n in ordered(runs, names) if not diverged(runs[n])]
    lo = min([runs[n]["valid"]["方面F1"] for n in ok_all] + ([noise[0]] if noise else []))
    hi = max(runs[n]["valid"]["方面F1"] for n in ok_all)
    ymin, ymax = max(0, lo - 0.03), min(1, hi + 0.02)
    for ax, (title, names, label) in zip(axes, FACTORS):
        names = ordered(runs, names)
        ok = [n for n in names if not diverged(runs[n])]
        f1 = {n: runs[n]["valid"]["方面F1"] for n in names}
        if noise:
            ax.axhspan(*noise, color="#999999", alpha=0.3, lw=0, label="Seed variation (baseline, 2 seeds)")
        for i, n in enumerate(names):
            if n in ok:
                ax.bar(i, f1[n], color=BASE_COLOR if n == "baseline" else "#4C72B0", width=0.6)
                ax.text(i, f1[n] + 0.003, f"{f1[n]:.3f}", ha="center", va="bottom", fontsize=7.5)
            else:  # 发散：F1 为 0，不画柱子，在坐标轴底部写字
                ax.text(i, ymin + 0.01, "diverged\n(F1 = 0)", ha="center", va="bottom", fontsize=7.5, color="#C44E52")
        ax.set_xticks(range(len(names)), [label(runs[n]) for n in names])
        ax.set_title(title)
        ax.set_ylim(ymin, ymax)
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
    order = ["baseline", "baseline_seed43", "rank4", "rank8", "rank32", "rank32_scale10",
             "lr5e-5", "lr2e-4", "layers8", "layers16"]
    rows = []
    for n in ordered(runs, order):
        s, v = runs[n], runs[n]["valid"]
        # 第一晚的组在加 scale 字段之前就跑完了，它们的 scale 都是默认的 20
        rows.append([n, s["rank"], f"{s.get('scale', 20.0):g}", f"{s['learning_rate']:.0e}",
                     "all" if s["num_layers"] == -1 else s["num_layers"],
                     s["seed"], f"{s.get('trainable_M', float('nan')):.1f}", s["best_step"], f"{s['best_val_loss']:.3f}",
                     f"{v['JSON合格率']:.3f}", f"{v['整体情感准确率']:.3f}", f"{v['方面F1']:.3f}",
                     f"{v['sec_per_item']:.2f}", f"{s['train_minutes']:.0f}"])
    header = ["run", "rank", "scale", "lr", "layers", "seed", "params_M", "best_step", "best_val_loss",
              "json_valid", "sentiment_acc", "aspect_f1", "sec_per_item", "train_min"]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sweep_table.csv"), "w") as f:
        f.write(",".join(header) + "\n" + "\n".join(",".join(map(str, r)) for r in rows) + "\n")
    # LaTeX 表：报告里直接 \input
    tex = ["\\begin{tabular}{lrrrrrrr}", "\\toprule",
           "Run & Rank & Scale & LR & Layers & Best step & Val loss & Aspect F1 \\\\", "\\midrule"]
    for r in rows:
        tex.append(f"{r[0].replace('_', '-')} & {r[1]} & {r[2]} & {r[3]} & {r[4]} & {r[7]} & {r[8]} & {r[11]} \\\\")
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
