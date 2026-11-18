# Gradio 演示页面打磨 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 字体统一、Analyze 分步揭晓（原始模型扫描→出结果→LoRA 扫描→出结果）、商品报告页可点击的示例 CSV。

**Architecture:** 新建纯渲染模块 `cdt503/demo_render.py`（只拼 HTML 字符串，不依赖 gradio/mlx，可单测）；
`app_gradio.py` 的 `Engine` 单条任务改成分步信号，新增模块级生成器 `analyze_steps()` 依次产出两张卡片的 HTML，
`build_ui` 只负责接线。模型调用仍然只在推理线程里。

**Tech Stack:** Python 3.12、Gradio 6.30、MLX（不改）、pytest（用 `uv run --with pytest` 临时装，不改 pyproject）

**Spec:** `cdt503/docs/2026-11-18-gradio-polish-design.md`

## Global Constraints

- 不改模型、提示词、检查点和任何实验结果；同一条评论的模型输出和以前一致
- 所有 MLX 调用只在 `Engine` 的推理线程里
- 不加载任何外网资源：字体栈 `-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif`；等宽 `ui-monospace, "SF Mono", Menlo, monospace`
- 强调色统一为蓝色（主题 `primary_hue="blue"`，LoRA 卡片框 `#3b5bdb`）；好评绿 `#1f8a4c`、差评红 `#c2412d`（沿用现有）
- 开发和验证只用 `--mock`，端口 7861，不碰 GPU
- 代码注释用中文；页面文字用英文；提交作者 `git -c user.name=ced commit`，只提交本地，不推送

## Review Focus

1. 多人同时点 Analyze：每个人都先看到自己的排队位置，最后都拿到结果，不会有人一直停在扫描状态 → Task 3 mock 压力测试 12 并发
2. 推理线程里某一步抛异常：两张卡片都显示错误提示并结束，不会一直扫描 → Task 2 `test_engine_error_ends_with_problem_cards`
3. 某一步一直不返回：到超时后显示错误提示 → Task 2 `test_timeout_ends_with_problem_cards`
4. 评论里有 `<`、`&` 等字符，或模型给的"观点"不是原文片段/互相重叠：页面正常转义、不崩、只标能找到且不重叠的片段 → Task 1 `test_review_html_escapes_and_skips_bad_spans`
5. 手机宽度和"减少动态效果"设置：两张卡片上下排列不溢出；系统开了减少动态效果时扫描光带停止 → Task 3 浏览器 375px 截图 + CSS `@media (prefers-reduced-motion: reduce)`

---

### Task 1: 渲染模块 `demo_render.py`

**Files:**
- Create: `cdt503/demo_render.py`
- Create: `cdt503/tests/test_demo_render.py`
- Modify: `cdt503/app_gradio.py`（删掉旧的 `highlight()`、`card()`、`esc()`、`CSS`、`COLOR_MAP`，改为从 `demo_render` 导入；这一步只换导入，UI 接线留给 Task 3）

**Interfaces:**
- Produces（全部是纯函数，返回 HTML 字符串）：
  - `esc(s) -> str`
  - `opinion_spans(text: str, parsed: dict | None) -> list[tuple[int, int, str, str]]`：`(start, end, 方面英文名, "pos"|"neg")`，按 start 排序；观点为空、不在原文里、或与已选片段重叠的跳过（沿用旧 `highlight()` 的规则）
  - `review_html(text: str, parsed: dict | None) -> str`：`<div class="rl-review">`，观点用 `<mark class="pos|neg">…</mark><small class="rl-tag">Taste +</small>`
  - `result_card(result: dict, text: str) -> tuple[str, dict | None]`：`result = {"raw": str, "ms": int}`；返回 (HTML, parsed)。合格：徽章 + `review_html` + 方面表；不合格：`✗ Invalid output` + `diagnose()` 列表；都带 "Raw model output" 折叠
  - `scanning_card(text: str, who: str) -> str`：`<div class="rl-card rl-scanning">`，状态行 `"{who} is reading…"` + 带 `rl-scan` 光带的原文
  - `waiting_card(msg: str) -> str`：灰色占位卡片
  - `queue_card(ahead: int) -> str`：`"Waiting in line — {ahead} request(s) ahead of you"`（ahead=1 用单数）
  - `problem_card(msg: str) -> str`：`<div class="rl-card"><div class="rl-problems">…`
  - `CSS: str`：含 `.rl-*`、`.pr-*`（沿用现有商品报告样式）、`@keyframes rl-sweep`、淡入动画、`@media (prefers-reduced-motion: reduce)` 关闭动画
