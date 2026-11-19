"""浏览器冒烟测试（mock 模式，不占 GPU）：深色模式下也看得清、手机宽度不横向滚动、动画脚本出错时内容仍可见。

需要本机装了 Google Chrome。运行：
  uv run --with pytest --with playwright pytest cdt503/tests/test_browser_smoke.py -q
没有 playwright 或 Chrome 时自动跳过。
"""
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

pw = pytest.importorskip("playwright.sync_api")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _luminance(css_rgb):
    r, g, b = (int(v) / 255 for v in re.findall(r"\d+", css_rgb)[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


@pytest.fixture(scope="module")
def server():
    port = _free_port()
    proc = subprocess.Popen([sys.executable, "cdt503/app_gradio.py", "--mock", "--port", str(port)], cwd=ROOT,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/"
    for _ in range(80):
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    else:
        proc.kill()
        pytest.fail("mock server did not start")
    yield url
    proc.terminate()
    proc.wait(10)


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"Google Chrome not available: {e}")
        yield b
        b.close()


def test_dark_system_still_readable(server, browser):
    ctx = browser.new_context(color_scheme="dark", viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.goto(server)
    pg.wait_for_selector(".rl-hero h1")
    pg.wait_for_timeout(1500)
    h1 = pg.evaluate("getComputedStyle(document.querySelector('.rl-hero h1')).color")
    head = pg.evaluate("getComputedStyle(document.querySelector('.rl-section-head h2')).color")
    ctx.close()
    assert _luminance(h1) < 0.4 and _luminance(head) < 0.4  # 白底上的深色字


def test_no_horizontal_scroll_on_phone(server, browser):
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, is_mobile=True)
    pg = ctx.new_page()
    pg.goto(server)
    pg.wait_for_selector(".rl-window")
    pg.wait_for_timeout(1500)
    width = pg.evaluate("document.documentElement.scrollWidth")
    ctx.close()
    assert width <= 375


def test_content_visible_if_script_throws(server, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()

    def inject(route):  # 在页面里的动画脚本加上 js-anim 之后故意制造一个错误
        resp = route.fetch()
        body = resp.text()
        body = body.replace('classList.add("js-anim");', 'classList.add("js-anim"); undefinedFn();')
        body = body.replace('classList.add(\\"js-anim\\");', 'classList.add(\\"js-anim\\"); undefinedFn();')
        route.fulfill(response=resp, body=body)

    pg.route(server, inject)
    pg.goto(server)
    pg.wait_for_selector(".rl-hero h1")
    pg.wait_for_timeout(4000)
    hidden = pg.evaluate("[...document.querySelectorAll('.reveal')].filter(e => getComputedStyle(e).opacity === '0').length")
    ctx.close()
    assert hidden == 0
