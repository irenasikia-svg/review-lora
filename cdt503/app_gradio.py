"""CDT503 第 3 阶段：Gradio 演示。输入一条中文商品评论，原始模型和 LoRA 微调后的模型并排给出抽取结果。

用法：
  uv run python cdt503/app_gradio.py                       # 本机：http://localhost:7860
  uv run python cdt503/app_gradio.py --share               # 生成公网链接，同学用手机打开
  uv run python cdt503/app_gradio.py --host 0.0.0.0        # 同一 Wi-Fi 下用 http://<本机IP>:7860（--share 用不了时的备用方案）
  uv run python cdt503/app_gradio.py --adapter adapters_best        # 换成别的检查点（默认是调参选出的 lr=5e-5）
  uv run python cdt503/app_gradio.py --mock                # 不加载模型，只看界面（开发用）

设计要点：
  - 内存里只有一份模型。LoRA 层的输出 = 原始输出 + scale × 旁路输出，把 scale 临时设成 0 就是原始模型
  - MLX 的计算流绑定在加载模型的线程上，而 Gradio 在别的线程里处理请求。所以开一个专门的推理线程：
    模型在这个线程里加载、也只在这个线程里推理，网页请求只往队列里放任务、等结果
  - 启动时先预热一次（第一次推理要编译，会慢几秒），预热完才开放网页
  - 一次只处理一个请求（GPU 只有一块），其他人排队；任何异常都变成页面上的提示，不会让程序崩溃
"""
import argparse
import json
import os
import queue
import re
import sys
import threading
import time
from concurrent.futures import Future

import gradio as gr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "cdt503/scripts"))
from aspects_en import ASPECT_EN, en  # noqa: E402
from common import ASPECTS, SENTIMENTS, parse_output  # noqa: E402

STUDENT = "mlx-community/Qwen3-1.7B-bf16"
MAX_CHARS = 300
TIMEOUT_SEC = 90

EXAMPLES = [
    "屏幕很清晰，运行速度也快，电池很耐用，物流第二天就到了",                      # 正面，多个方面
    "收到就是坏的，开不了机，客服一直推脱不给换",                                  # 负面
    "衣服面料不错，穿着很舒服，就是尺码偏小，颜色和图片有色差",                    # 褒贬混合
    "酒店离地铁站很近，早餐种类挺多，但是房间隔音很差，前台办入住等了半小时",      # 酒店，四个方面
    "苹果个头很大，脆甜多汁，就是有两个磕坏了，包装太简陋",                        # 水果：尺寸、口味、故障、包装
    "卡！严重卡！开个微信都要等半天，垃圾！！",                                    # 刁钻：语气激烈但有具体问题
    "还没用，用了再来评价",                                                        # 刁钻：没有任何具体方面
    "好评！用了三天就坏了，质量真是\"好\"啊",                                      # 刁钻：反讽
]


def diagnose(raw: str):
    """输出不合格时，说清楚具体违反了哪条规则。和 scripts/demo_server.py 的逻辑一致。"""
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.S).strip()
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return ["No JSON object found in the output"]
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return ["Invalid JSON syntax (the output may have been cut off)"]
    problems = []
    if obj.get("整体情感") not in SENTIMENTS:
        problems.append(f"Overall sentiment “{obj.get('整体情感')}” is not 正面/负面")
    for a in obj.get("方面", []) if isinstance(obj.get("方面"), list) else []:
        if isinstance(a, dict):
            if a.get("方面") not in ASPECTS:
                problems.append(f"Aspect “{a.get('方面')}” is not in the allowed list")
            if a.get("情感") not in SENTIMENTS:
                problems.append(f"Sentiment “{a.get('情感')}” is not 正面/负面")
    return problems or ["Missing fields or wrong types"]


class Engine:
    """专门的推理线程。所有 MLX 调用都在这个线程里发生。"""

    def __init__(self, adapter, mock=False):
        self.adapter, self.mock = adapter, mock
        self.jobs = queue.Queue()
        self.ready = threading.Event()
        self.error = None
        threading.Thread(target=self._loop, daemon=True).start()

    def _load(self):
        from mlx_lm import generate
        from mlx_lm.tuner.lora import LoRALinear

        from gen import encode, load_model

        self.model, self.tok = load_model(STUDENT, adapter_path=self.adapter)
        self.layers = [m for _, m in self.model.named_modules() if isinstance(m, LoRALinear)]
        self.scales = [m.scale for m in self.layers]
        if not self.layers:
            raise RuntimeError(f"No LoRA layers found in {self.adapter}")
        self._generate = lambda text: generate(self.model, self.tok, encode(self.tok, text), max_tokens=256)
        print(f"已加载 {STUDENT} + {self.adapter}（{len(self.layers)} 个 LoRA 层）", flush=True)

    def _run(self, text, lora):
        if self.mock:
            return mock_output(text, lora)
        for m, s in zip(self.layers, self.scales):
            m.scale = s if lora else 0.0
        return self._generate(text)

    def _loop(self):
        try:
            if not self.mock:
                self._load()
                t = time.time()
                for lora in (False, True):  # 预热：两种模式各跑一次
                    self._run(EXAMPLES[0], lora)
                print(f"预热完成（{time.time() - t:.1f} 秒）", flush=True)
        except Exception as e:  # noqa: BLE001
            self.error = e
        self.ready.set()
        while True:
            text, fut = self.jobs.get()
            try:
                out = {}
                for key, lora in (("base", False), ("lora", True)):
                    start = time.time()
                    raw = self._run(text, lora)
                    out[key] = {"raw": raw, "ms": int((time.time() - start) * 1000)}
                fut.set_result(out)
            except Exception as e:  # noqa: BLE001
                fut.set_exception(e)

    def submit(self, text):
        fut = Future()
        self.jobs.put((text, fut))
        return fut


