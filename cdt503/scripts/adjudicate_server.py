"""CDT503 第 2 阶段：人工标注的复核（仲裁）。不加载任何模型。

两位标注者一起看有问题的标注，商量出最终答案。哪些评论要复核，只看人工标注本身，不看模型输出：
  1. 两人都标过（共同标注）但标得不一样
  2. 某人标的所有方面，情感都和数据集自带的总体评价相反（例如整条是差评，却只标了好评）

复核结果写到 cdt503/data/aspect_gold_adjudicated.jsonl；A、B 的原始标注不改，
这样报告里能同时给出复核前、复核后的数字。

用法：uv run python cdt503/scripts/adjudicate_server.py   然后打开 http://localhost:8773
"""
import argparse
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "cdt503/scripts"))
from aspects_en import ASPECT_EN, CATEGORY_EN  # noqa: E402
from aspect_label_server import validate  # noqa: E402
from common import ASPECTS, CONFUSION_RULES  # noqa: E402

DATA = os.path.join(ROOT, "cdt503/data")
OUT = os.path.join(DATA, "aspect_gold_adjudicated.jsonl")
lock = threading.Lock()


def pairs(aspects):
    return {(a["方面"], a["情感"]) for a in aspects}


def load_jsonl(path, key="gid"):
    return {r[key]: r for r in map(json.loads, open(path))} if os.path.exists(path) else {}


def review_items():
    todo = load_jsonl(os.path.join(DATA, "aspect_gold_todo.jsonl"))
    order = list(json.load(open(os.path.join(DATA, "aspect_assign.json")))["assign"])
    labels = {w: {g: r["aspects"] for g, r in load_jsonl(os.path.join(DATA, f"aspect_gold_{w}.jsonl")).items()}
              for w in order}
    items = []
    for gid in sorted(todo):
        who = [w for w in order if gid in labels[w]]
        overall = "正面" if todo[gid]["label"] == 1 else "负面"
        reasons = []
        if len(who) > 1 and len({frozenset(pairs(labels[w][gid])) for w in who}) > 1:
            reasons.append("两人标得不一样")
        for w in who:
            a = labels[w][gid]
            if a and all(x["情感"] != overall for x in a):
                reasons.append(f"{w} 标的方面全是{'好评' if overall == '负面' else '差评'}，但整条是{'差评' if overall == '负面' else '好评'}")
        if not reasons:
            continue
        agreed = set.intersection(*[pairs(labels[w][gid]) for w in who])
        items.append({"gid": gid, "cat": todo[gid]["cat"], "cat_en": CATEGORY_EN.get(todo[gid]["cat"], ""),
                      "text": todo[gid]["text"], "overall": overall, "reasons": reasons,
                      "annotations": {w: labels[w][gid] for w in who},
                      "prefill": [{"方面": a, "情感": s} for a, s in sorted(agreed)]})
    return items


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
            with open(os.path.join(ROOT, "cdt503/demo/adjudicate.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if self.path == "/api/items":
            final = {g: r["aspects"] for g, r in load_jsonl(OUT).items()}
            return self._send(200, {
                "aspects": [{"name": k, "en": ASPECT_EN[k], "desc": v} for k, v in ASPECTS.items()],
                "rules": CONFUSION_RULES, "items": review_items(), "final": {str(k): v for k, v in final.items()}})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/final":
            return self._send(404, {"error": "not found"})
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        gid, aspects = body.get("gid"), body.get("aspects")
        if gid not in {it["gid"] for it in review_items()}:
            return self._send(400, {"error": "这条不在复核清单里"})
        if err := validate(aspects):
            return self._send(400, {"error": err})
        with lock:
            final = load_jsonl(OUT)
            final[gid] = {"gid": gid, "aspects": aspects, "ts": int(time.time())}
            tmp = OUT + ".tmp"
            with open(tmp, "w") as f:
                for k in sorted(final):
                    f.write(json.dumps(final[k], ensure_ascii=False) + "\n")
            os.replace(tmp, OUT)
        self._send(200, {"ok": True, "done": len(final)})

    def log_message(self, fmt, *a):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8773)
    args = ap.parse_args()
    print(f"复核页：http://localhost:{args.port}（共 {len(review_items())} 条需要复核）", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
