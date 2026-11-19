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
import asyncio
import json
import os
import queue
import tempfile
import sys
import threading
import time
from concurrent.futures import Future

import gradio as gr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "cdt503/scripts"))
from aspects_en import ASPECT_EN  # noqa: E402
import product_report  # noqa: E402
from common import ASPECTS  # noqa: E402
from demo_render import (CSS, HEAD_JS, esc, intro_html, problem_card, queue_card,  # noqa: E402
                         result_card, scanning_card, section_head, waiting_card)

STUDENT = "mlx-community/Qwen3-1.7B-bf16"
MAX_CHARS = 300
# 商品报告页的内置样例（cdt503/scripts/make_report_samples.py 生成，全是没用过的评论）
SAMPLES = {name: os.path.join(ROOT, f"cdt503/demo/samples/{key}.csv")
           for name, key in [("Hotel", "hotel"), ("Tablet", "tablet"), ("Fruit", "fruit")]}
TIMEOUT_SEC = 90
# 中英文都用系统字体：风格一致，也不依赖外网（Soft 主题默认的 Montserrat 要从 Google 下载）
FONT = ["-apple-system", "BlinkMacSystemFont", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
        "Noto Sans SC", "sans-serif"]
FONT_MONO = ["ui-monospace", "SF Mono", "Menlo", "monospace"]

# 按演示顺序排。实测（lr=5e-5）时原始模型在 1、2、3、4、6 上输出不合格，现场对比最直观。
# 1–3 是真实评论，来自第 2 阶段人工标注的 100 条
EXAMPLES = [
    "果子特别棒没有伤比超市便宜又好吃?直的够买",                                            # 好评；原始模型编出"味道"
    "乐视会员卡没有收到，想要退货还得退卡，恶心死了，还有那相机真的很垃圾，操作系统不好用",  # 差评；原始模型编出"产品"
    "升级完7.0系统，挺流畅的，就是感觉耗电有点快，亮屏时间大概在六个小时左右，总的来说还可以吧！",  # 褒贬混合；原始模型答"中性"
    "酒店离地铁站很近，早餐种类挺多，但是房间隔音很差，前台办入住等了半小时",              # 酒店，多个方面；原始模型答"中性"
    "苹果个头很大，脆甜多汁，就是有两个磕坏了，包装太简陋",                                # 原始模型只找到 1 个方面，微调后 4 个
    "还没用，用了再来评价",                                                                # 刁钻：没有具体方面；原始模型答"中性"
    "收到就是坏的，开不了机，客服一直推脱不给换",                                          # 原始模型漏了"服务"
    "好评！用了三天就坏了，质量真是\"好\"啊",                                              # 刁钻：反讽，两个模型都识别为差评
]


class CompareJob:
    """一条单条对比任务。推理线程依次发三个信号：开始处理 → 原始模型完成 → LoRA 完成，页面据此分步刷新。"""

    def __init__(self, ticket):
        self.ticket = ticket  # 第几个进队的任务（从 1 开始），用来算前面还有几个
        self.started = threading.Event()
        self.base, self.lora = Future(), Future()
        self.cancelled = False  # 页面关了或超时了：还没跑的部分不用再跑

    def cancel(self):
        self.cancelled = True


