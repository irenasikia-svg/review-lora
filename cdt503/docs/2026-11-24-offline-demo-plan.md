# 离线演示页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 一个自包含的离线演示网页（真实模型事先录下的输出 + 已生成的商品报告），发布到 GitHub Pages，并在 PPT 第 8 页放链接。

**Architecture:** 录制脚本用 `app_gradio.Engine`（真实模型）跑 8 个示例存 JSON；构建脚本复用 `demo_render.py` 和 `product_report.render_html` 渲染出和现场页一样的卡片，拼成一个内联了 CSS、脚本、数据、图片的 `index.html`。

**Tech Stack:** Python 3.12、MLX（只在录制时用）、纯 HTML/CSS/JS、`gh` CLI（GitHub Pages）

**Spec:** `cdt503/docs/2026-11-24-offline-demo-design.md`

## Global Constraints

- 示例输出只来自真实模型的录制（`recorded.json`），不手改；报告数字只来自 `cdt503/results/product_report/<样例>/`
- 页面不加载任何外部资源（无 `src="http`、`href="http` 的样式或脚本、无外部字体）
- 页面写明是离线录制版
- 发布地址 `https://irenasikia-svg.github.io/review-lora/`，`gh-pages` 分支只含 `index.html`、`.nojekyll`
- 改用户自己的 PPT（`~/Documents/503/pre/CDT503_BeyondStarRatings_slides.pptx`）前先备份，只加一个链接文本框
- 提交作者 `git -c user.name=ced commit`；推送和打开 Pages 是用户已同意的公开发布

## Review Focus

1. 手机打开（同学扫码）：版面不横向滚动，示例按钮能点 → Task 2 浏览器 375px 检查
2. 连续快速点多个示例：前一次的回放不会和后一次叠在一起 → Task 2 `test_click_cancels_previous_playback`（浏览器）
3. 没网时双击本地副本：页面完整（无外部资源）→ Task 2 `test_page_is_self_contained`
4. 报告样例切换：三份报告各自显示，图片能出来 → Task 2 浏览器检查
5. PPT 链接在 Keynote 里可点 → Task 3 Keynote 导出 PDF 检查链接

---

### Task 1: 录制真实输出

**Files:**
- Create: `cdt503/scripts/record_offline_demo.py`
- Create（生成）: `cdt503/offline_demo/recorded.json`
- Test: `cdt503/tests/test_offline_demo.py`

**Interfaces:**
- Produces: `recorded.json` = `[{"text": str, "base": {"raw": str, "ms": int}, "lora": {"raw": str, "ms": int}}, ...]`，顺序和 `app_gradio.EXAMPLES` 一致，共 8 条

- [ ] **Step 1: 写测试** `test_recorded_outputs_complete`：文件存在时，8 条、文本和 `EXAMPLES` 一一对应、每条 base/lora 的 `raw` 非空、`ms > 0`；LoRA 8 条全部能被 `parse_output` 解析
- [ ] **Step 2: 运行，确认失败**（文件还不存在）
- [ ] **Step 3: 写录制脚本**（`Engine(adapter)` 真实模型，`engine.submit(text)` 等两个 future；GPU 上没有别的模型程序时运行）并运行
- [ ] **Step 4: 运行测试，确认通过**；核对原始模型在示例 1、2、3、4、6 上不合格（和 `DEMO.md` 的记录一致，不一致就如实记下，不改数据）
- [ ] **Step 5: 提交**

### Task 2: 构建离线页面

**Files:**
- Create: `cdt503/scripts/build_offline_demo.py`
- Create（生成）: `cdt503/offline_demo/index.html`
- Test: `cdt503/tests/test_offline_demo.py`（追加）

**Interfaces:**
- Consumes: Task 1 `recorded.json`；`demo_render.intro_html / result_card / scanning_card / waiting_card / CSS / HEAD_JS`；`product_report.render_html`；`results/product_report/<hotel|tablet|fruit>/summary.json` 和 `aspects.png`
- Produces: `build_page() -> str`（整页 HTML），`main()` 写文件

- [ ] **Step 1: 写测试**：`test_page_is_self_contained`（无外部 `src=`/样式表链接，无 `fonts.googleapis`）；`test_page_has_all_examples_and_reports`（8 个示例按钮、3 个报告按钮、"offline" 说明）；`test_cards_come_from_recording`（页面里的每条 LoRA 结果卡片等于用 `result_card(recorded[i]["lora"], text)` 渲染的结果）
- [ ] **Step 2: 运行，确认失败**
- [ ] **Step 3: 实现**：页面 = 开头/How it works/Results（`intro_html()`，按钮改成跳到 `#try`）+ 试用区（示例按钮；点击后按录到的用时回放：左边扫描 → 左边结果 → 右边扫描 → 右边结果，用时压缩到 1–2 秒；再点别的示例会取消前一次）+ 报告区（三个样例按钮，显示预先渲染的报告和内联图片）+ 页脚（离线说明、GitHub 代码仓库地址）
- [ ] **Step 4: 运行测试；浏览器检查**（桌面和 375px：回放顺序、快速连点、三份报告、无横向滚动、无控制台错误）
- [ ] **Step 5: 提交**

### Task 3: 发布、PPT 链接、本地副本

- [ ] **Step 1**: 建 `gh-pages` 孤立分支（只含 `index.html`、`.nojekyll`），推送；`gh api -X POST repos/irenasikia-svg/review-lora/pages` 打开 Pages（来源 `gh-pages` `/`）；等构建完成，`curl` 网址返回 200 且内容等于本地文件
- [ ] **Step 2**: `build_deck.js` 第 8 页加链接文本（"Offline demo: irenasikia-svg.github.io/review-lora"，超链接到网址）；重建 PPT；用户那份 PPT 备份后用 python-pptx 在第 8 页加同样的文本框；Keynote 导出检查第 8 页
- [ ] **Step 3**: `index.html` 复制到 `~/Documents/503/pre/离线演示_Offline_Demo.html`；README、`DEMO.md`、演示脚本"出问题时"一栏加上离线演示
- [ ] **Step 4**: 提交（`cdt503` 分支），询问后推送
