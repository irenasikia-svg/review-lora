"""给报告和 PPT 截演示页的高清图（真实模型）。

先启动演示：uv run python cdt503/app_gradio.py（端口 7860，等到"预热完成"），再运行：
  uv run --with playwright python cdt503/scripts/capture_demo_screens.py
用本机已装的 Google Chrome（不另外下载浏览器），2 倍像素密度。输出到 cdt503/figures/demo_screens/：
  compare_scanning.png  左边出结果、右边正在扫描（示例 1）
  compare_done.png      两边都出结果（示例 1）
  report_hotel.png      商品报告页，Hotel 示例文件（约 2 分钟）
"""
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "cdt503/figures/demo_screens")
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:7860/"


def union_clip(page, selectors, pad=12):
    """几个元素合起来的外框，用来只截结果区域。"""
    boxes = [page.locator(s).first.bounding_box() for s in selectors]
    x0 = min(b["x"] for b in boxes) - pad
    y0 = min(b["y"] for b in boxes) - pad
    x1 = max(b["x"] + b["width"] for b in boxes) + pad
    y1 = max(b["y"] + b["height"] for b in boxes) + pad
    return {"x": max(0, x0), "y": max(0, y0), "width": x1 - max(0, x0), "height": y1 - max(0, y0)}


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
        page.goto(URL)
        page.get_by_text("果子特别棒没有伤比超市便宜又好吃?直的够买", exact=True).click()
        page.wait_for_timeout(600)
        page.get_by_role("button", name="Analyze").click()

        # 左边出结果、右边还在扫描的那一刻
        page.wait_for_function("document.querySelectorAll('.rl-done').length === 1 && "
                               "document.querySelectorAll('.rl-scanning').length === 1", timeout=60000)
        page.wait_for_timeout(700)
        cols = ["h3:has-text('Base model')", ".rl-lora"]
        page.screenshot(path=os.path.join(OUT, "compare_scanning.png"), clip=union_clip(page, cols))

        page.wait_for_function("document.querySelectorAll('.rl-done').length === 2", timeout=60000)
        page.wait_for_timeout(1500)  # 等高亮依次亮起的动画走完
        page.screenshot(path=os.path.join(OUT, "compare_done.png"), clip=union_clip(page, cols))
        print("单条对比截图完成", flush=True)

        page.get_by_role("tab", name="Product report").click()
        page.get_by_text("Hotel · 150 reviews", exact=True).click()
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Generate report").click()
        page.wait_for_selector(".pr-card", timeout=400000)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(OUT, "report_hotel.png"), full_page=True)
        print("商品报告截图完成", flush=True)
        browser.close()


if __name__ == "__main__":
    main()
