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
