"""报告用：最终模型（lr=5e-5）的训练/验证损失曲线，和调参前的默认配置（lr=1e-4）对比。单栏宽度 3.5 英寸。

用法：uv run python cdt503/scripts/plot_final_curve.py
输出：cdt503/figures/final_loss_curve.{pdf,png}
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
plt.rcParams.update({"font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
RUNS = [("lr5e-5", "Tuned (lr=5e-5)", "#4C72B0", "-"), ("baseline", "Default (lr=1e-4)", "#222222", "--")]


def main():
    fig, ax = plt.subplots(figsize=(3.5, 2.1))
    for name, label, color, ls in RUNS:
        d = os.path.join(ROOT, "cdt503/results/sweep", name)
        curve = json.load(open(os.path.join(d, "curve.json")))
        best = json.load(open(os.path.join(d, "summary.json")))["best_step"]
        tr = [(s, v) for s, v in curve["train"]]
        va = [(s, v) for s, v in curve["val"] if s > 1]
        ax.plot(*zip(*tr), color=color, ls=ls, lw=0.8, alpha=0.45)
        ax.plot(*zip(*va), color=color, ls=ls, lw=1.6, marker="o", ms=2.5, label=f"{label}: validation")
        ax.axvline(best, color=color, ls=":", lw=0.8)
        ax.annotate(f"best step {best}", (best, 0.012), color=color, fontsize=6.5, rotation=90,
                    ha="right", va="bottom")
    ax.plot([], [], color="#888888", lw=0.8, alpha=0.6, label="training (thin lines)")
    ax.set_xlabel("Training step (batch size 8; 228 steps = 1 epoch)")
    ax.set_ylabel("Loss (answer tokens only)")
    # 前 30 步的训练损失很大（> 1），截掉才能看清后面的差别
    ax.set_ylim(0, 0.30)
    ax.axvline(228, color="#bbbbbb", lw=0.6)
    # 说明文字放在两条"best step"虚线之间、所有曲线上方的空白处，用箭头指向第 1 轮分界线（228 步）
    ax.annotate("epoch 2 begins:\ntrain loss halves,\nval. loss flat", xy=(229, 0.24), xytext=(320, 0.255),
                fontsize=6.3, color="#666666", ha="center", va="center",
                arrowprops=dict(arrowstyle="->", color="#999999", lw=0.6))
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out = os.path.join(ROOT, "cdt503/figures/final_loss_curve")
    for ext in ("pdf", "png"):
        fig.savefig(f"{out}.{ext}", dpi=300, bbox_inches="tight")
    print("已保存", os.path.relpath(out, ROOT) + ".{pdf,png}")


if __name__ == "__main__":
    main()
