"""生成离线演示页：一个自包含的 HTML（样式、脚本、数据、图片都内联，不加载外部资源）。

- 试用区：8 个内置示例，回放 record_offline_demo.py 录下的真实输出（左边原始模型先出、右边 LoRA 后出）
- 报告区：Hotel / Tablet / Fruit 三份真实生成的商品报告（cdt503/results/product_report/）
结果卡片用 demo_render.py 渲染，和现场演示页一模一样。

用法：uv run python cdt503/scripts/build_offline_demo.py
输出：cdt503/offline_demo/index.html（发布到 GitHub Pages，也复制一份给本地双击打开）
"""
import base64
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("cdt503", "scripts", "cdt503/scripts"):
    sys.path.insert(0, os.path.join(ROOT, sub))

import product_report  # noqa: E402
from aspects_en import ASPECT_EN  # noqa: E402
from common import ASPECTS  # noqa: E402
from demo_render import (CSS, HEAD_JS, esc, intro_html, result_card, scanning_card,  # noqa: E402
                         section_head, waiting_card)

RECORDED = os.path.join(ROOT, "cdt503/offline_demo/recorded.json")
REPORTS = [("Hotel", "hotel"), ("Tablet", "tablet"), ("Fruit", "fruit")]
OUT = os.path.join(ROOT, "cdt503/offline_demo/index.html")
REPO = "github.com/irenasikia-svg/review-lora"


def _label(text, n=14):
    return text if len(text) <= n else text[:n] + "…"


def build_data():
    """页面用到的全部数据：每个示例的扫描卡片和结果卡片（HTML）、录到的用时，三份报告的 HTML 和图。"""
    records = json.load(open(RECORDED, encoding="utf-8"))["records"]
    examples = []
    for r in records:
        t = r["text"]
        examples.append({
            "text": t, "label": _label(t),
            "base_ms": r["base"]["ms"], "lora_ms": r["lora"]["ms"],
            "base_scan": scanning_card(t, "Base model"), "lora_scan": scanning_card(t, "LoRA model"),
            "wait": waiting_card("Waiting for the base model…"),
            "base_html": result_card(r["base"], t)[0], "lora_html": result_card(r["lora"], t)[0],
        })
    reports = []
    for name, key in REPORTS:
        d = os.path.join(ROOT, "cdt503/results/product_report", key)
        rep = json.load(open(os.path.join(d, "summary.json"), encoding="utf-8"))
        png = base64.b64encode(open(os.path.join(d, "aspects.png"), "rb").read()).decode()
        reports.append({"name": name, "html": product_report.render_html(rep), "img": "data:image/png;base64," + png})
    return {"examples": examples, "reports": reports}


PAGE_CSS = """
body { margin: 0; font: 16px/1.6 -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB",
  "Microsoft YaHei", "Noto Sans SC", sans-serif; }
.gradio-container { padding: 0 20px 40px; box-sizing: border-box; }
.od-note { max-width: 760px; margin: 0 auto; background: #F5F5F7; border-radius: 16px; padding: 14px 20px;
  color: #6E6E73; font-size: 14px; text-align: center; }
.od-pills { display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 18px; }
.od-pills button { font: inherit; font-size: 14px; border: 1px solid #DADDE6; background: #fff; color: #1D1D1F;
  border-radius: 999px; padding: 7px 14px; cursor: pointer; }
.od-pills button.on { background: #3B5BDB; border-color: #3B5BDB; color: #fff; }
.od-two { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.od-col h3 { font-size: 17px; margin: 0 0 12px; }
.od-col.rl-lora { padding: 14px 16px !important; }
.od-hint { color: #6E6E73; font-size: 14px; margin: 0 0 10px; }
.od-report img { max-width: 560px; width: 100%; display: block; margin: 18px auto 0; }
details.od-aspects { margin-top: 22px; font-size: 14px; }
details.od-aspects table { border-collapse: collapse; width: 100%; margin-top: 8px; }
details.od-aspects td, details.od-aspects th { text-align: left; padding: 4px 8px; border-top: 1px solid #E3E5EC; vertical-align: top; }
@media (max-width: 760px) { .od-two { grid-template-columns: 1fr; } }
"""

