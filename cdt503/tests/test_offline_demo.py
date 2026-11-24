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
