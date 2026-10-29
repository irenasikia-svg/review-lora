"""演示压力测试：模拟全班同时点 Analyze，确认排队正常、不崩溃，并记录每个人要等多久。

先启动演示（uv run python cdt503/app_gradio.py），再运行：
  uv run python cdt503/scripts/stress_test_demo.py --n 12
另外测两种异常输入：空字符串、超过 300 字的长文本，期望页面给提示而不是报错。
"""
import argparse
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from gradio_client import Client

sys.path.insert(0, __file__.rsplit("/scripts/", 1)[0])
from app_gradio import EXAMPLES  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:7860/")
    ap.add_argument("--n", type=int, default=12, help="同时发出的请求数")
    args = ap.parse_args()

    def one(i):
        client = Client(args.url, verbose=False)  # 每个"同学"一个独立连接
        start = time.time()
        try:
            out = client.predict(EXAMPLES[i % len(EXAMPLES)], api_name="/analyze")
            ok = "rl-card" in out[2]  # LoRA 一栏正常出了结果卡片
            return i, time.time() - start, "ok" if ok else "unexpected output"
        except Exception as e:  # noqa: BLE001
            return i, time.time() - start, f"error: {e}"

    print(f"同时发出 {args.n} 个请求…")
    t0 = time.time()
    with ThreadPoolExecutor(args.n) as pool:
        results = sorted(pool.map(one, range(args.n)), key=lambda r: r[1])
    for i, sec, status in results:
        print(f"  请求 {i:2d}: {sec:5.1f} 秒  {status}")
    waits = [r[1] for r in results]
    ok = sum(r[2] == "ok" for r in results)
    print(f"成功 {ok}/{args.n}；最快 {min(waits):.1f} 秒，中位数 {statistics.median(waits):.1f} 秒，"
          f"最慢 {max(waits):.1f} 秒；总耗时 {time.time() - t0:.1f} 秒")

    client = Client(args.url, verbose=False)
    for label, text in [("空输入", ""), ("超长输入（500 字）", "屏幕很清晰，" * 100)]:
        try:
            out = client.predict(text, api_name="/analyze")
            print(f"{label}：正常返回（{'有结果' if out and 'rl-card' in str(out[2]) else '无结果，页面会显示提示'}）")
        except Exception as e:  # noqa: BLE001
            print(f"{label}：报错 {e}")


if __name__ == "__main__":
    main()