- Consumes: `diagnose(raw)` 从 `app_gradio.py` 挪进 `demo_render.py`（它只依赖 `common.ASPECTS/SENTIMENTS`）；`en()` 来自 `aspects_en`；`parse_output` 来自 `common`

- [ ] **Step 1: 写失败的测试** `cdt503/tests/test_demo_render.py`

```python
TEXT = "屏幕很清晰，但电池两天就没电了"
PARSED = {"整体情感": "负面", "方面": [
    {"方面": "使用效果", "观点": "屏幕很清晰", "情感": "正面"},
    {"方面": "使用效果", "观点": "电池两天就没电了", "情感": "负面"}]}

def test_opinion_spans_positions():
    assert opinion_spans(TEXT, PARSED) == [(0, 5, "Performance", "pos"), (7, 15, "Performance", "neg")]

def test_review_html_escapes_and_skips_bad_spans():
    text = "a<b>&c 很好"
    parsed = {"整体情感": "正面", "方面": [
        {"方面": "使用效果", "观点": "很好", "情感": "正面"},
        {"方面": "服务", "观点": "不存在的片段", "情感": "负面"},
        {"方面": "价格", "观点": "很", "情感": "正面"}]}          # 和"很好"重叠，跳过
    html = review_html(text, parsed)
    assert "a&lt;b&gt;&amp;c" in html and "<b>" not in html
    assert html.count("<mark") == 1 and 'class="pos"' in html

def test_result_card_valid_and_invalid():
    ok, p = result_card({"raw": json.dumps(PARSED, ensure_ascii=False), "ms": 1234}, TEXT)
    assert p and "Valid JSON" in ok and "1.23 s" in ok and "<mark" in ok
    bad, p2 = result_card({"raw": '{"整体情感": "中性", "方面": []}', "ms": 900}, TEXT)
    assert p2 is None and "Invalid output" in bad and "正面/负面" in bad

def test_status_cards():
    assert "rl-scan" in scanning_card("<x>", "Base model") and "&lt;x&gt;" in scanning_card("<x>", "Base model")
    assert "1 request ahead" in queue_card(1) and "3 requests ahead" in queue_card(3)
    assert "rl-problems" in problem_card("boom")

def test_css_has_reduced_motion():
    assert "prefers-reduced-motion" in CSS and "@keyframes rl-sweep" in CSS
```

（测试文件开头：`sys.path` 加 `cdt503/`、`scripts/`、`cdt503/scripts/`，`from demo_render import ...`，`import json`）

- [ ] **Step 2: 运行，确认失败**

Run: `cd ~/claude/review-lora && uv run --with pytest pytest cdt503/tests/test_demo_render.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'demo_render'`

- [ ] **Step 3: 实现 `cdt503/demo_render.py`**（签名见 Interfaces；`opinion_spans` 用 `str.find` 找第一次出现，规则照旧 `highlight()`）；`app_gradio.py` 改成 `from demo_render import CSS, diagnose, esc, ...`，旧 `card(result)` 的调用点暂时改为 `result_card(result, text)` 以保持页面能跑

- [ ] **Step 4: 运行，确认通过**

Run: `uv run --with pytest pytest cdt503/tests/test_demo_render.py -q`
Expected: `5 passed`

- [ ] **Step 5: 提交**

```bash
git add cdt503/demo_render.py cdt503/tests/test_demo_render.py cdt503/app_gradio.py
git -c user.name=ced commit -m "演示页：渲染逻辑拆到 demo_render.py，原文高亮改为自绘 HTML"
```

---

### Task 2: 推理线程分步交结果 + `analyze_steps` 生成器

