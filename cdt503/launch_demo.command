#!/bin/zsh
# CDT503 演示网页：在访达里双击这个文件即可启动（会打开一个终端窗口）。
#
# 它会依次：检查环境 → 启动演示（真实模型，约 20–30 秒预热）→ 自动打开网页
#           → 生成扫码页（有公网链接就用公网链接，没有就用局域网地址）并打开
# 停止演示：关掉这个终端窗口，或按 Control + C
#
# 可选开关（一般用不到）：DEMO_SHARE=0 不生成公网链接；NO_OPEN=1 不自动打开网页（测试用）

PROJECT="$HOME/claude/review-lora"
PORT=7860
TMP="${${TMPDIR:-/tmp}%/}"
LOG="$TMP/cdt503_demo.log"
QR_HTML="$TMP/cdt503_qr.html"
SHARE_FLAG="--share"; [[ "$DEMO_SHARE" == "0" ]] && SHARE_FLAG=""
UV="$(command -v uv 2>/dev/null || echo "$HOME/.local/bin/uv")"

step() { print -P "%F{cyan}▶%f $1"; }
warn() { print -P "%F{yellow}⚠ $1%f"; }
fail() { print -P "%F{red}✗ $1%f"; echo; read -k1 "?按任意键关闭窗口…"; exit 1; }
show() { [[ "$NO_OPEN" == "1" ]] || open "$1"; }

clear
print -P "%B%F{yellow}★★★%f  Beyond Star Ratings — 演示启动器%b"
echo

# —— 检查 ——
cd "$PROJECT" 2>/dev/null || fail "找不到项目文件夹 $PROJECT"
[[ -x "$UV" ]] || fail "找不到 uv（Python 环境工具）。请先安装：https://docs.astral.sh/uv/"
[[ -f cdt503/runs/sweep/lr5e-5/best/adapters.safetensors ]] || \
  fail "找不到模型权重 cdt503/runs/sweep/lr5e-5/best/（换电脑演示时，把 5_代码/模型权重 里的压缩包解压到这里）"

if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  step "演示已经在运行，直接打开网页"
  show "http://127.0.0.1:$PORT"
  [[ -f "$QR_HTML" ]] && show "$QR_HTML"
  echo; read -k1 "?按任意键关闭窗口…"; exit 0
fi

OTHERS=$(pgrep -fl "mlx_lm|demo_server.py|label_server.py|adjudicate_server.py|countdown" | grep -v pgrep)
if [[ -n "$OTHERS" ]]; then
  warn "有别的模型程序正在占用 GPU，同时运行可能内存不足："
  echo "$OTHERS"
  read -k1 "?仍要继续吗？(y/n) " ans; echo
  [[ "$ans" == "y" ]] || exit 1
fi

# —— 启动 ——
step "启动演示：加载模型并预热，大约 20–30 秒…"
: > "$LOG"
"$UV" run python cdt503/app_gradio.py $SHARE_FLAG --host 0.0.0.0 --port $PORT >> "$LOG" 2>&1 &
APP=$!

stop() {
  trap - INT TERM HUP EXIT
  echo; step "正在停止演示…"
  pkill -TERM -P $APP 2>/dev/null; kill $APP 2>/dev/null; wait $APP 2>/dev/null
  [[ -n "$TAIL" ]] && kill $TAIL 2>/dev/null
  step "已停止。可以关闭这个窗口了。"
  exit 0
}
trap stop INT TERM HUP EXIT

for i in {1..180}; do
  curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break
  if ! kill -0 $APP 2>/dev/null; then
    tail -20 "$LOG"; trap - EXIT; fail "演示启动失败（上面是错误信息；最常见的原因是 GPU 内存不足，关掉其他模型程序再试）"
  fi
  sleep 1
done
curl -s -o /dev/null "http://127.0.0.1:$PORT/" || { tail -20 "$LOG"; trap - EXIT; stop; }
step "网页已就绪，正在打开：http://127.0.0.1:$PORT"
show "http://127.0.0.1:$PORT"

# —— 扫码页：优先用公网链接（最多等 40 秒），否则用局域网地址 ——
PUBLIC=""
if [[ -n "$SHARE_FLAG" ]]; then
  step "正在申请公网链接（最多等 40 秒）…"
  for i in {1..40}; do
    PUBLIC=$(grep -o 'https://[a-z0-9.-]*\.gradio\.live' "$LOG" | head -1)
    [[ -n "$PUBLIC" ]] && break
    sleep 1
  done
  [[ -z "$PUBLIC" ]] && warn "没拿到公网链接（网络可能拦截了），改用局域网地址"
fi
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
LAN=""; [[ -n "$IP" ]] && LAN="http://$IP:$PORT"
if [[ -n "$PUBLIC" ]]; then
  "$UV" run -q --with "qrcode[pil]" python cdt503/scripts/make_qr_page.py "$PUBLIC" "$QR_HTML" && show "$QR_HTML"
elif [[ -n "$LAN" ]]; then
  "$UV" run -q --with "qrcode[pil]" python cdt503/scripts/make_qr_page.py "$LAN" "$QR_HTML" lan && show "$QR_HTML"
fi

echo
print -P "%B演示正在运行%b"
echo   "  本机：      http://127.0.0.1:$PORT"
[[ -n "$PUBLIC" ]] && echo "  公网链接：  $PUBLIC   （同学手机扫码用这个）"
[[ -n "$LAN" ]] && echo "  局域网：    $LAN   （同一 Wi-Fi 下可用）"
[[ -f "$QR_HTML" ]] && echo "  扫码页：    $QR_HTML"
echo
print -P "%F{8}停止演示：关掉这个窗口，或按 Control + C。下面是运行日志：%f"
tail -n 0 -f "$LOG" &
TAIL=$!
wait $APP
trap - EXIT
kill $TAIL 2>/dev/null
warn "演示已经退出（日志：$LOG）"
read -k1 "?按任意键关闭窗口…"