class Engine:
    """专门的推理线程。所有 MLX 调用都在这个线程里发生。"""

    def __init__(self, adapter, mock=False, mock_delay=1.5):
        self.adapter, self.mock, self.mock_delay = adapter, mock, mock_delay
        self.jobs = queue.Queue()
        self.ready = threading.Event()
        self.error = None
        self._lock = threading.Lock()
        self._issued = 0    # 发出的任务号（单条和批量都算）
        self._finished = 0  # 已经处理完的任务数
        threading.Thread(target=self._loop, daemon=True).start()

    def _load(self):
        from mlx_lm import generate
        from mlx_lm.tuner.lora import LoRALinear

        from gen import encode, extract, load_model

        self.model, self.tok = load_model(STUDENT, adapter_path=self.adapter)
        self.layers = [m for _, m in self.model.named_modules() if isinstance(m, LoRALinear)]
        self.scales = [m.scale for m in self.layers]
        if not self.layers:
            raise RuntimeError(f"No LoRA layers found in {self.adapter}")
        self._generate = lambda text: generate(self.model, self.tok, encode(self.tok, text), max_tokens=256)
        # 商品报告用：一批评论一起生成（批大小 8，和 B4 成本测量一致）
        self._extract = lambda texts: extract(self.model, self.tok, texts, batch_size=8, log_every=10**9)
        print(f"已加载 {STUDENT} + {self.adapter}（{len(self.layers)} 个 LoRA 层）", flush=True)

    def _run(self, text, lora):
        if self.mock:
            return mock_output(text, lora, self.mock_delay)
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
            kind, payload, target = self.jobs.get()
            try:
                if kind == "compare":  # 单条评论：原始模型和 LoRA 各生成一次，各自一完成就交出去
                    if target.cancelled:  # 等的人已经走了，不占 GPU
                        continue
                    target.started.set()
                    for fut, lora in ((target.base, False), (target.lora, True)):
                        if target.cancelled:
                            break
                        start = time.time()
                        raw = self._run(payload, lora)
                        fut.set_result({"raw": raw, "ms": int((time.time() - start) * 1000)})
                else:  # "batch"：商品报告，一组评论只用 LoRA 模型
                    if self.mock:
                        target.set_result([mock_output(t, True, 0.02) for t in payload])
                    else:
                        for m, s in zip(self.layers, self.scales):
                            m.scale = s
                        target.set_result(self._extract(payload))
            except Exception as e:  # noqa: BLE001
                for fut in (target.base, target.lora) if kind == "compare" else (target,):
                    if not fut.done():
                        fut.set_exception(e)
            finally:
                with self._lock:
                    self._finished += 1

    def submit(self, text):
        with self._lock:  # 发号和进队在同一把锁里，保证号码顺序就是排队顺序
            self._issued += 1
            job = CompareJob(self._issued)
            self.jobs.put(("compare", text, job))
        return job

    def submit_batch(self, texts):
        fut = Future()
        with self._lock:
            self._issued += 1
            self.jobs.put(("batch", texts, fut))
        return fut

    def ahead(self, job):
        """前面还有几个任务没做完（包括正在做的那个）。"""
        with self._lock:
            return max(0, job.ticket - 1 - self._finished)

    def progress(self):
        """已经处理完的任务数。排队时只要它在涨，就说明队伍在动，不算超时。"""
        with self._lock:
            return self._finished


async def _wait(fut, timeout):
    """在事件循环里等推理线程的 Future，不占线程；shield 防止超时时把推理线程那边的 Future 一起取消。"""
    return await asyncio.wait_for(asyncio.shield(asyncio.wrap_future(fut)), timeout)


async def analyze_steps(engine, text, timeout=TIMEOUT_SEC):
    """单条对比的分步刷新：依次产出 (左卡片 HTML, 右卡片 HTML)。
    排队中 → 原始模型扫描中 → 左边出结果、LoRA 扫描中 → 两边结果。超时或出错时两边显示提示并结束。
    用 async：几十个人同时排队也只是事件循环里的协程，不占 Gradio 的工作线程。"""
    job = engine.submit(text)
    try:
        # 排队时的超时按"队伍多久没动"算：人多时排得久不算超时，推理线程卡住才算
        shown, seen, since = None, engine.progress(), time.monotonic()
        while not job.started.is_set():
            n = engine.ahead(job)
            if n > 0 and n != shown:
                shown = n
                yield queue_card(n), queue_card(n)
            p = engine.progress()
            if p != seen:
                seen, since = p, time.monotonic()
            elif time.monotonic() - since >= timeout:
                msg = problem_card("The demo is busy and your request timed out. Please try again.")
                yield msg, msg
                return
            await asyncio.sleep(0.1)

        yield scanning_card(text, "Base model"), waiting_card("Waiting for the base model…")
        try:
            base = await _wait(job.base, timeout)
        except Exception as e:  # noqa: BLE001  超时或推理出错
            msg = problem_card(_failure_text(e))
            yield msg, msg
            return
        base_html, _ = result_card(base, text)
        yield base_html, scanning_card(text, "LoRA model")
        try:
            lora = await _wait(job.lora, timeout)
        except Exception as e:  # noqa: BLE001
            yield base_html, problem_card(_failure_text(e))
            return
        lora_html, _ = result_card(lora, text)
        yield base_html, lora_html
    finally:
        # 正常结束、超时、出错、页面被关掉（生成器被关闭）都会走到这里：没跑完的部分取消掉
        if not job.lora.done():
            job.cancel()


