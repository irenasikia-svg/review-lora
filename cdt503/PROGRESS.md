# CDT503 项目进度交接（2026-11-18 更新）

新开对话时先读这份文件。项目在 `~/claude/review-lora`，分支 `cdt503`（GitHub: irenasikia-svg/review-lora，公开仓库）。
组员：Han Daiyuan (3231363) = 标注者 A，Li Mingtai (3231959) = 标注者 B。项目标题：**Beyond Star Ratings: Aspect Extraction from Chinese Reviews**。

## 规则（用户定的，一直有效）

- 调参只看验证集；测试集只在最终配置上跑一次
- 耗时超过 10 分钟的任务：先冒烟测试、报预计耗时、等用户确认
- git 提交作者用 `git -c user.name=ced commit`；**push 要用户点头**（自动模式会拦截未经确认的推送）
- 报告和 PPT 用英文；和用户沟通、代码注释用中文；用户是 ML 入门水平，要讲清楚
- 不改动已有结果，新结果放新目录

## 正在跑的

没有。B3 已于 2026-11-18 01:45 跑完（两组都正常结束，没再崩）。

## 接下来要做的（按顺序）

1. ~~B3 收尾~~ **已完成**（11-18）：报告表 III 调参后一行改成 3 个种子平均 0.801（0.790–0.807），表 V 加了 seed 43/44 两行，
   主结果、调参噪声阈值（0.01 → 0.02）、学习率段落、局限性、结论、摘要都同步改了；qa_prep Q9/Q10/Q13/Q14 和速查表、slides 第 6/7 页已同步；
   重新编译仍是 6 页
2. ~~商品报告页写进报告~~ **已完成**（11-18）：报告 III-E 加了一段、摘要加了半句；演示脚本加了 15 秒报告段（上台前先生成好 Hotel 报告）；qa_prep 加了 Q22；数字来自 `cdt503/results/product_report/`（`scripts/product_report_samples.py` 离线生成）。第 6 页右栏还空一半，想加报告页截图或 `results/product_report/hotel/aspects.png` 条形图都放得下
3. **推送**：每次推送前问用户
3a. ~~演示页打磨~~ **已完成**（11-18）：系统字体、分步揭晓动画、商品报告示例文件；审查修复（排队异步、离开的请求取消）
3b. ~~PPT 初版 + 讲稿~~ **已完成**（11-18）：`cdt503/presentation/CDT503_BeyondStarRatings_slides.pptx`（9 页，明亮简洁），生成脚本 `cdt503/presentation/deck/build.sh`，讲稿内容在 `deck/speech.js`（同时生成 PPT 备注和 `speech_script.md`）。注意：pptxgenjs 写的图表 Keynote 显示空白，所以图表由 `deck/add_charts.py` 用 python-pptx 加；检查渲染用 Keynote 导出 PDF
3c. **交付材料文件夹** `~/Documents/503/`（11-18 整理）：报告 PDF + TeXPage 源码、PPT、讲稿/问答/演示脚本（docx）、截图、样例、分工、代码压缩包、权重备份；`README.md` 是索引。仓库里改了东西要重新复制过去
4. **用户自己做的**：
   - ~~演示截图~~ 已用真实模型截好（`cdt503/figures/demo_screenshot.png`，报告图 6）
   - 在家试 `--share`、录备用视频（步骤见 `cdt503/DEMO.md`）
   - 通读 PPT 初版、按自己的习惯改讲稿、计时彩排
5. 小清理：`cdt503/results/baselines_cost_smoke/` 是冒烟测试产物，可以加进 `.gitignore`

## 已完成（都已提交）

| 部分 | 结果 |
|---|---|
| 调参（10 组，验证集） | lr=5e-5 最好 0.793；lr=2e-4 发散；r=32 变差，scale 降到 10 后恢复（0.766）；顶部 8 层训练时间减半 |
| 测试集（262 条，每个模型一次） | 原始 0.513 → 默认 LoRA 0.734 → 调参后 0.807；调参 +0.073，95% 区间 [+0.038, +0.110] |
| B3 多种子（最终配置 seed 42/43/44） | 验证 0.793 / 0.788 / 0.807（平均 0.796）；测试 0.807 / 0.790 / 0.805（平均 0.801），每个种子都比默认高 ≥ 0.056；报告的 seed 42 刚好是测试最高的 |
| 人工评估（100 条全新评论，2 人标注 + 仲裁） | 学生 0.701、老师 0.689、原始 0.458；学生和老师无显著差异 |
| B1 公平对比（20 条双人标注） | 组员 B 0.644、学生 0.661、老师 0.693、原始 0.419（区间重叠，不说"达到人类水平"） |
| B2 少样本（验证集） | 原始 0.538 → 给 4 个示例 0.594；LoRA 0.802 |
| B4 成本（批大小 8） | 老师 vs 学生：权重 17.2 vs 3.5 GB（4.9×），峰值 19.8 vs 5.7 GB（3.5×），1.37 vs 0.75 秒/条（1.8×）；参数 30.5B/3.3B 激活 vs 1.74B |
| 报告 | 6 页，第 6 页右栏空着；标题、学号已改；C1–C7 全部改完 |
| Gradio | 风格 B 单页滚动（11-19）：开头 → How it works → Results（带出场动画）→ Try it live（单条对比，8 个示例）→ Product report；参考稿 `cdt503/docs/mockups/` |
| 商品报告页 | 150 条样例：酒店好评 53%（星级 55%）一致 93%；平板 49%（50%）96%；水果 41%（45%）95% |
| 备份 | 权重压缩包 `backups/review-lora-adapters-20261103.zip`（用户自己存网盘） |

## 已知的坑

- **GPU 内存**：老师模型（17 GB）、训练（~12 GB）、Gradio 批量生成（~6 GB）任意两个叠加都可能 Metal OOM。一次只跑一个
- MLX 计算流绑定线程：Gradio 里所有模型调用都走 `app_gradio.py` 的专用推理线程
- IEEEtran 表格默认 `\footnotesize`，别加 `\small`（会变大）；表格超宽就减 `\tabcolsep` 或缩短文字
- 渲染 PDF 检查版面：`uv run --with pypdfium2 python -c "..."`（本机没装 poppler）
- 删除文件不要用变量路径（`rm $S/*` 会被安全检查拦下）

## 新对话的开场白（复制粘贴即可）

> 继续 CDT503 项目。先读 ~/claude/review-lora/cdt503/PROGRESS.md，然后检查 B3 是否跑完，按"接下来要做的"第 1 步开始。
