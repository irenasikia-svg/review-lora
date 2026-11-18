"""分步揭晓的测试：推理线程先交原始模型结果、再交 LoRA 结果；排队、出错、超时、中途离开都要正常收尾。

只用 --mock 引擎（不加载模型）。运行：uv run --with pytest pytest cdt503/tests -q
"""
import asyncio
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("cdt503", "scripts", "cdt503/scripts"):
    sys.path.insert(0, os.path.join(ROOT, sub))

from app_gradio import CompareJob, Engine, analyze_steps  # noqa: E402


async def _collect(agen):
    return [step async for step in agen]


def collect(agen):
    return asyncio.run(_collect(agen))


def test_steps_reveal_base_then_lora():
    eng = Engine("unused", mock=True, mock_delay=0.05)
    eng.ready.wait(5)
    steps = collect(analyze_steps(eng, "收到就是坏的，客服不理人", timeout=5))
    assert "rl-scan" in steps[0][0] and "rl-scan" not in steps[0][1]
    assert "rl-scanning" not in steps[-2][0] and "rl-scan" in steps[-2][1]
    assert all("rl-scanning" not in h for h in steps[-1]) and all("rl-card" in h for h in steps[-1])


def test_engine_error_ends_with_problem_cards(monkeypatch):
    eng = Engine("unused", mock=True, mock_delay=0.01)
    eng.ready.wait(5)
    monkeypatch.setattr(eng, "_run", lambda text, lora: (_ for _ in ()).throw(RuntimeError("boom")))
    last = collect(analyze_steps(eng, "测试", timeout=5))[-1]
    assert all("rl-problems" in h for h in last)


def test_timeout_ends_with_problem_cards():
    class Stuck:  # 任务永远不开始，队伍也一直不动
        def submit(self, text):
            return CompareJob(ticket=2)

        def ahead(self, job):
            return 1

        def progress(self):
            return 0

    last = collect(analyze_steps(Stuck(), "测试", timeout=0.5))[-1]
    assert all("rl-problems" in h for h in last)


def test_queue_position_shown_first():
    eng = Engine("unused", mock=True, mock_delay=0.3)
    eng.ready.wait(5)
    first = eng.submit("占位任务")  # 先占住推理线程
    steps = collect(analyze_steps(eng, "第二个请求", timeout=5))
    assert "ahead of you" in steps[0][0]
    first.lora.result(5)


def test_closed_request_never_reaches_the_model(monkeypatch):
    eng = Engine("unused", mock=True, mock_delay=0.2)
    eng.ready.wait(5)
    calls, orig = [], eng._run
    monkeypatch.setattr(eng, "_run", lambda t, lora: (calls.append(t), orig(t, lora))[1])
    blocker = eng.submit("占位任务")

    async def leave():  # 看到排队提示后就关掉了页面
        g = analyze_steps(eng, "我会离开", timeout=5)
        await g.__anext__()
        await g.aclose()

    asyncio.run(leave())
    blocker.lora.result(5)
    deadline = time.monotonic() + 5
    while eng.progress() < 2 and time.monotonic() < deadline:
        time.sleep(0.02)
    assert eng.progress() == 2 and "我会离开" not in calls


def test_waiting_in_a_moving_line_is_not_a_timeout():
    eng = Engine("unused", mock=True, mock_delay=0.25)
    eng.ready.wait(5)
    for _ in range(2):
        eng.submit("排在前面")  # 前面两个任务共约 1 秒，比超时长，但队伍一直在动
    last = collect(analyze_steps(eng, "我的请求", timeout=0.7))[-1]
    assert all("rl-done" in h for h in last)


def test_many_requests_wait_together_in_one_event_loop():
    eng = Engine("unused", mock=True, mock_delay=0.02)
    eng.ready.wait(5)

    async def everyone():
        return await asyncio.gather(*[_collect(analyze_steps(eng, f"请求{i}", timeout=10)) for i in range(20)])

    results = asyncio.run(everyone())
    assert all(all("rl-done" in h for h in steps[-1]) for steps in results)
    assert sum("ahead of you" in steps[0][0] for steps in results) >= 15
