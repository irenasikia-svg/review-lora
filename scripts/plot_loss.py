"""第 5 步之后：从训练日志里画出损失曲线 → results/loss_curve.png

怎么看这张图：
  - 训练损失（train）一直往下走：模型在记住训练数据
  - 验证损失（valid）是它没见过的数据上的表现。
    如果训练损失还在降、验证损失却开始回升，就是"过拟合"——死记硬背，不会举一反三了。
"""
import re

import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def main():
    # 去掉终端颜色代码后，日志里每行形如 "  60    0.164 ▼ ..."（训练）或 "  60    val 0.215 ..."（验证）
    log = re.sub(r"\x1b\[[0-9;]*m", "", open("logs/train.log").read())
    train = [(int(i), float(v)) for i, v in re.findall(r"^\s*(\d+)\s+([\d.]+) [▼▲]", log, flags=re.M)]
    val = [(int(i), float(v)) for i, v in re.findall(r"^\s*(\d+)\s+val ([\d.]+)", log, flags=re.M)]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(*zip(*train), label="训练损失", color="#4C72B0", linewidth=1.5)
    ax.plot(*zip(*val), label="验证损失", color="#DD8452", marker="o", linewidth=2)
    ax.set_xlabel("训练步数")
    ax.set_ylabel("损失（越低越好）")
    ax.set_title("LoRA 微调 Qwen3-1.7B：损失曲线")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig("results/loss_curve.png", dpi=150)
    print("已保存 results/loss_curve.png")
    print("验证损失：", val)


if __name__ == "__main__":
    main()
