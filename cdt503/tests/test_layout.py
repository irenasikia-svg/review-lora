"""页面结构：单页滚动（没有标签页）、演示区和报告区各一个"窗口"、/analyze 接口还在（压力测试要用）。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("cdt503", "scripts", "cdt503/scripts"):
    sys.path.insert(0, os.path.join(ROOT, sub))

import gradio as gr  # noqa: E402

from app_gradio import Engine, build_ui  # noqa: E402


def test_page_is_one_scroll_and_keeps_api():
    eng = Engine("unused", mock=True, mock_delay=0.01)
    eng.ready.wait(5)
    demo = build_ui(eng, "mock")
    blocks = list(demo.blocks.values())
    assert not any(isinstance(b, gr.Tab) for b in blocks)
    assert sum("rl-window" in (getattr(b, "elem_classes", None) or []) for b in blocks) == 2
    assert any(getattr(fn, "api_name", None) == "analyze" for fn in demo.fns.values())