def mock_output(text, lora):
    """--mock：不加载模型，造一个假结果，只用来检查界面布局。"""
    time.sleep(0.3)
    if not lora:
        return '{"整体情感": "中性", "方面": [{"方面": "舒适度", "观点": "很舒服", "情感": "正面"}]}'
    aspects = []
    for kw, asp, senti in [("屏幕", "使用效果", "正面"), ("坏", "故障瑕疵", "负面"), ("客服", "服务", "负面"),
                           ("物流", "物流", "正面"), ("尺码", "尺寸重量", "负面"), ("隔音", "房间设施", "负面")]:
        if kw in text:
            i = text.index(kw)
            aspects.append({"方面": asp, "观点": text[i:i + 6], "情感": senti})
    return json.dumps({"整体情感": "负面" if "坏" in text or "差" in text else "正面", "方面": aspects}, ensure_ascii=False)


# —— 渲染 ——
def highlight(text, parsed):
    """把抽到的"观点"在原文里标出来，交给 gr.HighlightedText。观点不是原文片段时就不标。"""
    if not parsed:
        return [(text, None)]
    spans = []
    for a in parsed["方面"]:
        op = a["观点"]
        i = text.find(op) if op else -1
        if i < 0 or any(i < e and i + len(op) > s for s, e, _ in spans):
            continue
        spans.append((i, i + len(op), f"{en(a['方面'])} {'+' if a['情感'] == '正面' else '−'}"))
    out, pos = [], 0
    for s, e, label in sorted(spans):
        if s > pos:
            out.append((text[pos:s], None))
        out.append((text[s:e], label))
        pos = e
    if pos < len(text):
        out.append((text[pos:], None))
    return out


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card(result):
    raw, ms = result["raw"], result["ms"]
    parsed = parse_output(raw)
    html = ['<div class="rl-card">']
    if parsed:
        senti = "pos" if parsed["整体情感"] == "正面" else "neg"
        html.append(f'<div class="rl-row"><span class="rl-badge ok">✓ Valid JSON</span>'
                    f'<span class="rl-badge {senti}">Overall: {"positive" if senti == "pos" else "negative"}</span>'
                    f'<span class="rl-ms">{ms / 1000:.2f} s</span></div>')
        if parsed["方面"]:
            html.append('<table class="rl-table"><tr><th>Aspect</th><th>Opinion</th><th></th></tr>')
            for a in parsed["方面"]:
                s = "pos" if a["情感"] == "正面" else "neg"
                html.append(f'<tr><td><b>{esc(en(a["方面"]))}</b><br><small>{esc(a["方面"])}</small></td>'
                            f'<td>{esc(a["观点"])}</td><td class="rl-{s}">{"+ positive" if s == "pos" else "− negative"}</td></tr>')
            html.append("</table>")
        else:
            html.append('<p class="rl-muted">No specific aspect mentioned.</p>')
    else:
        html.append(f'<div class="rl-row"><span class="rl-badge bad">✗ Invalid output</span>'
                    f'<span class="rl-ms">{ms / 1000:.2f} s</span></div>')
        html.append('<div class="rl-problems">A program cannot use this output:<ul>'
                    + "".join(f"<li>{esc(p)}</li>" for p in diagnose(raw)) + "</ul></div>")
    html.append(f'<details><summary>Raw model output</summary><pre>{esc(raw)}</pre></details></div>')
    return "".join(html), parsed


CSS = """
.rl-card { font-size: 15px; }
.rl-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }
.rl-badge { font-size: 13px; font-weight: 600; border-radius: 6px; padding: 2px 9px; }
.rl-badge.ok, .rl-badge.pos { background: #e3f4ea; color: #1f8a4c; }
.rl-badge.neg { background: #fbe7e3; color: #c2412d; }
.rl-badge.bad { background: #fdf0d9; color: #a15c00; }
.rl-ms { margin-left: auto; font-size: 13px; opacity: .7; font-variant-numeric: tabular-nums; }
.rl-table { width: 100%; border-collapse: collapse; }
.rl-table th { text-align: left; font-size: 12px; opacity: .6; font-weight: 500; }
.rl-table td { padding: 6px 4px; border-top: 1px solid rgba(128,128,128,.25); vertical-align: top; }
.rl-pos { color: #1f8a4c; white-space: nowrap; } .rl-neg { color: #c2412d; white-space: nowrap; }
.rl-problems { background: #fdf0d9; color: #a15c00; border-radius: 8px; padding: 8px 12px; font-size: 14px; }
.rl-problems ul { margin: 4px 0 0; }
.rl-muted { opacity: .65; }
.rl-card pre { white-space: pre-wrap; word-break: break-all; font-size: 12px; }
.rl-lora { border: 2px solid #3b5bdb !important; border-radius: 12px; padding: 10px 12px !important; }
"""
COLOR_MAP = {f"{v} +": "#3cb371" for v in ASPECT_EN.values()} | {f"{v} −": "#e8735a" for v in ASPECT_EN.values()}


