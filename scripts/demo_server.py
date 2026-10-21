"""演示网页的后端：输入一条评论，同时给出原始模型和 LoRA 微调后模型的抽取结果。

用法：
  uv run python scripts/demo_server.py               # 默认用第一版模型
  uv run python scripts/demo_server.py --version v2  # 第二版训练完成后
然后浏览器打开 http://localhost:8770

省内存的小技巧：只加载一份模型。LoRA 层的输出是 原始输出 + scale × 小矩阵的输出，
把 scale 临时设成 0，旁路就不起作用，模型就变回原始模型。所以"开关 LoRA"不需要加载两份。
"""
import argparse
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VERSIONS = {
    "v1": {"rules_dir": os.path.join(ROOT, "runs/v1"),
           "adapter": os.path.join(ROOT, "runs/v1/adapters_step240"),
           "label": "第一版标签 · LoRA 第 240 步"},
    "v2": {"rules_dir": None,
           "adapter": os.path.join(ROOT, "adapters_best"),
           "label": "第二版标签 · LoRA 第 400 步"},
}

ap = argparse.ArgumentParser()
ap.add_argument("--version", default="v1", choices=VERSIONS)
ap.add_argument("--port", type=int, default=8770)
args = ap.parse_args()
cfg = VERSIONS[args.version]

# 和 annotator_agreement.py 一样：规则目录排在最前面，import 到的就是那一版的规则
sys.path.insert(0, os.path.join(ROOT, "scripts"))
if cfg["rules_dir"]:
    sys.path.insert(0, cfg["rules_dir"])
from mlx_lm import generate  # noqa: E402
from mlx_lm.tuner.lora import LoRALinear  # noqa: E402

from common import ASPECTS, SENTIMENTS, parse_output  # noqa: E402
from gen import encode, load_model  # noqa: E402

STUDENT = "mlx-community/Qwen3-1.7B-bf16"
EXAMPLES = [
    "衣服收到了，质量不错，穿上大小合适，很舒服，满意",
    "还好，稍微有点卡，给家里老人买的。够用，价格合理，耐用，我家人手机平板都选华为。支持国产！",
    "东西还行，到货当天降价了，申请价格保护，却被拒绝了",
    "买了2个不一样的裤子，结果卖家挑了其中一款最便宜的发了两条，而且11号下单，18号才收到。",
    "这苹果还可以，味道不错，我都准备再买",
    "地上有大蟑螂，床上有虫子",
    "热水器很漂亮，而且比实体店实惠多了。配的配件齐全，安装后使用了一下，加热很快。超赞！",
    "新手机买来有点卡，充电器是坏的，我找手机供应商，他们让我找京东快递，两边踢皮球",
]

print(f"加载 {STUDENT} + {cfg['adapter']} ...", flush=True)
model, tokenizer = load_model(STUDENT, adapter_path=cfg["adapter"])
lora_layers = [m for _, m in model.named_modules() if isinstance(m, LoRALinear)]
lora_scales = [m.scale for m in lora_layers]
print(f"已加载，共 {len(lora_layers)} 个 LoRA 层", flush=True)


def set_lora(enabled: bool):
    for m, s in zip(lora_layers, lora_scales):
        m.scale = s if enabled else 0.0


def diagnose(raw: str):
    """输出不合格时，说清楚具体哪里不合规（给演示页显示用）。"""
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.S).strip()
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return ["没有找到 JSON"]
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return ["JSON 语法错误（可能输出太长被截断）"]
    problems = []
    if obj.get("整体情感") not in SENTIMENTS:
        problems.append(f"整体情感「{obj.get('整体情感')}」不是正面/负面")
    for a in obj.get("方面", []) if isinstance(obj.get("方面"), list) else []:
        if isinstance(a, dict):
            if a.get("方面") not in ASPECTS:
                problems.append(f"方面「{a.get('方面')}」不在列表里")
            if a.get("情感") not in SENTIMENTS:
                problems.append(f"情感「{a.get('情感')}」不是正面/负面")
    return problems or ["字段缺失或类型不对"]


def run(text: str, enabled: bool):
    set_lora(enabled)
    start = time.time()
    raw = generate(model, tokenizer, encode(tokenizer, text), max_tokens=256)
    ms = int((time.time() - start) * 1000)
    parsed = parse_output(raw)
    return {"raw": raw, "parsed": parsed, "ms": ms,
            "problems": [] if parsed else diagnose(raw)}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(ROOT, "demo/index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/api/info":
            self._send(200, {"version": args.version, "label": cfg["label"], "model": STUDENT,
                             "aspects": ASPECTS, "examples": EXAMPLES})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/extract":
            return self._send(404, {"error": "not found"})
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        text = str(body.get("text", "")).strip()[:300]
        if not text:
            return self._send(400, {"error": "评论不能为空"})
        result = {"original": run(text, enabled=False), "lora": run(text, enabled=True)}
        self._send(200, result)

    def log_message(self, fmt, *a):
        sys.stderr.write("%s %s\n" % (self.command, self.path))


if __name__ == "__main__":
    print(f"演示页：http://localhost:{args.port}", flush=True)
    # 用单线程服务器：MLX 的计算流是按线程绑定的，模型在主线程加载，就只能在主线程里推理。
    # 顺带保证 GPU 一次只处理一个请求。
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
