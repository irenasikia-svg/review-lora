"""商品评论报告：把一批评论的抽取结果汇总成商家能直接看的结论。不加载模型，Gradio 的报告页调用这里。

输入：评论原文列表 + 模型对每条的原始输出（可选：数据集自带的人工好评/差评标签）
输出：
  - 总体：分析了多少条、好评/差评比例、模型输出不合格的条数
  - 每个方面：被提到几次、好评几次、差评几次、好评率，各附几条原文观点
  - 最受好评 / 最常被抱怨的方面
  - 一张条形图、一份逐条结果的 CSV
"""
import csv
import io
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "cdt503/scripts"))
from aspects_en import en  # noqa: E402
from common import parse_output  # noqa: E402

MAX_REVIEWS = 300
MIN_MENTIONS_FOR_RANKING = 3  # 只被提到一两次的方面不进"最受好评/最常被抱怨"，免得一条评论就决定排名


def read_reviews(text_blob="", file_path=None):
    """粘贴的文字（一行一条）或上传的文件（CSV 取 text 列或第一列；TXT 一行一条）。返回 (评论, 标签或 None)。"""
    rows = []
    if file_path:
        raw = open(file_path, encoding="utf-8-sig", errors="replace").read()
        if file_path.lower().endswith(".csv"):
            reader = csv.DictReader(io.StringIO(raw))
            col = "text" if reader.fieldnames and "text" in reader.fieldnames else (reader.fieldnames or [None])[0]
            for r in reader:
                label = r.get("label")
                rows.append((r.get(col) or "", int(label) if label in ("0", "1") else None))
        else:
            rows += [(line, None) for line in raw.splitlines()]
    rows += [(line, None) for line in (text_blob or "").splitlines()]
    rows = [(t.strip(), lab) for t, lab in rows if t and t.strip()]
    return rows


