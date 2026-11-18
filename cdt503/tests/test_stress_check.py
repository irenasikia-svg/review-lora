"""压力测试脚本的成功判定：只有两栏都是真正的结果卡片才算成功，排队/超时/出错卡片都不算。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("cdt503", "scripts", "cdt503/scripts"):
    sys.path.insert(0, os.path.join(ROOT, sub))

from demo_render import problem_card, queue_card, result_card  # noqa: E402
from stress_test_demo import ok_output  # noqa: E402


def test_ok_output_only_counts_real_results():
    good, _ = result_card({"raw": '{"整体情感": "正面", "方面": []}', "ms": 10}, "好")
    invalid, _ = result_card({"raw": '{"整体情感": "中性", "方面": []}', "ms": 10}, "好")  # 不合格也是模型的真实回答
    assert ok_output((good, good)) and ok_output((invalid, good))
    assert not ok_output((problem_card("timed out"), problem_card("timed out")))
    assert not ok_output((good, problem_card("boom")))
    assert not ok_output((queue_card(3), queue_card(3)))
    assert not ok_output(None)
