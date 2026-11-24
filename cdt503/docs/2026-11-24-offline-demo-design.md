# 离线演示页：设计（2026-11-24，用户已选定"公开网页 + 本地副本"）

## 为什么

现场演示依赖讲台电脑上的模型和服务器。要一份不依赖它们的演示：现场出问题时点 PPT 里的链接就能继续讲，同学和老师课后也能打开看。

## 目标

- 一个自包含的网页（CSS、脚本、数据、图片全部内联，不加载任何外部资源），外观和风格 B 演示页一致：开头、How it works、Results、试用区、商品报告
- 试用区：8 个内置示例，点一下按真实顺序回放（左边原始模型先扫描、出结果，右边 LoRA 再扫描、出结果），结果是**真实模型事先录下的输出**
- 商品报告区：Hotel / Tablet / Fruit 三个样例，点一下显示已经用真实模型生成好的报告（KPI、最受好评/最常被抱怨、方面表、条形图）
- 页面上写明这是离线版、结果是事先录制的，现场版用一键启动
- 发布到 GitHub Pages：`https://irenasikia-svg.github.io/review-lora/`（`review-lora` 仓库新开 `gh-pages` 分支，只放这个页面）；同一个文件复制到 `~/Documents/503/pre/` 作为本地副本
- PPT 第 8 页加一行可点击的链接（网址）

## 不做的

- 不能输入自己的评论（离线没有模型）；不新生成任何结果，所有输出都来自真实模型的记录
- 不改现场演示页、不改模型和实验结果

## 绝不能出现的

- 编造或手改模型输出：8 个示例的输出必须是这次用真实模型录下的原始输出，报告数字来自 `cdt503/results/product_report/`
- 依赖外网资源（字体、脚本、图片）

## 做法（我定的）

- `cdt503/scripts/record_offline_demo.py`：加载真实模型（和演示页同一个检查点），对 8 个示例各跑一次原始模型和 LoRA，存原始输出和用时到 `cdt503/offline_demo/recorded.json`
- `cdt503/scripts/build_offline_demo.py`：用 `demo_render.py` 现成的函数把录下的输出渲染成结果卡片（和现场页一模一样），用 `product_report.render_html` 渲染三份报告，条形图转成内联图片，拼成 `cdt503/offline_demo/index.html`
- 发布：`gh-pages` 分支只含 `index.html` 和 `.nojekyll`；用 `gh api` 打开该仓库的 Pages（来源 `gh-pages` 分支根目录）
- PPT：生成脚本和用户自己改过的那份 PPT（`pre/` 里）都在第 8 页加链接；改用户那份时只加这一个文本框，其他不动