def build_report(texts, raws, labels=None):
    parsed = [parse_output(r) for r in raws]
    labels = labels or [None] * len(texts)
    valid = [(t, p, lab) for t, p, lab in zip(texts, parsed, labels) if p]
    pos = sum(p["整体情感"] == "正面" for _, p, _ in valid)
    stats = defaultdict(lambda: {"pos": 0, "neg": 0, "pos_examples": [], "neg_examples": []})
    for text, p, _ in valid:
        for a in p["方面"]:
            s = stats[a["方面"]]
            key = "pos" if a["情感"] == "正面" else "neg"
            s[key] += 1
            s[f"{key}_examples"].append((len(text), a["观点"], text))
    aspects = []
    for name, s in stats.items():
        n = s["pos"] + s["neg"]
        aspects.append({
            "aspect": name, "aspect_en": en(name), "mentions": n, "pos": s["pos"], "neg": s["neg"],
            "pos_rate": s["pos"] / n,
            # 例子挑原文最短的：现场一眼能读完
            "pos_examples": [(o, t) for _, o, t in sorted(s["pos_examples"])[:2]],
            "neg_examples": [(o, t) for _, o, t in sorted(s["neg_examples"])[:2]],
        })
    aspects.sort(key=lambda a: -a["mentions"])
    ranked = [a for a in aspects if a["mentions"] >= MIN_MENTIONS_FOR_RANKING]
    with_labels = [(p, lab) for _, p, lab in valid if lab is not None]
    return {
        "n": len(texts), "n_valid": len(valid), "n_invalid": len(texts) - len(valid),
        "pos": pos, "neg": len(valid) - pos, "pos_rate": pos / len(valid) if valid else 0.0,
        "no_aspect": sum(not p["方面"] for _, p, _ in valid),
        "aspects": aspects,
        # 一次好评都没有的方面不能算"最受好评"（反之亦然）
        "top_praised": sorted([a for a in ranked if a["pos"]], key=lambda a: (-a["pos"], -a["pos_rate"]))[:3],
        "top_complaints": sorted([a for a in ranked if a["neg"]], key=lambda a: (-a["neg"], a["pos_rate"]))[:3],
        # 有人工星级标签时（内置样例）：模型判断的整体好坏和人工标签一致的比例
        "label_agreement": (sum((p["整体情感"] == "正面") == (lab == 1) for p, lab in with_labels) / len(with_labels)
                            if with_labels else None),
        "label_pos_rate": (sum(lab == 1 for _, lab in with_labels) / len(with_labels) if with_labels else None),
        "parsed": parsed,
    }


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_html(rep):
    if rep["n_valid"] == 0:
        return '<div class="rl-problems">No usable model output — nothing to report.</div>'
    pct = round(100 * rep["pos_rate"])
    h = ['<div class="pr-card">']
    h.append(f'<div class="pr-kpis"><div><b>{rep["n"]}</b><span>reviews analysed</span></div>'
             f'<div><b class="pos">{pct}%</b><span>positive overall</span></div>'
             f'<div><b class="neg">{100 - pct}%</b><span>negative overall</span></div>'
             f'<div><b>{rep["n_invalid"]}</b><span>unusable outputs</span></div></div>')
    h.append(f'<div class="pr-bar"><div class="pos" style="width:{pct}%"></div>'
             f'<div class="neg" style="width:{100 - pct}%"></div></div>')

    def chips(items, kind):
        if not items:
            return '<span class="pr-muted">— (no aspect with at least 3 mentions)</span>'
        return "".join(f'<span class="pr-chip {kind}">{_esc(a["aspect_en"])} '
                       f'<small>{a[kind]}×</small></span>' for a in items)
    h.append(f'<p><b>Most praised:</b> {chips(rep["top_praised"], "pos")}</p>')
    h.append(f'<p><b>Most criticised:</b> {chips(rep["top_complaints"], "neg")}</p>')
    if rep["label_agreement"] is not None:
        h.append(f'<p class="pr-muted">Check against the reviews\' own star ratings: '
                 f'{round(100 * rep["label_pos_rate"])}% were rated positive; the model\'s overall verdict '
                 f'agrees on {round(100 * rep["label_agreement"])}% of reviews.</p>')
    h.append('<table class="pr-table"><tr><th>Aspect</th><th>Mentions</th><th>+ / −</th>'
             '<th>Example opinions</th></tr>')
    for a in rep["aspects"][:10]:
        ex = [f'<span class="pos">+ {_esc(o)}</span>' for o, _ in a["pos_examples"][:1]]
        ex += [f'<span class="neg">− {_esc(o)}</span>' for o, _ in a["neg_examples"][:1]]
        h.append(f'<tr><td><b>{_esc(a["aspect_en"])}</b><br><small>{_esc(a["aspect"])}</small></td>'
                 f'<td>{a["mentions"]}</td><td><span class="pos">{a["pos"]}</span> / '
                 f'<span class="neg">{a["neg"]}</span></td><td>{"<br>".join(ex)}</td></tr>')
    h.append("</table>")
    if rep["no_aspect"]:
        h.append(f'<p class="pr-muted">{rep["no_aspect"]} reviews mentioned no specific aspect.</p>')
    h.append("</div>")
    return "".join(h)


def plot(rep, top=10):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    aspects = rep["aspects"][:top][::-1]
    fig, ax = plt.subplots(figsize=(6, 0.38 * max(len(aspects), 3) + 0.8))
    if aspects:
        y = range(len(aspects))
        ax.barh(y, [a["pos"] for a in aspects], color="#3cb371", label="positive")
        ax.barh(y, [a["neg"] for a in aspects], left=[a["pos"] for a in aspects], color="#e8735a", label="negative")
        ax.set_yticks(list(y), [a["aspect_en"] for a in aspects])
        ax.legend(frameon=False, loc="lower right")
    ax.set_xlabel("Mentions")
    ax.set_title("Aspects mentioned, by sentiment")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    return fig


def to_csv(path, texts, rep, labels=None):
    labels = labels or [None] * len(texts)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # 带 BOM，Excel 打开中文不乱码
        w = csv.writer(f)
        w.writerow(["review", "star_label", "valid_output", "overall", "aspects"])
        for t, lab, p in zip(texts, labels, rep["parsed"]):
            asp = "; ".join(f'{en(a["方面"])}{"+" if a["情感"] == "正面" else "-"} ({a["观点"]})' for a in p["方面"]) if p else ""
            w.writerow([t, "" if lab is None else lab, bool(p),
                        ("positive" if p["整体情感"] == "正面" else "negative") if p else "", asp])
    return path
