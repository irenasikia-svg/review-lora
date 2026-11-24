"""离线演示页：录制的真实输出完整、页面自包含、卡片都来自录制。

运行：uv run --with pytest pytest cdt503/tests/test_offline_demo.py -q
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("cdt503", "scripts", "cdt503/scripts"):
    sys.path.insert(0, os.path.join(ROOT, sub))

from app_gradio import EXAMPLES  # noqa: E402
from common import parse_output  # noqa: E402

RECORDED = os.path.join(ROOT, "cdt503/offline_demo/recorded.json")


def _recorded():
    if not os.path.exists(RECORDED):
        pytest.fail("recorded.json missing: run cdt503/scripts/record_offline_demo.py")
    return json.load(open(RECORDED, encoding="utf-8"))["records"]


def test_recorded_outputs_complete():
    rec = _recorded()
    assert [r["text"] for r in rec] == EXAMPLES
    for r in rec:
        for side in ("base", "lora"):
            assert r[side]["raw"].strip() and r[side]["ms"] > 0
        assert parse_output(r["lora"]["raw"]) is not None  # 微调后 8 条都应是合格输出


def _page_data(html):
    """取出页面里内嵌的数据（<script type="application/json" id="rl-data">）。"""
    start = html.index('<script type="application/json" id="rl-data">') + len('<script type="application/json" id="rl-data">')
    return json.loads(html[start:html.index("</script>", start)])


def test_page_is_self_contained():
    from build_offline_demo import build_data, build_page
    html = build_page(build_data())
    for bad in ('src="http', "src='http", "url(http", "@import", "fonts.googleapis", 'rel="stylesheet"'):
        assert bad not in html, bad


def test_page_has_all_examples_and_reports():
    from build_offline_demo import build_data, build_page
    html = build_page(build_data())
    assert html.count("data-example=") == 8 and html.count("data-report=") == 3
    assert "Offline version" in html


def test_cards_come_from_recording():
    from build_offline_demo import build_data, build_page
    from demo_render import result_card
    data = build_data()
    assert _page_data(build_page(data)) == data
    for ex, rec in zip(data["examples"], _recorded()):
        assert ex["base_html"] == result_card(rec["base"], rec["text"])[0]
        assert ex["lora_html"] == result_card(rec["lora"], rec["text"])[0]


def test_demo_box_says_recorded():
    """点开头按钮会直接跳到演示区，所以演示区里也要写明是录制回放。"""
    from build_offline_demo import build_data, build_page
    html = build_page(build_data())
    box = html[html.index('id="try"'):html.index('id="od-review"')]
    assert "Recorded" in box


def test_css_variables_all_defined():
    """离线页没有 Gradio 主题：CSS 里用到的每个 var(--x) 都要在页面自己的样式里定义。"""
    import re
    from build_offline_demo import PAGE_CSS
    from demo_render import CSS
    used = set(re.findall(r"var\((--[\w-]+)", CSS + PAGE_CSS))
    defined = set(re.findall(r"(--[\w-]+)\s*:", CSS + PAGE_CSS))
    defined.add("--i")  # --i 是 review_html 在每个高亮元素的 style 属性里设的
    assert used <= defined, used - defined
