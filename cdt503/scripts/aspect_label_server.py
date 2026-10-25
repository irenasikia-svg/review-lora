"""CDT503 第 2 阶段：方面人工标注工具的后端。不加载任何模型，不占 GPU。

用法：
  uv run python cdt503/scripts/aspect_label_server.py                  # 只在本机用，打开 http://localhost:8772
  uv run python cdt503/scripts/aspect_label_server.py --host 0.0.0.0   # 同一 Wi-Fi 下组员用 http://<本机IP>:8772 访问

每个组员在网页上选自己的名字，只看到分给自己的评论；标注结果按人分开存：
  cdt503/data/aspect_gold_<名字>.jsonl   每行 {"gid", "annotator", "aspects": [{"方面", "情感"}], "ts"}
标注规则、方面定义、示例直接取自 scripts/common.py —— 和老师模型、学生模型用的是同一份。
"""
import argparse
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "cdt503/scripts"))
from aspects_en import ASPECT_EN, CATEGORY_EN  # noqa: E402
from common import ASPECTS, CONFUSION_RULES, EXAMPLES, SENTIMENTS  # noqa: E402

DATA = os.path.join(ROOT, "cdt503/data")
TODO = os.path.join(DATA, "aspect_gold_todo.jsonl")
ASSIGN = os.path.join(DATA, "aspect_assign.json")
lock = threading.Lock()  # 几个组员同时保存时，避免同一个文件被同时写


def gold_path(annotator):
    return os.path.join(DATA, f"aspect_gold_{annotator}.jsonl")


def load_gold(annotator):
    path = gold_path(annotator)
    if not os.path.exists(path):
        return {}
    return {r["gid"]: r for r in map(json.loads, open(path))}


def validate(aspects):
    if not isinstance(aspects, list):
        return "aspects 必须是列表"
    seen = set()
    for a in aspects:
        if a.get("方面") not in ASPECTS or a.get("情感") not in SENTIMENTS:
            return f"非法的方面或情感：{a}"
        if a["方面"] in seen:
            return f"方面重复：{a['方面']}"
        seen.add(a["方面"])
    return None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            with open(os.path.join(ROOT, "cdt503/demo/aspect_label.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if url.path == "/api/guide":
            assign = json.load(open(ASSIGN))
            return self._send(200, {
                "annotators": list(assign["assign"]),
                "aspects": [{"name": k, "en": ASPECT_EN[k], "desc": v} for k, v in ASPECTS.items()],
                "rules": CONFUSION_RULES,
                "examples": [{"text": t, "aspects": out["方面"]} for t, out in EXAMPLES],
            })
        if url.path == "/api/items":
            who = parse_qs(url.query).get("annotator", [""])[0]
            assign = json.load(open(ASSIGN))["assign"]
            if who not in assign:
                return self._send(400, {"error": "未知的标注者"})
            todo = {r["gid"]: r for r in map(json.loads, open(TODO))}
            # 只发标注需要的字段：不发数据集的情感标签，也没有任何模型输出，避免影响判断
            items = [{"gid": g, "cat": todo[g]["cat"], "cat_en": CATEGORY_EN.get(todo[g]["cat"], ""),
                      "text": todo[g]["text"]} for g in assign[who]]
            gold = load_gold(who)
            return self._send(200, {"items": items, "labels": {str(k): v["aspects"] for k, v in gold.items()}})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/label":
            return self._send(404, {"error": "not found"})
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        who, gid, aspects = body.get("annotator"), body.get("gid"), body.get("aspects")
        assign = json.load(open(ASSIGN))["assign"]
        if who not in assign or gid not in assign[who]:
            return self._send(400, {"error": "这条评论没有分给你"})
        if aspects is not None and (err := validate(aspects)):
            return self._send(400, {"error": err})
        with lock:
            gold = load_gold(who)
            if aspects is None:
                gold.pop(gid, None)
            else:
                gold[gid] = {"gid": gid, "annotator": who, "aspects": aspects, "ts": int(time.time())}
            tmp = gold_path(who) + ".tmp"
            with open(tmp, "w") as f:
                for k in sorted(gold):
                    f.write(json.dumps(gold[k], ensure_ascii=False) + "\n")
            os.replace(tmp, gold_path(who))
        self._send(200, {"ok": True, "done": len(gold)})

    def log_message(self, fmt, *a):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8772)
    args = ap.parse_args()
    print(f"方面标注页：http://{'localhost' if args.host == '127.0.0.1' else args.host}:{args.port}", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
