# 演示页风格 B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Gradio 演示页改成参考稿 B 的单页滚动版（开头、How it works、Results、Try it live、Product report），带滚动出场动画。

**Architecture:** 介绍部分和各段标题是 `demo_render.py` 里的纯函数（返回 HTML），样式在 `CSS`，动画脚本是 `HEAD_JS`（通过 `launch(head=...)` 注入）；`app_gradio.py` 的 `build_ui` 去掉标签页、按段落排布现有组件，回调逻辑不动。

**Tech Stack:** Python 3.12、Gradio 6.30（`launch(css=, head=)`）、pytest（`uv run --with pytest`）

**Spec:** `cdt503/docs/2026-11-19-gradio-style-b-design.md`；参考稿 `cdt503/docs/mockups/style-b-product.html`

## Global Constraints

- 不改模型、推理线程、`analyze_steps`、商品报告计算；`/analyze` 接口和输出顺序不变
- 不从外网加载任何资源；系统字体栈沿用 `FONT`
- 颜色照参考稿 B：正文 `#1D1D1F`、次要 `#6E6E73`、色带 `#F5F5F7`、强调蓝 `#3B5BDB`；好评绿 `#2E9E6A`、差评红 `#E0603F`
- 动画只用于介绍部分和段落标题；演示输出区（`base_out`、`lora_out`、报告结果）不加入场动画
- 默认可见：只有 `<html>` 上有 `js-anim` 类时 `.reveal` 才先隐藏；`prefers-reduced-motion: reduce` 时不加 `js-anim`
- 提交作者 `git -c user.name=ced commit`，只提交本地

## Review Focus

1. 脚本没运行或报错：页面内容仍全部可见 → Task 1 `test_reveal_hidden_only_under_js_anim`
2. Gradio 后渲染出的元素（重新连接、切换显示）：不会卡在隐藏状态 → Task 1 `HEAD_JS` 用 MutationObserver + 3 秒兜底把所有 `.reveal` 设为可见；`test_head_js_has_fallback`
3. 手机宽度：三列卡片变一列，"窗口"不溢出 → Task 3 浏览器 375px 检查
4. 演示时直接跳到演示区：`#try` 锚点可用 → Task 1 `test_intro_has_sections_and_anchor` + Task 3 浏览器检查
5. 压力测试和截图脚本仍能用 → Task 3 压力测试 25/25、截图脚本重跑

---

### Task 1: 介绍区 HTML、样式和动画脚本

**Files:**
- Modify: `cdt503/demo_render.py`
- Test: `cdt503/tests/test_demo_render.py`（追加）

**Interfaces:**
- Produces:
  - `intro_html() -> str`：三段，分别是 `<section class="rl-hero">`（含 `href="#try"` 的按钮和高亮依次亮起的评论）、`<section id="how" class="rl-band">`（三张 `.rl-feature` 卡）、`<section id="results">`（三张卡，数字带 `data-count`：`0.80`、`5`（后缀 `×`），中间一张是 `≈`）
  - `section_head(title: str, sub: str, anchor: str) -> str`：`<div id="{anchor}" class="rl-section-head reveal">`，标题 + 一行说明
  - `CSS`：在现有基础上追加 B 风格（`.rl-hero`、`.rl-band`、`.rl-feature`、`.rl-kpi`、`.rl-window` 窗口框、Gradio 按钮/输入框/示例的圆角药丸样式、`html.js-anim .reveal{opacity:0}` 和 `.reveal.in`）
  - `HEAD_JS: str`：一段 `<script>`；不满足减少动态效果时给 `<html>` 加 `js-anim`；IntersectionObserver 给 `.reveal` 加 `in`、触发 `[data-count]` 计数；MutationObserver 观察后出现的 `.reveal`；3 秒后把仍未出场的 `.reveal` 全部加 `in`（兜底）

- [ ] **Step 1: 写失败的测试**（追加到 `test_demo_render.py`，导入 `intro_html, section_head, HEAD_JS`）

```python
def test_intro_has_sections_and_anchor():
    h = intro_html()
    assert 'class="rl-hero' in h and 'id="how"' in h and 'id="results"' in h and 'href="#try"' in h
    assert 'data-count="0.80"' in h and 'data-count="5"' in h and h.count('class="rl-feature') == 3

def test_section_head():
    h = section_head("Try it live", "Same model, twice.", "try")
    assert 'id="try"' in h and "Try it live" in h and "reveal" in h

def test_reveal_hidden_only_under_js_anim():
    import re
    assert "html.js-anim .reveal" in CSS
    assert not re.search(r"(^|[}\s])\.reveal\s*\{[^}]*opacity:\s*0", CSS)  # 不能无条件隐藏

def test_head_js_has_fallback():
    for s in ("js-anim", "IntersectionObserver", "MutationObserver", "prefers-reduced-motion", "setTimeout"):
        assert s in HEAD_JS

def test_no_external_resources():
    for part in (CSS, HEAD_JS, intro_html()):
        assert "http://" not in part and "https://" not in part
```

