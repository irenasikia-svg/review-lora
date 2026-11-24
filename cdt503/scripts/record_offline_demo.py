"""给离线演示页录制真实输出：用演示页同一个检查点，对 8 个内置示例各跑一次原始模型和 LoRA。

结果原样存进 cdt503/offline_demo/recorded.json（原始输出 + 用时），离线页只回放这些记录，不编造、不手改。
要占 GPU，运行前关掉演示页和其他模型程序：
  uv run python cdt503/scripts/record_offline_demo.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("cdt503", "scripts", "cdt503/scripts"):
    sys.path.insert(0, os.path.join(ROOT, sub))

from app_gradio import EXAMPLES, Engine  # noqa: E402

ADAPTER = os.path.join(ROOT, "cdt503/runs/sweep/lr5e-5/best")
OUT = os.path.join(ROOT, "cdt503/offline_demo/recorded.json")


def main():
    engine = Engine(ADAPTER)  # 真实模型：加载并预热（模型调用都在它自己的推理线程里）
    engine.ready.wait()
    if engine.error:
        raise SystemExit(f"模型加载失败：{engine.error}")
    records = []
    for i, text in enumerate(EXAMPLES, 1):
        job = engine.submit(text)
        base, lora = job.base.result(timeout=180), job.lora.result(timeout=180)
        records.append({"text": text, "base": base, "lora": lora})
        print(f"{i}/{len(EXAMPLES)}  原始 {base['ms']} ms，LoRA {lora['ms']} ms", flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"adapter": os.path.relpath(ADAPTER, ROOT), "records": records}, f, ensure_ascii=False, indent=2)
    print("已保存", OUT)


if __name__ == "__main__":
    main()
