# CDT503 报告

IEEEtran 会议格式，英文，目前 6 页（要求 4–6 页；第 6 页右栏还空着，放进截图也不会超页）。`main.pdf` 是最新编译结果。

## 编译

本地（已装 tectonic，第一次会自动下载需要的宏包）：

```bash
cd ~/claude/review-lora/cdt503/report && tectonic main.tex
```

上传 TeXPage：先打包，再把 `texpage.zip` 上传成新项目，编译器必须选 XeLaTeX（作者行有中文名，用了 ctex）：

```bash
sh ~/claude/review-lora/cdt503/report/make_texpage_zip.sh
```

改了图（比如重跑了 `plot_sweep.py`）或换了截图之后，要重新打包。

## 交之前要补的

- [x] **学号**：两位组员的学号已填入作者行
- [ ] **演示截图**：启动演示（`uv run python cdt503/app_gradio.py`），点第 1 个示例"果子特别棒……"再点 Analyze，
  截取左右两栏的结果（原始模型那栏会显示 "Aspect '味道' is not in the allowed list"），
  存成 `cdt503/figures/demo_screenshot.png`。图注写的就是这个例子；换别的例子要同步改图注
- [ ] 截图加进去后重新编译，确认仍然不超过 6 页

## 图表来源

| 报告里 | 文件 | 由谁生成 |
|---|---|---|
| 图 1 系统框图 | `fig_pipeline.tex`（TikZ） | 手写 |
| 图 2 调参对比 | `figures/sweep_val_curves.pdf`、`sweep_metrics.pdf` | `cdt503/scripts/plot_sweep.py` |
| 图 3 损失曲线 | `figures/final_loss_curve.pdf` | `cdt503/scripts/plot_final_curve.py` |
| 图 4、5 人工评估 | `figures/human_per_aspect_f1.pdf`、`human_error_analysis.pdf` | `cdt503/scripts/eval_human.py` |
| 表 III 测试集 | 原始、默认两行来自 `results/final_test/summary.json`；调参后一行（3 个种子平均和范围）来自 `results/final_test_seeds/summary.json` | `cdt503/scripts/final_test_summary.py`、`cdt503/scripts/seed_summary.py` |
| 表 IV 少样本对照和成本 | 数字来自 `results/baselines_cost/summary.json` | `cdt503/scripts/baselines_and_cost.py` |
| 表 V 调参 | 数字来自 `results/sweep/sweep_table.csv`；两行 seed 43/44 复跑来自 `results/final_test_seeds/summary.json` | `cdt503/scripts/plot_sweep.py`、`cdt503/scripts/seed_summary.py` |
| 表 VI 人工评估 | 数字来自 `results/human_eval/metrics.json` | `cdt503/scripts/eval_human.py` |
| 表 VII 公平人机对比 | 数字来自 `results/human_eval_fair/fair_20.json` | `cdt503/scripts/eval_human.py` |
| III-E 商品报告的数字（93–96%、71/35、43/38 等） | `results/product_report/{hotel,tablet,fruit}/summary.json` | `cdt503/scripts/product_report_samples.py` |

表格里的数字是手写进 `main.tex` 的（方便在 TeXPage 上单独编译），如果重新跑了实验，要对照上面的文件手动更新。