**Files:**
- Modify: `cdt503/app_gradio.py`（`Engine`、`mock_output`、新增 `CompareJob`、`analyze_steps`）
- Create: `cdt503/tests/test_analyze_steps.py`

**Interfaces:**
- Consumes: Task 1 的 `result_card`、`scanning_card`、`waiting_card`、`queue_card`、`problem_card`
- Produces:
  - `class CompareJob`：属性 `ticket: int`、`started: threading.Event`、`base: Future`、`lora: Future`
  - `Engine(adapter, mock=False, mock_delay=1.5)`；`Engine.submit(text) -> CompareJob`；`Engine.ahead(job) -> int`（= `job.ticket - 1 - 已完成任务数`，下限 0；批量任务也计入已完成数）
  - 推理线程处理 compare：`started.set()` → 跑原始模型 → `base.set_result({"raw", "ms"})` → 跑 LoRA → `lora.set_result(...)`；任一步异常时，对还没完成的 future 都 `set_exception`
  - `mock_output(text, lora, delay)`：单条用 `engine.mock_delay`，批量（商品报告）用 0.02 秒/条
  - `analyze_steps(engine, text, timeout=TIMEOUT_SEC) -> Iterator[tuple[str, str]]`：产出 `(左卡片 HTML, 右卡片 HTML)`，顺序：
    1. 未开始时：每 0.4 秒检查一次；排队数 n > 0 且和上次不同才产出 `(queue_card(n), queue_card(n))`（n = 0 时不产出，继续等）
    2. `(scanning_card(text, "Base model"), waiting_card("Waiting for the base model…"))`
    3. `(base 结果卡, scanning_card(text, "LoRA model"))`
    4. `(base 结果卡, lora 结果卡)`
    - 超时或异常：产出 `(problem_card(...), problem_card(...))` 后结束（已出结果的一边保留结果卡）
  - 空输入、截断、未预热、加载失败的检查留在 `build_ui` 的包装函数里（Task 3），`analyze_steps` 假设输入已清洗

- [ ] **Step 1: 写失败的测试** `cdt503/tests/test_analyze_steps.py`

```python
def test_steps_reveal_base_then_lora():
    eng = Engine("unused", mock=True, mock_delay=0.05); eng.ready.wait(5)
    steps = list(analyze_steps(eng, "收到就是坏的，客服不理人", timeout=5))
    assert "rl-scan" in steps[0][0] and "rl-scan" not in steps[0][1]
    assert "rl-scanning" not in steps[-2][0] and "rl-scan" in steps[-2][1]
    assert all("rl-scanning" not in h for h in steps[-1]) and all("rl-card" in h for h in steps[-1])

def test_engine_error_ends_with_problem_cards(monkeypatch):
    eng = Engine("unused", mock=True, mock_delay=0.01); eng.ready.wait(5)
    monkeypatch.setattr(eng, "_run", lambda text, lora: (_ for _ in ()).throw(RuntimeError("boom")))
    last = list(analyze_steps(eng, "测试", timeout=5))[-1]
    assert all("rl-problems" in h for h in last)

def test_timeout_ends_with_problem_cards():
    class Stuck:                      # 任务永远不开始
        def submit(self, text): return CompareJob(ticket=2)
        def ahead(self, job): return 1
    last = list(analyze_steps(Stuck(), "测试", timeout=0.5))[-1]
    assert all("rl-problems" in h for h in last)

def test_queue_position_shown_first():
    eng = Engine("unused", mock=True, mock_delay=0.3); eng.ready.wait(5)
    first = eng.submit("占位任务")                 # 先占住推理线程
    steps = list(analyze_steps(eng, "第二个请求", timeout=5))
    assert "ahead of you" in steps[0][0]
    first.lora.result(5)
```

（`CompareJob(ticket=...)` 的构造函数：`CompareJob(ticket: int)`，其余属性在 `__init__` 里新建）

- [ ] **Step 2: 运行，确认失败**

Run: `uv run --with pytest pytest cdt503/tests/test_analyze_steps.py -q`
Expected: FAIL，`ImportError: cannot import name 'analyze_steps'`

