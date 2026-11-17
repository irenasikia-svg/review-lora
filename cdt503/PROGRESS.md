# CDT503 项目进度交接（2026-11-17 22:30）

新开对话时先读这份文件。项目在 `~/claude/review-lora`，分支 `cdt503`（GitHub: irenasikia-svg/review-lora，公开仓库）。
组员：Han Daiyuan (3231363) = 标注者 A，Li Mingtai (3231959) = 标注者 B。项目标题：**Beyond Star Ratings: Aspect Extraction from Chinese Reviews**。

## 规则（用户定的，一直有效）

- 调参只看验证集；测试集只在最终配置上跑一次
- 耗时超过 10 分钟的任务：先冒烟测试、报预计耗时、等用户确认
- git 提交作者用 `git -c user.name=ced commit`；**push 要用户点头**（自动模式会拦截未经确认的推送）
- 报告和 PPT 用英文；和用户沟通、代码注释用中文；用户是 ML 入门水平，要讲清楚
- 不改动已有结果，新结果放新目录

## 正在跑的

**B3 多种子重复**（lr=5e-5 最终配置，种子 43、44），2026-11-17 22:22 启动，预计 **01:45 左右**结束：

```bash
caffeinate -s sh -c 'uv run python cdt503/scripts/sweep.py --only lr5e-5_seed43 lr5e-5_seed44 && uv run python cdt503/scripts/seed_summary.py --eval-test'
```

- 日志：`cdt503/results/sweep/sweep.log`（每组完成一行）、`cdt503/results/sweep/night3.out`（末尾出现第 2 个 `exit=` 即全部结束）
- 22:10 第一次启动时，因为同时开了真实模型的 Gradio 报告页，两组都 GPU 内存不足崩了（第 40 步前，没有检查点，没损失）；22:22 单独重跑
- 如果中途断了：重新运行上面的命令即可续跑
- **跑完前不要开 Gradio、演示服务器、标注服务器或 countdown-grpo**

## 接下来要做的（按顺序）

1. **B3 收尾**：确认 `sweep.log` 里两组都"完成"，`cdt503/results/final_test_seeds/summary.json` 有 3 个种子的验证集和测试集结果
   - 改报告 `cdt503/report/main.tex`：表 III 调参后那一行改成"3 个种子的平均值（最小–最大）"；主结果段落里"each model was trained once (seed 42)"那段改成多种子说法；局限性里"Each configuration, including the final one, was trained once"改成"除最终配置外"
   - 同步 `cdt503/presentation/qa_prep.md` 的 Q10、速查表；`slides_outline.md` 第 7 页
   - 重新编译（`cd cdt503/report && tectonic main.tex`），用 pypdfium2 渲染逐页检查，确认 ≤ 6 页
   - 提交种子结果（`results/sweep/lr5e-5_seed4{3,4}/`、`results/final_test_seeds/`、`sweep.log`、`night3.out`）
2. **商品报告页**（已完成、已实测，见下）：问用户要不要写进报告第 III-E 节（一两句 + 可选截图）和 PPT 演示脚本
3. **推送**：本地有未推送的提交（`0582841` 商品报告页，以及之后的），推送前问用户
4. **用户自己做的**：
   - 演示截图存 `cdt503/figures/demo_screenshot.png`（页面现在有两个标签页，截"Compare one review"页的第 1 个示例"果子特别棒……"），然后重新编译、检查第 5–6 页
   - 在家试 `--share`、录备用视频（步骤见 `cdt503/DEMO.md`）
   - 做 PPT、计时彩排
5. 小清理：`cdt503/results/baselines_cost_smoke/` 是冒烟测试产物，可以加进 `.gitignore`

## 已完成（都已提交）

| 部分 | 结果 |
|---|---|
| 调参（10 组，验证集） | lr=5e-5 最好 0.793；lr=2e-4 发散；r=32 变差，scale 降到 10 后恢复（0.766）；顶部 8 层训练时间减半 |
| 测试集（262 条，每个模型一次） | 原始 0.513 → 默认 LoRA 0.734 → 调参后 0.807；调参 +0.073，95% 区间 [+0.038, +0.110] |
| 人工评估（100 条全新评论，2 人标注 + 仲裁） | 学生 0.701、老师 0.689、原始 0.458；学生和老师无显著差异 |
| B1 公平对比（20 条双人标注） | 组员 B 0.644、学生 0.661、老师 0.693、原始 0.419（区间重叠，不说"达到人类水平"） |
| B2 少样本（验证集） | 原始 0.538 → 给 4 个示例 0.594；LoRA 0.802 |
| B4 成本（批大小 8） | 老师 vs 学生：权重 17.2 vs 3.5 GB（4.9×），峰值 19.8 vs 5.7 GB（3.5×），1.37 vs 0.75 秒/条（1.8×）；参数 30.5B/3.3B 激活 vs 1.74B |
| 报告 | 6 页，第 6 页右栏空着；标题、学号已改；C1–C7 全部改完 |
| Gradio | 两个标签页：单条对比（8 个示例，原始模型在 5 个上出错）、商品报告页 |
| 商品报告页 | 酒店样例 150 条：好评 53%（星级 55%），整体判断与星级一致 93% |
| 备份 | 权重压缩包 `backups/review-lora-adapters-20261103.zip`（用户自己存网盘） |

## 已知的坑

- **GPU 内存**：老师模型（17 GB）、训练（~12 GB）、Gradio 批量生成（~6 GB）任意两个叠加都可能 Metal OOM。一次只跑一个
- MLX 计算流绑定线程：Gradio 里所有模型调用都走 `app_gradio.py` 的专用推理线程
- IEEEtran 表格默认 `\footnotesize`，别加 `\small`（会变大）；表格超宽就减 `\tabcolsep` 或缩短文字
- 渲染 PDF 检查版面：`uv run --with pypdfium2 python -c "..."`（本机没装 poppler）
- 删除文件不要用变量路径（`rm $S/*` 会被安全检查拦下）

## 新对话的开场白（复制粘贴即可）

> 继续 CDT503 项目。先读 ~/claude/review-lora/cdt503/PROGRESS.md，然后检查 B3 是否跑完，按"接下来要做的"第 1 步开始。