- [ ] **Step 2: 运行，确认失败**

Run: `uv run --with pytest pytest cdt503/tests/test_demo_render.py -q`
Expected: FAIL，`ImportError: cannot import name 'intro_html'`

- [ ] **Step 3: 实现**（文字、数字照参考稿 B 的开头、How it works、Results 三段；图标用参考稿里的三个内联 SVG）

- [ ] **Step 4: 运行，确认通过**

Run: `uv run --with pytest pytest cdt503/tests -q`
Expected: `18 passed`

- [ ] **Step 5: 提交** `git -c user.name=ced commit -m "演示页风格 B：介绍区 HTML、样式和出场动画脚本"`

---

### Task 2: 单页布局

**Files:**
- Modify: `cdt503/app_gradio.py`（`build_ui`、`main`）
- Test: `cdt503/tests/test_layout.py`（新建）

**Interfaces:**
- Consumes: Task 1 的 `intro_html`、`section_head`、`CSS`、`HEAD_JS`
- 布局（自上而下）：`gr.HTML(intro_html())` → `gr.HTML(section_head("Try it live", …, "try"))` → `gr.Column(elem_classes="rl-window")` 里放现有的输入框/按钮/示例/两栏结果（LoRA 一栏仍是 `rl-lora`）和"16 个方面"折叠 → `gr.HTML(section_head("Product report", …, "report"))` → `gr.Column(elem_classes="rl-window")` 里放现有报告组件 → 页脚小字
- 去掉 `gr.Tab`；去掉旧的顶部 `## Beyond Star Ratings…` 标题（由开头一段代替），适配器名放到页脚
- `main`：`demo.launch(..., css=CSS, head=HEAD_JS, theme=theme)`

- [ ] **Step 1: 写失败的测试** `test_layout.py`

```python
def test_page_is_one_scroll_and_keeps_api():
    eng = Engine("unused", mock=True, mock_delay=0.01); eng.ready.wait(5)
    demo = build_ui(eng, "mock")
    blocks = list(demo.blocks.values())
    assert not any(isinstance(b, gr.Tab) for b in blocks)
    assert sum("rl-window" in (getattr(b, "elem_classes", None) or []) for b in blocks) == 2
    assert any(getattr(fn, "api_name", None) == "analyze" for fn in demo.fns.values())
```

- [ ] **Step 2: 运行，确认失败**（现在有两个 `gr.Tab`）

Run: `uv run --with pytest pytest cdt503/tests/test_layout.py -q`
Expected: FAIL（assert not any(isinstance(b, gr.Tab) …)）

- [ ] **Step 3: 按 Interfaces 改 `build_ui` 和 `main`**

- [ ] **Step 4: 运行全部测试**

Run: `uv run --with pytest pytest cdt503/tests -q`
Expected: `19 passed`

- [ ] **Step 5: 提交** `git -c user.name=ced commit -m "演示页风格 B：去掉标签页，改成单页滚动"`

---

### Task 3: 验证、截图、同步材料

**Files:**
- Modify: `cdt503/scripts/capture_demo_screens.py`（不再点标签页：滚动到 `#report` 再点 Hotel 示例；结果区选择器改为两栏所在的行）
- Modify: `cdt503/DEMO.md`、`cdt503/presentation/demo_script.md`（"切到 Product report 标签页"→"往下滚到 Product report"）
- 重新生成：`cdt503/figures/demo_screens/*`、`cdt503/figures/demo_screenshot.png`、PPT（`sh cdt503/presentation/deck/build.sh`）、报告 PDF 和 TeXPage 压缩包；复制到 `~/Documents/503`

- [ ] **Step 1: mock 模式浏览器检查**（端口 7861）：桌面宽度截开头、How it works、Results、Try it live 四屏；跑一次示例（分步揭晓仍正常）；点 "Try it live" 跳到 `#try`；Hotel 示例文件生成报告；手机 375px 无横向滚动；控制台无报错；无外网请求
- [ ] **Step 2: mock 压力测试**：`uv run python cdt503/scripts/stress_test_demo.py --url http://127.0.0.1:7861/ --n 25`，Expected `成功 25/25`
- [ ] **Step 3: 真实模型截图**：启动真实演示后 `uv run --with playwright python cdt503/scripts/capture_demo_screens.py`，三张图都生成；重新裁剪报告图 6 和 PPT 用图
- [ ] **Step 4: 重建 PPT、报告**，Keynote 导出检查第 8 页；报告仍 6 页
- [ ] **Step 5: 改文档、复制到 `~/Documents/503`、提交**
