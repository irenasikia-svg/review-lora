"""demo_render 的单元测试：只测拼出来的 HTML，不加载模型。

运行：uv run --with pytest pytest cdt503/tests -q
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("cdt503", "scripts", "cdt503/scripts"):
    sys.path.insert(0, os.path.join(ROOT, sub))

from demo_render import (CSS, HEAD_JS, intro_html, opinion_spans, problem_card, queue_card,  # noqa: E402
                         result_card, review_html, scanning_card, section_head)

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
    # 不能有以 .reveal 开头、无条件隐藏的规则（html.js-anim .reveal 这种带前提的可以）
    assert not re.search(r"(^|\})\s*\.reveal\s*\{[^}]*opacity:\s*0", CSS, flags=re.M)


def test_head_js_has_fallback():
    for s in ("js-anim", "IntersectionObserver", "MutationObserver", "prefers-reduced-motion", "setTimeout"):
        assert s in HEAD_JS


def test_no_external_resources():
    for part in (CSS, HEAD_JS, intro_html()):
        assert "http://" not in part and "https://" not in part
