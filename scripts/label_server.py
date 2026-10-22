"""人工标注工具的后端：给 150 条评论标"价值分类"。不加载任何模型。

用法：uv run python scripts/label_server.py --split test  然后浏览器打开 http://localhost:8771
每标一条就写进 data/value_<split>.jsonl，随时关掉、下次接着标。
"""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--split", default="test", choices=["dev", "test"])
SPLIT = ap.parse_args().split
TODO = os.path.join(ROOT, f"data/value_{SPLIT}_todo.jsonl")
GOLD = os.path.join(ROOT, f"data/value_{SPLIT}.jsonl")
VALUES = ["有效评论", "模板重复", "套话好评", "无信息量", "空洞差评"]
PORT = 8771


def load_items():
    # 只把标注需要看到的字段发给网页：不包含抽样分层，也没有任何模型判断
    return [{k: r[k] for k in ("gid", "cat", "text", "dup_count", "group_cats")}
            for r in map(json.loads, open(TODO))]


def load_gold():
    if not os.path.exists(GOLD):
        return {}
    return {r["gid"]: r for r in map(json.loads, open(GOLD))}


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
            with open(os.path.join(ROOT, "demo/label.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/api/items":
            gold = load_gold()
            self._send(200, {"split": SPLIT, "values": VALUES, "items": load_items(),
                             "labels": {str(k): v["value"] for k, v in gold.items()}})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/label":
            return self._send(404, {"error": "not found"})
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        gid, value = body.get("gid"), body.get("value")
        if value not in VALUES and value is not None:
            return self._send(400, {"error": "未知分类"})
        gold = load_gold()
        if value is None:
            gold.pop(gid, None)
        else:
            gold[gid] = {"gid": gid, "value": value}
        # 整个文件重写，按 gid 排序，便于在 git 里看改动
        with open(GOLD, "w") as f:
            for k in sorted(gold):
                f.write(json.dumps(gold[k], ensure_ascii=False) + "\n")
        self._send(200, {"ok": True, "done": len(gold)})

    def log_message(self, fmt, *a):
        pass


if __name__ == "__main__":
    print(f"标注 {SPLIT}：http://localhost:{PORT}", flush=True)
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
