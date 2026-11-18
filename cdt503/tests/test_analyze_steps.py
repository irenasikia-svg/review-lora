"""分步揭晓的测试：推理线程先交原始模型结果、再交 LoRA 结果；排队、出错、超时都要正常收尾。

只用 --mock 引擎（不加载模型）。运行：uv run --with pytest pytest cdt503/tests -q
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("cdt503", "scripts", "cdt503/scripts"):
    sys.path.insert(0, os.path.join(ROOT, sub))

from app_gradio import CompareJob, Engine, analyze_steps  # noqa: E402


def test_steps_reveal_base_then_lora():
    eng = Engine("unused", mock=True, mock_delay=0.05)
    eng.ready.wait(5)
    steps = list(analyze_steps(eng, "收到就是坏的，客服不理人", timeout=5))
    assert "rl-scan" in steps[0][0] and "rl-scan" not in steps[0][1]
    assert "rl-scanning" not in steps[-2][0] and "rl-scan" in steps[-2][1]
    assert all("rl-scanning" not in h for h in steps[-1]) and all("rl-card" in h for h in steps[-1])


def test_engine_error_ends_with_problem_cards(monkeypatch):
    eng = Engine("unused", mock=True, mock_delay=0.01)
    eng.ready.wait(5)
    monkeypatch.setattr(eng, "_run", lambda text, lora: (_ for _ in ()).throw(RuntimeError("boom")))
    last = list(analyze_steps(eng, "测试", timeout=5))[-1]
    assert all("rl-problems" in h for h in last)


def test_timeout_ends_with_problem_cards():
    class Stuck:  # 任务永远不开始
        def submit(self, text):
            return CompareJob(ticket=2)

        def ahead(self, job):
            return 1

    last = list(analyze_steps(Stuck(), "测试", timeout=0.5))[-1]
    assert all("rl-problems" in h for h in last)


def test_queue_position_shown_first():
    eng = Engine("unused", mock=True, mock_delay=0.3)
    eng.ready.wait(5)
    first = eng.submit("占位任务")  # 先占住推理线程
    steps = list(analyze_steps(eng, "第二个请求", timeout=5))
    assert "ahead of you" in steps[0][0]
    first.lora.result(5)
