"""演示页的 HTML 渲染：结果卡片、原文高亮、扫描动画、排队提示。

全是纯函数，只拼字符串，不依赖 gradio 和 MLX，所以可以单独测试（cdt503/tests/test_demo_render.py）。
页面上的文字用英文；颜色：好评绿、差评红、强调色蓝（和 LoRA 一栏的蓝框一致）。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "cdt503/scripts"))
from aspects_en import en  # noqa: E402
from common import ASPECTS, SENTIMENTS, parse_output  # noqa: E402


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def diagnose(raw: str):
    """输出不合格时，说清楚具体违反了哪条规则。和 scripts/demo_server.py 的逻辑一致。"""
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.S).strip()
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return ["No JSON object found in the output"]
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return ["Invalid JSON syntax (the output may have been cut off)"]
    problems = []
    if obj.get("整体情感") not in SENTIMENTS:
        problems.append(f"Overall sentiment “{obj.get('整体情感')}” is not 正面/负面")
    for a in obj.get("方面", []) if isinstance(obj.get("方面"), list) else []:
        if isinstance(a, dict):
            if a.get("方面") not in ASPECTS:
                problems.append(f"Aspect “{a.get('方面')}” is not in the allowed list")
            if a.get("情感") not in SENTIMENTS:
                problems.append(f"Sentiment “{a.get('情感')}” is not 正面/负面")
    return problems or ["Missing fields or wrong types"]


def opinion_spans(text, parsed):
    """模型给的"观点"在原文里的位置：[(起点, 终点, 方面英文名, "pos"/"neg")]，按起点排序。
    观点为空、不是原文片段、或和已经选中的片段重叠的，都跳过。"""
    if not parsed:
        return []
    spans = []
    for a in parsed["方面"]:
        op = a["观点"]
        i = text.find(op) if op else -1
        if i < 0 or any(i < e and i + len(op) > s for s, e, _, _ in spans):
            continue
        spans.append((i, i + len(op), en(a["方面"]), "pos" if a["情感"] == "正面" else "neg"))
    return sorted(spans)


def review_html(text, parsed):
    """原文，观点用 <mark> 标出，后面跟一个小标签（方面 +/−）。--i 让高亮依次亮起。"""
    out, pos = ['<div class="rl-review">'], 0
    for k, (s, e, aspect, senti) in enumerate(opinion_spans(text, parsed)):
        out.append(esc(text[pos:s]))
        sign = "+" if senti == "pos" else "−"
        out.append(f'<mark class="{senti}" style="--i:{k}">{esc(text[s:e])}</mark>'
                   f'<small class="rl-tag {senti}" style="--i:{k}">{esc(aspect)} {sign}</small>')
        pos = e
    out.append(esc(text[pos:]) + "</div>")
    return "".join(out)


def result_card(result, text):
    """一个模型的结果卡片。result = {"raw": 原始输出, "ms": 用时毫秒}。返回 (HTML, 解析结果或 None)。"""
    raw, ms = result["raw"], result["ms"]
    parsed = parse_output(raw)
    h = ['<div class="rl-card rl-done">']
    if parsed:
        senti = "pos" if parsed["整体情感"] == "正面" else "neg"
        h.append(f'<div class="rl-row"><span class="rl-badge ok">✓ Valid JSON</span>'
                 f'<span class="rl-badge {senti}">Overall: {"positive" if senti == "pos" else "negative"}</span>'
                 f'<span class="rl-ms">{ms / 1000:.2f} s</span></div>')
        h.append(review_html(text, parsed))
        if parsed["方面"]:
            h.append('<table class="rl-table"><tr><th>Aspect</th><th>Opinion</th><th></th></tr>')
            for a in parsed["方面"]:
                s = "pos" if a["情感"] == "正面" else "neg"
                h.append(f'<tr><td><b>{esc(en(a["方面"]))}</b><br><small>{esc(a["方面"])}</small></td>'
                         f'<td>{esc(a["观点"])}</td>'
                         f'<td class="rl-{s}">{"+ positive" if s == "pos" else "− negative"}</td></tr>')
            h.append("</table>")
        else:
            h.append('<p class="rl-muted">No specific aspect mentioned.</p>')
    else:
        h.append(f'<div class="rl-row"><span class="rl-badge bad">✗ Invalid output</span>'
                 f'<span class="rl-ms">{ms / 1000:.2f} s</span></div>')
        h.append(review_html(text, None))
        h.append('<div class="rl-problems">A program cannot use this output:<ul>'
                 + "".join(f"<li>{esc(p)}</li>" for p in diagnose(raw)) + "</ul></div>")
    h.append(f'<details><summary>Raw model output</summary><pre>{esc(raw)}</pre></details></div>')
    return "".join(h), parsed


def scanning_card(text, who):
    """模型正在读：原文上有一道光带扫过，下面是两条闪动的占位条。"""
    return (f'<div class="rl-card rl-scanning"><div class="rl-status"><span class="rl-dot"></span>'
            f'{esc(who)} is reading…</div>'
            f'<div class="rl-review rl-scan">{esc(text)}</div>'
            '<div class="rl-skel"><span></span><span></span></div></div>')


def waiting_card(msg):
    """还没轮到这一栏：灰色虚线框。"""
    return f'<div class="rl-card rl-waiting">{esc(msg)}</div>'


def queue_card(ahead):
    word = "request" if ahead == 1 else "requests"
    return (f'<div class="rl-card rl-waiting"><div class="rl-status"><span class="rl-dot"></span>'
            f'Waiting in line — {ahead} {word} ahead of you</div></div>')


def problem_card(msg):
    return f'<div class="rl-card"><div class="rl-problems">{esc(msg)}</div></div>'


CSS = """
.rl-card { font-size: 15px; line-height: 1.6; }
.rl-done { animation: rl-in .35s ease-out; }
.rl-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }
.rl-badge { font-size: 13px; font-weight: 600; border-radius: 6px; padding: 2px 9px; }
.rl-badge.ok, .rl-badge.pos { background: rgba(31,138,76,.12); color: #1f8a4c; }
.rl-badge.neg { background: rgba(194,65,45,.12); color: #c2412d; }
.rl-badge.bad { background: rgba(214,130,0,.14); color: #a15c00; }
.rl-ms { margin-left: auto; font-size: 13px; opacity: .65; font-variant-numeric: tabular-nums; }
.rl-review { font-size: 16px; line-height: 2; padding: 10px 12px; margin-bottom: 10px; border-radius: 10px;
  background: rgba(59,91,219,.06); }
.rl-review mark { color: inherit; border-radius: 4px; padding: 1px 2px;
  animation: rl-mark .5s ease-out both; animation-delay: calc(var(--i) * 140ms + 150ms); }
.rl-review mark.pos { background: rgba(31,138,76,.20); }
.rl-review mark.neg { background: rgba(194,65,45,.20); }
.rl-tag { font-size: 11px; font-weight: 600; margin: 0 4px 0 2px; white-space: nowrap;
  animation: rl-in .4s ease-out both; animation-delay: calc(var(--i) * 140ms + 300ms); }
.rl-tag.pos { color: #1f8a4c; } .rl-tag.neg { color: #c2412d; }
.rl-table { width: 100%; border-collapse: collapse; }
/* 盖掉 Gradio 给 HTML 表格加的深色全边框，只留行间细线 */
.rl-table, .rl-table tr, .rl-table th, .rl-table td, .pr-table, .pr-table tr, .pr-table th, .pr-table td {
  border: none !important; background: none !important; }
.rl-table th { text-align: left; font-size: 12px; opacity: .6; font-weight: 500; padding: 0 4px 4px; }
.rl-table td { padding: 6px 4px; border-top: 1px solid var(--border-color-primary) !important; vertical-align: top; }
.rl-pos { color: #1f8a4c; white-space: nowrap; } .rl-neg { color: #c2412d; white-space: nowrap; }
.rl-problems { background: rgba(214,130,0,.12); color: #a15c00; border-radius: 8px; padding: 8px 12px; font-size: 14px; }
.rl-problems ul { margin: 4px 0 0; }
.rl-muted { opacity: .65; }
.rl-card pre { white-space: pre-wrap; word-break: break-all; font-size: 12px; }
.rl-card details summary { cursor: pointer; font-size: 13px; opacity: .7; }
.rl-lora { border: 2px solid #3b5bdb !important; border-radius: 12px; padding: 10px 12px !important; }

/* 等待和扫描 */
.rl-waiting { border: 1.5px dashed var(--border-color-primary); border-radius: 10px; padding: 18px 14px;
  color: var(--body-text-color-subdued); font-size: 14px; text-align: center; }
.rl-status { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; color: #3b5bdb;
  margin-bottom: 10px; justify-content: inherit; }
.rl-waiting .rl-status { color: var(--body-text-color-subdued); justify-content: center; margin: 0; }
.rl-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; animation: rl-pulse 1s ease-in-out infinite; }
.rl-scan { position: relative; overflow: hidden; color: var(--body-text-color-subdued); }
.rl-scan::after { content: ""; position: absolute; inset: 0; transform: translateX(-100%);
  background: linear-gradient(100deg, transparent 25%, rgba(59,91,219,.28) 50%, transparent 75%);
  animation: rl-sweep 1.3s ease-in-out infinite; }
.rl-skel span { display: block; height: 12px; border-radius: 6px; margin: 8px 0; background: rgba(128,128,128,.18);
  animation: rl-pulse 1.2s ease-in-out infinite; }
.rl-skel span:first-child { width: 70%; } .rl-skel span:last-child { width: 45%; }

@keyframes rl-sweep { to { transform: translateX(100%); } }
@keyframes rl-pulse { 50% { opacity: .35; } }
@keyframes rl-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
@keyframes rl-mark { from { background-color: transparent; } }
@media (prefers-reduced-motion: reduce) {
  .rl-done, .rl-review mark, .rl-tag, .rl-dot, .rl-skel span { animation: none !important; }
  .rl-scan::after { animation: none !important; transform: none; opacity: .5; }
}

/* 商品报告页（product_report.render_html） */
.pr-card { font-size: 15px; }
.pr-card .pos { color: #1f8a4c; } .pr-card .neg { color: #c2412d; }
.pr-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 10px; }
.pr-kpis div { border: 1px solid var(--border-color-primary); border-radius: 10px; padding: 8px 12px; }
.pr-kpis b { display: block; font-size: 26px; line-height: 1.2; font-variant-numeric: tabular-nums; }
.pr-kpis span { font-size: 12px; opacity: .7; }
.pr-bar { display: flex; height: 10px; border-radius: 5px; overflow: hidden; margin: 4px 0 14px; }
.pr-bar .pos { background: #3cb371; } .pr-bar .neg { background: #e8735a; }
.pr-chip { display: inline-block; border-radius: 999px; padding: 1px 10px; margin: 0 4px 4px 0; font-size: 14px; }
.pr-chip.pos { background: rgba(31,138,76,.12); } .pr-chip.neg { background: rgba(194,65,45,.12); }
.pr-table { width: 100%; border-collapse: collapse; margin-top: 8px; }
.pr-table th { text-align: left; font-size: 12px; opacity: .6; font-weight: 500; }
.pr-table td { padding: 6px 4px; border-top: 1px solid var(--border-color-primary) !important; vertical-align: top; }
.pr-muted { opacity: .65; font-size: 13px; }
"""


# —— 风格 B：介绍区（开头 / How it works / Results）和各段标题 ——
_ICON = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round">{d}</svg>')
_ICONS = {
    "tag": _ICON.format(c="#C98516", d='<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/>'
                                       '<circle cx="7.5" cy="7.5" r="1.5"/>'),
    "spark": _ICON.format(c="#3B5BDB", d='<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>'
                                         '<path d="M19 17v4M17 19h4"/>'),
    "check": _ICON.format(c="#2E9E6A", d='<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>'),
}


def intro_html():
    """页面开头的三段介绍。数字来自报告；没有脚本时也是完整可读的静态页面。"""
    features = [
        ("tag", "rgba(242,169,59,.16)", "Teacher labels", "Qwen3-30B labels 2,425 real reviews with 16 fixed aspects."),
        ("spark", "rgba(59,91,219,.12)", "Student learns", "LoRA trains 1% of Qwen3-1.7B: a 70 MB file, 94 minutes."),
        ("check", "rgba(46,158,106,.14)", "Honestly tested", "Tuned on validation only, then checked against our own labels."),
    ]
    cards = "".join(f'<div class="rl-feature reveal"><div class="ic" style="background:{bg}">{_ICONS[ic]}</div>'
                    f'<h3>{esc(h)}</h3><p>{esc(p)}</p></div>' for ic, bg, h, p in features)
    kpis = ('<div class="rl-kpi reveal"><div class="big" data-count="0.80">0.80</div>'
            '<p>aspect-F1 on the test set<br>base model: 0.51</p></div>'
            '<div class="rl-kpi reveal"><div class="big">≈</div><p>the 30B teacher,<br>judged against human labels</p></div>'
            '<div class="rl-kpi reveal"><div class="big" data-count="5" data-suffix="×">5×</div>'
            '<p>less memory<br>than the teacher</p></div>')
    return (
        '<section class="rl-hero reveal">'
        '<div class="rl-eyebrow">CDT503 · Track B: NLP / PEFT</div>'
        '<h1>Beyond Star Ratings.</h1>'
        '<p class="rl-sub">Stars say whether customers are happy. Our 1.7B model tells you why.</p>'
        '<div class="rl-cta"><a class="pri" href="#try">Try it live</a><a class="sec" href="#how">How it works ›</a></div>'
        '<div class="rl-hero-card"><p>酒店<span class="hl pos">离地铁站很近</span>，早餐种类挺多，但是'
        '<span class="hl neg">房间隔音很差</span>，<span class="hl neg">前台办入住等了半小时</span>。</p>'
        '<span class="rl-pill pos">Location +</span><span class="rl-pill neg">Room &amp; facilities −</span>'
        '<span class="rl-pill neg">Service −</span></div>'
        '</section>'
        '<section id="how" class="rl-band">'
        '<h2 class="reveal">How it works.</h2>'
        '<p class="rl-sub reveal">A big model teaches, a small model learns, on one laptop.</p>'
        f'<div class="rl-grid3">{cards}</div>'
        '</section>'
        '<section id="results" class="rl-results">'
        '<h2 class="reveal">Small model. Near-teacher results.</h2>'
        f'<div class="rl-grid3">{kpis}</div>'
        '</section>'
    )


def section_head(title, sub, anchor):
    """演示区、报告区上方的大标题（也是页内跳转的锚点）。"""
    return (f'<div id="{esc(anchor)}" class="rl-section-head reveal"><h2>{esc(title)}</h2>'
            f'<p class="rl-sub">{esc(sub)}</p></div>')


CSS += """
/* ===== 风格 B（参考稿 cdt503/docs/mockups/style-b-product.html） ===== */
body, gradio-app, .gradio-container, .main, .wrap { background: #fff !important; }
/* width:100% 不能省：gradio-app 是纵向 flex，左右 auto 边距会让容器缩成内容宽度，手机上就会横向滚动 */
.gradio-container { max-width: 1120px !important; width: 100% !important; margin: 0 auto !important; color: #1D1D1F; }
button.primary { background: #3B5BDB !important; border-color: #3B5BDB !important; color: #fff !important; }
button.primary:hover { background: #2F4BC0 !important; }
.rl-sub { font-size: 21px; color: #6E6E73; max-width: 640px; margin: 0 auto; line-height: 1.5; }
.rl-hero { text-align: center; padding: 96px 0 72px; }
.rl-eyebrow { font-size: 15px; font-weight: 600; color: #3B5BDB; }
.rl-hero h1 { font-size: 76px; line-height: 1.04; letter-spacing: -.035em; margin: 14px 0 18px; font-weight: 700; }
.rl-cta { margin-top: 32px; display: flex; gap: 14px; justify-content: center; }
.rl-cta a { text-decoration: none !important; font-weight: 600; font-size: 16px; padding: 13px 26px; border-radius: 999px;
  white-space: nowrap; }
.rl-cta .pri { background: #3B5BDB; color: #fff !important; } .rl-cta .sec { color: #3B5BDB !important; }
.rl-hero-card { margin: 56px auto 0; max-width: 760px; background: #fff; border-radius: 28px; padding: 32px 38px; text-align: left;
  box-shadow: 0 30px 60px -30px rgba(0,0,0,.25), 0 0 0 1px rgba(0,0,0,.04); }
.rl-hero-card p { font-size: 25px; margin: 0 0 20px; line-height: 1.7; }
.rl-hero-card .hl { border-radius: 6px; padding: 1px 3px; transition: background-color .6s ease; }
.rl-hero-card .hl.pos { background: rgba(46,158,106,.18); } .rl-hero-card .hl.neg { background: rgba(224,96,63,.18); }
html.js-anim .rl-hero:not(.in) .hl { background: transparent; }
.rl-hero.in .hl:nth-of-type(1) { transition-delay: .5s; } .rl-hero.in .hl:nth-of-type(2) { transition-delay: .85s; }
.rl-hero.in .hl:nth-of-type(3) { transition-delay: 1.2s; }
.rl-pill { display: inline-block; font-size: 14px; font-weight: 600; border-radius: 999px; padding: 5px 14px; margin: 0 8px 6px 0; }
.rl-pill.pos { background: rgba(46,158,106,.12); color: #2E9E6A; } .rl-pill.neg { background: rgba(224,96,63,.12); color: #E0603F; }
.rl-band { background: #F5F5F7; border-radius: 32px; padding: 88px 48px; text-align: center; }
.rl-band h2, .rl-results h2, .rl-section-head h2 { font-size: 44px; line-height: 1.1; letter-spacing: -.025em; margin: 0 0 14px;
  font-weight: 700; text-align: center; }
.rl-grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; margin-top: 48px; text-align: left; }
.rl-feature { background: #fff; border-radius: 24px; padding: 32px; }
.rl-feature .ic { width: 46px; height: 46px; border-radius: 14px; display: grid; place-items: center; margin-bottom: 22px; }
.rl-feature h3 { font-size: 21px; margin: 0 0 6px; } .rl-feature p { margin: 0; color: #6E6E73; font-size: 16px; }
.rl-results { padding: 96px 0 40px; }
.rl-kpi { background: #F5F5F7; border-radius: 24px; padding: 32px; }
.rl-kpi .big { font-size: 64px; font-weight: 700; letter-spacing: -.03em; line-height: 1; margin-bottom: 14px;
  font-variant-numeric: tabular-nums; }
.rl-kpi p { margin: 0; color: #6E6E73; font-size: 16px; }
.rl-section-head { text-align: center; padding: 88px 0 8px; scroll-margin-top: 16px; }
/* "窗口"：演示区和报告区的外框 */
.rl-window { background: #fff !important; border-radius: 26px !important; padding: 46px 30px 28px !important; position: relative;
  box-shadow: 0 30px 70px -35px rgba(0,0,0,.30), 0 0 0 1px rgba(0,0,0,.05) !important; margin-top: 36px; }
.rl-window::before { content: ""; position: absolute; top: 18px; left: 22px; width: 12px; height: 12px; border-radius: 50%;
  background: #E3E3E8; box-shadow: 20px 0 0 #E3E3E8, 40px 0 0 #E3E3E8; }
.rl-window button.primary, .rl-window button.secondary { border-radius: 999px !important; font-weight: 600; }
.rl-window textarea { border-radius: 14px !important; font-size: 17px !important; }
.rl-foot { text-align: center; color: #6E6E73; font-size: 13px; padding: 48px 0 24px; }
/* 出场动画：只有脚本运行（<html> 上有 js-anim）时才先藏起来，脚本出错时内容照常可见 */
.reveal { transition: opacity .7s ease, transform .7s cubic-bezier(.2,.7,.2,1); }
html.js-anim .reveal { opacity: 0; transform: translateY(28px) scale(.985); }
html.js-anim .reveal.in { opacity: 1; transform: none; }
.rl-grid3 > .reveal:nth-child(2) { transition-delay: .12s; } .rl-grid3 > .reveal:nth-child(3) { transition-delay: .24s; }
@media (max-width: 760px) {
  .rl-hero { padding: 56px 0 40px; } .rl-hero h1 { font-size: 46px; }
  .rl-band { padding: 56px 20px; border-radius: 24px; }
  .rl-band h2, .rl-results h2, .rl-section-head h2 { font-size: 32px; }
  .rl-grid3 { grid-template-columns: 1fr; }
  .rl-hero-card { padding: 22px; } .rl-hero-card p { font-size: 20px; }
  .rl-window { padding: 42px 14px 18px !important; }
}
@media (prefers-reduced-motion: reduce) { .reveal, .rl-hero-card .hl { transition: none !important; } }
"""

# 出场动画脚本：通过 launch(head=HEAD_JS) 注入。Gradio 的组件是后渲染的，所以用 MutationObserver 接住新出现的元素；
# 每秒检查一次屏幕内还没出场的元素（兜底，防止卡在隐藏状态）
HEAD_JS = """<script>
(function () {
  // 页面只有浅色版：系统是深色模式、网址里又没指定时，换成 ?__theme=light（Gradio 自带的开关），否则白底上是白字
  try {
    if (!/[?&]__theme=/.test(location.search) && window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches) {
      var u = new URL(location.href);
      u.searchParams.set("__theme", "light");
      location.replace(u.toString());
      return;
    }
  } catch (e) {}
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var root = document.documentElement;
  try {
    var count = function (el) {
      var to = parseFloat(el.dataset.count), suf = el.dataset.suffix || "";
      var dec = (el.dataset.count.split(".")[1] || "").length, t0 = performance.now();
      var tick = function (t) {
        var k = Math.min(1, (t - t0) / 900);
        el.textContent = (to * (1 - Math.pow(1 - k, 3))).toFixed(dec) + suf;
        if (k < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };
    var show = function (el) {
      if (el.classList.contains("in")) return;
      el.classList.add("in");
      el.querySelectorAll("[data-count]").forEach(count);
    };
    var io = ("IntersectionObserver" in window) ? new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { show(e.target); io.unobserve(e.target); } });
    }, { threshold: 0.15 }) : null;
    var watch = function (node) {
      if (!node || !node.querySelectorAll) return;
      var list = Array.prototype.slice.call(node.querySelectorAll(".reveal:not(.in)"));
      if (node.matches && node.matches(".reveal:not(.in)")) list.push(node);
      list.forEach(function (el) {
        if (el.dataset.rlWatched) return;
        el.dataset.rlWatched = "1";
        if (io) io.observe(el); else show(el);
      });
    };
    // Gradio 的组件是后渲染的：用 MutationObserver 接住新出现的元素
    new MutationObserver(function (muts) {
      muts.forEach(function (m) { m.addedNodes.forEach(function (n) { if (n.nodeType === 1) watch(n); }); });
    }).observe(root, { childList: true, subtree: true });
    // 兜底：每秒把已经在屏幕内（或滚过去了）却还没出场的元素显示出来；先排下一次，再干活
    var sweep = function () {
      setTimeout(sweep, 1000);
      document.querySelectorAll(".reveal:not(.in)").forEach(function (el) {
        if (el.getBoundingClientRect().top < window.innerHeight) show(el);
      });
    };
    sweep();
    // 一切就绪后才让待出场的元素先藏起来；之后任何一步出错都撤掉，内容照常显示
    root.classList.add("js-anim");
    watch(document);
  } catch (e) {
    root.classList.remove("js-anim");
  }
})();
</script>"""