def _failure_text(e):
    if isinstance(e, TimeoutError):
        return "The model took too long to answer. Please try again."
    return f"Something went wrong ({type(e).__name__}). Please try again."


def mock_output(text, lora, delay):
    """--mock：不加载模型，造一个假结果，只用来检查界面布局。delay 模拟生成用时（秒）。"""
    time.sleep(delay)
    if not lora:
        return '{"整体情感": "中性", "方面": [{"方面": "舒适度", "观点": "很舒服", "情感": "正面"}]}'
    aspects = []
    for kw, asp, senti in [("屏幕", "使用效果", "正面"), ("坏", "故障瑕疵", "负面"), ("客服", "服务", "负面"),
                           ("物流", "物流", "正面"), ("尺码", "尺寸重量", "负面"), ("隔音", "房间设施", "负面")]:
        if kw in text:
            i = text.index(kw)
            aspects.append({"方面": asp, "观点": text[i:i + 6], "情感": senti})
    return json.dumps({"整体情感": "负面" if "坏" in text or "差" in text else "正面", "方面": aspects}, ensure_ascii=False)


def build_ui(engine, adapter_label):
    async def analyze(text):
        """异步生成器：每 yield 一次，页面上两张卡片就刷新一次（排队 → 扫描 → 结果）。"""
        text = (text or "").strip()
        if not text:
            gr.Warning("Please type a review first.")
            yield gr.skip(), gr.skip()
            return
        if len(text) > MAX_CHARS:
            gr.Info(f"Review truncated to {MAX_CHARS} characters.")
            text = text[:MAX_CHARS]
        if not engine.ready.is_set():
            gr.Warning("The model is still warming up — please try again in a few seconds.")
            yield gr.skip(), gr.skip()
            return
        if engine.error:
            msg = problem_card(f"The model failed to load: {engine.error}")
            yield msg, msg
            return
        async for step in analyze_steps(engine, text):
            yield step

    def report(text, upload, progress=gr.Progress()):
        rows = product_report.read_reviews(text, upload)
        if not rows:
            gr.Warning("Paste some reviews, upload a file, or click a sample file.")
            return gr.skip(), gr.skip(), gr.skip()
        if len(rows) > product_report.MAX_REVIEWS:
            gr.Info(f"Using the first {product_report.MAX_REVIEWS} of {len(rows)} reviews.")
            rows = rows[:product_report.MAX_REVIEWS]
        if not engine.ready.is_set() or engine.error:
            gr.Warning("The model is not ready yet — please try again in a few seconds.")
            return gr.skip(), gr.skip(), gr.skip()
        texts = [t[:MAX_CHARS] for t, _ in rows]
        labels = [lab for _, lab in rows]
        raws = []
        try:
            # 每 16 条交给推理线程一次：进度条能动，别人的单条请求也能在两组之间插进来
            for i in range(0, len(texts), 16):
                progress(i / len(texts), desc=f"Reading reviews {i + 1}–{min(i + 16, len(texts))} of {len(texts)}")
                raws += engine.submit_batch(texts[i:i + 16]).result(timeout=TIMEOUT_SEC * 2)
        except Exception as e:  # noqa: BLE001
            msg = f'<div class="rl-problems">Something went wrong ({esc(type(e).__name__)}). Please try again.</div>'
            return msg, None, None
        rep = product_report.build_report(texts, raws, labels)
        csv_path = os.path.join(tempfile.mkdtemp(prefix="review_report_"), "review_report.csv")
        product_report.to_csv(csv_path, texts, rep, labels)
        return (product_report.render_html(rep), gr.update(value=product_report.plot(rep), visible=True),
                gr.update(value=csv_path, visible=True))

    with gr.Blocks(title="Beyond Star Ratings — demo") as demo:
        # 一整页往下滚：开头 → How it works → Results（介绍，带出场动画）→ Try it live → Product report（实机）
        gr.HTML(intro_html())

        gr.HTML(section_head("Try it live.", "The same 1.7B model answers twice: as-is, and with our LoRA adapter.", "try"))
        with gr.Column(elem_classes="rl-window"):
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
                    base_out = gr.HTML(waiting_card("Results appear here"))
                with gr.Column(elem_classes="rl-lora"):
                    gr.Markdown("### LoRA fine-tuned")
                    lora_out = gr.HTML(waiting_card("Results appear here"))
            with gr.Accordion("The 16 aspects the model may choose from", open=False):
                gr.Markdown("| Aspect | 中文 | Covers |\n|---|---|---|\n" + "\n".join(
                    f"| {ASPECT_EN[k]} | {k} | {v} |" for k, v in ASPECTS.items()))

        gr.HTML(section_head("A whole product, in one report.",
                             f"Paste up to {product_report.MAX_REVIEWS} reviews, upload a CSV/TXT, or click a sample file. "
                             "About 0.75 s per review.", "report"))
        with gr.Column(elem_classes="rl-window"):
            with gr.Row():
                rep_text = gr.Textbox(label="Reviews (one per line)", lines=8, max_lines=14, scale=3)
                with gr.Column(scale=2, min_width=220):
                    rep_file = gr.File(label="…or upload CSV / TXT", file_types=[".csv", ".txt"], type="filepath")
                    # 点一下示例就把 CSV 装进上传框：能看到文件格式，也能下载下来照着改
                    gr.Examples([[p] for p in SAMPLES.values()], inputs=rep_file,
                                example_labels=[f"{name} · 150 reviews" for name in SAMPLES],
                                label="…or click a sample file (150 unseen reviews each)")
                    rep_btn = gr.Button("Generate report", variant="primary")
            rep_html = gr.HTML()
            with gr.Row():
                # 生成报告前先藏起来，免得显示空的占位图标；图自带标题，所以不再加标签
                rep_plot = gr.Plot(show_label=False, visible=False)
                rep_csv = gr.File(label="Download per-review results (CSV)", visible=False)
            gr.Markdown("<small>Built-in samples come from the dataset, which mixes positive and negative reviews "
                        "roughly 50/50 by design, so their positive share is not that of a real product.</small>")

        gr.HTML(f'<div class="rl-foot">Han Daiyuan · Li Mingtai · Lingnan University<br>'
                f'Qwen3-1.7B + 70 MB LoRA adapter ({esc(adapter_label)}) · runs locally on an Apple M5 with MLX · '
                'one request at a time, so you may wait in a short queue</div>')
        # 自己画排队/扫描状态，所以关掉 Gradio 自带的进度遮罩。不限并发：每个人的请求马上进推理线程的队伍、
        # 马上看到自己的排队位置；等待是事件循环里的协程，不占线程。真正的推理仍由推理线程一个一个做
        btn.click(analyze, box, [base_out, lora_out], show_progress="hidden", concurrency_limit=None,
                  api_name="analyze")
        box.submit(analyze, box, [base_out, lora_out], show_progress="hidden", concurrency_limit=None)
        rep_btn.click(report, [rep_text, rep_file], [rep_html, rep_plot, rep_csv])
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
    theme = gr.themes.Soft(primary_hue="blue", font=FONT, font_mono=FONT_MONO).set(
        body_background_fill="#FFFFFF", button_primary_background_fill="#3B5BDB")
    demo.launch(server_name=args.host, server_port=args.port, share=args.share, css=CSS, head=HEAD_JS,
                theme=theme, show_error=True)


if __name__ == "__main__":
    main()