# 回放：左边扫描 → 左边结果 → 右边扫描 → 右边结果。用时取录到的毫秒数，限制在 0.8–2.2 秒之间（看得清又不拖）；
# 点别的示例时取消上一次还没走完的回放
PAGE_JS = """<script>
(function () {
  var data = JSON.parse(document.getElementById("rl-data").textContent);
  var left = document.getElementById("od-left"), right = document.getElementById("od-right");
  var review = document.getElementById("od-review"), timers = [];
  var clamp = function (ms) { return Math.max(800, Math.min(2200, ms)); };
  function play(i) {
    timers.forEach(clearTimeout); timers = [];
    var ex = data.examples[i];
    document.querySelectorAll("[data-example]").forEach(function (b) { b.classList.toggle("on", +b.dataset.example === i); });
    review.textContent = ex.text;
    left.innerHTML = ex.base_scan; right.innerHTML = ex.wait;
    var t1 = clamp(ex.base_ms), t2 = t1 + clamp(ex.lora_ms);
    timers.push(setTimeout(function () { left.innerHTML = ex.base_html; right.innerHTML = ex.lora_scan; }, t1));
    timers.push(setTimeout(function () { right.innerHTML = ex.lora_html; }, t2));
  }
  function showReport(i) {
    var r = data.reports[i];
    document.querySelectorAll("[data-report]").forEach(function (b) { b.classList.toggle("on", +b.dataset.report === i); });
    document.getElementById("od-report").innerHTML = r.html + '<img alt="Aspects mentioned, by sentiment" src="' + r.img + '">';
  }
  document.querySelectorAll("[data-example]").forEach(function (b) { b.addEventListener("click", function () { play(+b.dataset.example); }); });
  document.querySelectorAll("[data-report]").forEach(function (b) { b.addEventListener("click", function () { showReport(+b.dataset.report); }); });
  showReport(0);
})();
</script>"""


def build_page(data):
    ex_buttons = "".join(f'<button type="button" data-example="{i}" title="{esc(e["text"])}">{esc(e["label"])}</button>'
                         for i, e in enumerate(data["examples"]))
    rep_buttons = "".join(f'<button type="button" data-report="{i}">{esc(r["name"])} · 150 reviews</button>'
                          for i, r in enumerate(data["reports"]))
    aspects = "".join(f"<tr><td>{esc(ASPECT_EN[k])}</td><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in ASPECTS.items())
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")  # 防止数据里的 </ 提前结束 <script>
    intro = intro_html().replace(">Try it live<", ">Try the demo<")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Beyond Star Ratings — offline demo</title>
<style>{CSS}{PAGE_CSS}</style>
{HEAD_JS}
</head>
<body>
<div class="gradio-container">
{intro}
<p class="od-note">Offline version: every result on this page was recorded from the real model (Qwen3-1.7B + our LoRA
adapter, on an Apple M5 with MLX) and is replayed here. You can click the examples, but not type your own review.</p>
{section_head("Try the demo.", "The same 1.7B model answers twice: as-is, and with our LoRA adapter.", "try")}
<div class="rl-window">
  <p class="od-hint">Click an example. The base model answers first, then the fine-tuned one.</p>
  <div class="od-pills">{ex_buttons}</div>
  <div class="rl-review" id="od-review">Pick an example above.</div>
  <div class="od-two">
    <div class="od-col"><h3>Base model (no fine-tuning)</h3><div id="od-left">{waiting_card("Results appear here")}</div></div>
    <div class="od-col rl-lora"><h3>LoRA fine-tuned</h3><div id="od-right">{waiting_card("Results appear here")}</div></div>
  </div>
  <details class="od-aspects"><summary>The 16 aspects the model may choose from</summary>
    <table><tr><th>Aspect</th><th>中文</th><th>Covers</th></tr>{aspects}</table></details>
</div>
{section_head("A whole product, in one report.", "Reports generated by the real model on 150 unseen reviews each.", "report")}
<div class="rl-window">
  <div class="od-pills">{rep_buttons}</div>
  <div id="od-report" class="od-report"></div>
  <p class="od-hint" style="margin-top:16px">The samples come from a dataset that mixes positive and negative reviews
  roughly 50/50 by design, so their positive share is not that of a real product.</p>
</div>
<div class="rl-foot">Han Daiyuan · Li Mingtai · Lingnan University · CDT503<br>Code: {REPO}</div>
</div>
<script type="application/json" id="rl-data">{blob}</script>
{PAGE_JS}
</body>
</html>
"""


def main():
    html = build_page(build_data())
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {OUT}（{len(html) // 1024} KB）")


if __name__ == "__main__":
    main()