- [ ] **Step 3: 按 Interfaces 实现**（`ticket` 和已完成数用 `threading.Lock` 保护；`analyze_steps` 用 `job.started.wait(0.4)` 轮询、`time.monotonic()` 计总超时；`Future.result(timeout=剩余时间)`）

- [ ] **Step 4: 运行全部测试，确认通过**

Run: `uv run --with pytest pytest cdt503/tests -q`
Expected: `9 passed`

- [ ] **Step 5: 提交**

```bash
git add cdt503/app_gradio.py cdt503/tests/test_analyze_steps.py
git -c user.name=ced commit -m "演示页：推理线程分步交结果，analyze_steps 依次产出排队/扫描/结果"
```

---

### Task 3: 页面接线、示例文件、文档

**Files:**
- Modify: `cdt503/app_gradio.py`（`build_ui`、`main`）
- Modify: `cdt503/scripts/stress_test_demo.py`（LoRA 卡片从 `out[2]` 改为 `out[1]`）
- Modify: `cdt503/DEMO.md`、`cdt503/presentation/demo_script.md`（"选 Hotel 样例"→"点 Hotel 示例文件"）
- Modify: `.gitignore`（加 `.gradio/`）

**Interfaces:**
- Consumes: Task 1 `CSS`；Task 2 `analyze_steps`、`Engine`
- 页面变化（其余照旧）：
  - `THEME = gr.themes.Soft(primary_hue="blue", font=[Global Constraints 的字体栈], font_mono=[等宽栈])`，`launch(theme=THEME, css=CSS)`
  - 单条对比：删掉两个 `gr.HighlightedText`，每栏只剩标题 + `gr.HTML`；`analyze(text)` 包装成生成器：做原有的空输入/截断/预热/加载失败检查（空输入 `gr.Warning` 后 `yield gr.skip(), gr.skip()`），然后 `yield from analyze_steps(engine, text)`
  - 事件：`btn.click` 和 `box.submit` 用 `outputs=[base_out, lora_out]`、`show_progress="hidden"`、`concurrency_limit=16`、`api_name="analyze"`（只在 click 上设）
  - 商品报告：删掉 `rep_sample` 下拉框；`gr.Examples([[p] for p in SAMPLES.values()], inputs=rep_file, example_labels=["Hotel · 150 reviews", "Tablet · 150 reviews", "Fruit · 150 reviews"], label="…or click a sample file")`；`report(text, upload, progress=...)` 去掉 `sample` 参数
  - 两栏结果在空状态时显示 `waiting_card("Results appear here")`（`gr.HTML(value=...)`），不再有占位图标

- [ ] **Step 1: 实现上述接线**

- [ ] **Step 2: 跑测试**

Run: `uv run --with pytest pytest cdt503/tests -q`
Expected: `9 passed`

- [ ] **Step 3: mock 模式启动，内置浏览器验证**

Run（后台）: `uv run python cdt503/app_gradio.py --mock --port 7861`
检查（桌面宽度）：标题和正文是苹方/系统字体（`getComputedStyle(document.body).fontFamily` 不含 Montserrat）；点示例 1 → Analyze，分别截到"左扫描/右等待"、"左结果/右扫描"、"两边结果"三帧；控制台无报错；网络请求里没有 `fonts.googleapis.com`
检查（商品报告）：点 "Hotel · 150 reviews" → 上传框出现 hotel.csv → Generate report → 出 KPI、图、CSV
检查（手机 375px）：两栏上下排列，无横向滚动

- [ ] **Step 4: mock 压力测试**

Run: `uv run python cdt503/scripts/stress_test_demo.py --url http://127.0.0.1:7861/ --n 12`
Expected: `成功 12/12`，空输入和超长输入两行都"正常返回"

- [ ] **Step 5: 停掉 mock 服务，改文档，提交**

```bash
git add cdt503/app_gradio.py cdt503/scripts/stress_test_demo.py cdt503/DEMO.md cdt503/presentation/demo_script.md .gitignore cdt503/docs/
git -c user.name=ced commit -m "演示页：系统字体、分步揭晓动画、商品报告示例文件"
```
