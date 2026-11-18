"""生成扫码页：大二维码 + 网址，投到屏幕上让同学用手机扫。启动器 launch_demo.command 会自动调用。

用法：uv run --with "qrcode[pil]" python cdt503/scripts/make_qr_page.py <网址> <输出.html> [lan]
最后加 lan 表示这是局域网地址（同学要连同一个 Wi-Fi），页面上会提示。
"""
import base64
import html
import io
import sys

import qrcode


def main():
    url, out = sys.argv[1], sys.argv[2]
    lan = len(sys.argv) > 3 and sys.argv[3] == "lan"
    buf = io.BytesIO()
    qrcode.make(url, box_size=12, border=2).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    note = "Same Wi-Fi as this laptop" if lan else "Scan with your phone camera"
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Try the demo</title>
<style>
  body {{ margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #fff;
         font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; color: #1F2330; }}
  .box {{ text-align: center; padding: 24px; }}
  h1 {{ font-family: Georgia, serif; font-size: 44px; margin: 0 0 8px; }}
  p {{ color: #5A5F73; font-size: 20px; margin: 0 0 24px; }}
  img {{ width: min(60vh, 80vw); image-rendering: pixelated; }}
  code {{ display: block; margin-top: 18px; font-size: 22px; color: #3B5BDB; word-break: break-all; }}
</style></head>
<body><div class="box">
  <h1>Try our demo</h1>
  <p>{note} · requests are answered one at a time</p>
  <img src="data:image/png;base64,{b64}" alt="QR code for {html.escape(url)}">
  <code>{html.escape(url)}</code>
</div></body></html>
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)


if __name__ == "__main__":
    main()