def build_ui(engine, adapter_label):
    def analyze(text):
        text = (text or "").strip()
        if not text:
            gr.Warning("Please type a review first.")
            return gr.skip(), gr.skip(), gr.skip(), gr.skip()
        if len(text) > MAX_CHARS:
            gr.Info(f"Review truncated to {MAX_CHARS} characters.")
            text = text[:MAX_CHARS]
        if not engine.ready.is_set():
            gr.Warning("The model is still warming up — please try again in a few seconds.")
            return gr.skip(), gr.skip(), gr.skip(), gr.skip()
        if engine.error:
            msg = f'<div class="rl-problems">The model failed to load: {esc(engine.error)}</div>'
            return msg, [(text, None)], msg, [(text, None)]
        try:
            out = engine.submit(text).result(timeout=TIMEOUT_SEC)
        except Exception as e:  # noqa: BLE001
            msg = f'<div class="rl-problems">Something went wrong ({esc(type(e).__name__)}). Please try again.</div>'
            return msg, [(text, None)], msg, [(text, None)]
        base_html, base_p = card(out["base"])
        lora_html, lora_p = card(out["lora"])
        return base_html, highlight(text, base_p), lora_html, highlight(text, lora_p)

    with gr.Blocks(title="Review Aspect Extraction — LoRA demo") as demo:
        gr.Markdown(
            "## Aspect-based sentiment extraction for Chinese product reviews\n"
            "Type a Chinese e-commerce review. The **same Qwen3-1.7B model** answers twice: once as-is, "
            f"and once with a 70 MB **LoRA adapter** fine-tuned on 1.8k reviews labelled by Qwen3-30B. "
            f"<small>Adapter: `{adapter_label}` · runs locally on an Apple M5 with MLX</small>")
        with gr.Row():
            box = gr.Textbox(label="Review (Chinese)", lines=3, max_lines=6, scale=5,
                             placeholder="例如：屏幕很清晰，但电池两天就没电了，客服也不理人")
            with gr.Column(scale=1, min_width=140):
                btn = gr.Button("Analyze", variant="primary")
                gr.ClearButton(box, value="Clear")
        gr.Examples(EXAMPLES, inputs=box, label="Try an example (click to fill in, then Analyze)")
        with gr.Row(equal_height=False):
            with gr.Column():
                gr.Markdown("### Base model (no fine-tuning)")
                base_hl = gr.HighlightedText(label="Opinions found in the review", color_map=COLOR_MAP,
                                             combine_adjacent=False, show_legend=False)
                base_out = gr.HTML()
            with gr.Column(elem_classes="rl-lora"):
                gr.Markdown("### LoRA fine-tuned")
                lora_hl = gr.HighlightedText(label="Opinions found in the review", color_map=COLOR_MAP,
                                             combine_adjacent=False, show_legend=False)
                lora_out = gr.HTML()
        with gr.Accordion("The 16 aspects the model may choose from", open=False):
            gr.Markdown("| Aspect | 中文 | Covers |\n|---|---|---|\n" + "\n".join(
                f"| {ASPECT_EN[k]} | {k} | {v} |" for k, v in ASPECTS.items()))
        gr.Markdown("<small>One request at a time on a single GPU — if many people try at once, you will wait in a "
                    "short queue.</small>")
        btn.click(analyze, box, [base_out, base_hl, lora_out, lora_hl])
        box.submit(analyze, box, [base_out, base_hl, lora_out, lora_hl])
    return demo


def main():
    ap = argparse.ArgumentParser()
    # 默认用第 1 阶段按验证集选出的最优配置（lr=5e-5，第 240 步）
    ap.add_argument("--adapter", default=os.path.join(ROOT, "cdt503/runs/sweep/lr5e-5/best"))
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--share", action="store_true")
    ap.add_argument("--mock", action="store_true", help="不加载模型，只检查界面")
    args = ap.parse_args()

    engine = Engine(args.adapter, mock=args.mock)
    print("加载模型并预热中…" if not args.mock else "模拟模式：不加载模型", flush=True)
    engine.ready.wait()
    if engine.error:
        print(f"模型加载失败：{engine.error}", flush=True)  # 网页仍然打开，并在页面上提示
    demo = build_ui(engine, os.path.relpath(args.adapter, ROOT) if not args.mock else "mock")
    demo.queue(default_concurrency_limit=1, max_size=40)
    demo.launch(server_name=args.host, server_port=args.port, share=args.share, css=CSS,
                theme=gr.themes.Soft(), show_error=True)


if __name__ == "__main__":
    main()
