"""demo_render 的单元测试：只测拼出来的 HTML，不加载模型。

运行：uv run --with pytest pytest cdt503/tests -q
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("cdt503", "scripts", "cdt503/scripts"):
    sys.path.insert(0, os.path.join(ROOT, sub))

from demo_render import (CSS, opinion_spans, problem_card, queue_card, result_card,  # noqa: E402
                         review_html, scanning_card)

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
