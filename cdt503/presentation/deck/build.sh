#!/bin/sh
# 一键生成展示 PPT：排版（pptxgenjs）→ 加图表（python-pptx）→ 生成讲稿文档
# 用法：sh cdt503/presentation/deck/build.sh
set -e
cd "$(dirname "$0")"
[ -d node_modules ] || npm install --no-audit --no-fund
NODE_PATH=node_modules node build_deck.js
uv run --with python-pptx python add_charts.py
node write_speech_md.js
