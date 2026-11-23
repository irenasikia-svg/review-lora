#!/bin/sh
# 一键生成展示 PPT 和讲稿（8 分钟版、6 分钟版各一份；两份 PPT 幻灯片一样，只有演讲者备注不同）
# 排版（pptxgenjs）→ 加图表（python-pptx）→ 生成讲稿文档
# 用法：sh cdt503/presentation/deck/build.sh
set -e
cd "$(dirname "$0")"
[ -d node_modules ] || npm install --no-audit --no-fund
NODE_PATH=node_modules node build_deck.js
uv run --with python-pptx python add_charts.py
node write_speech_md.js speech.js speech_script.md 8
SPEECH=speech_6min.js OUT=CDT503_BeyondStarRatings_slides_6min.pptx NODE_PATH=node_modules node build_deck.js
uv run --with python-pptx python add_charts.py
node write_speech_md.js speech_6min.js speech_script_6min.md 6
