#!/bin/sh
# 打包上传 TeXPage 用的 zip：main.tex、refs.bib、fig_pipeline.tex 放在根目录，图片放在 figures/ 里
# （main.tex 的 \graphicspath 同时认 ../figures/ 和 figures/，所以本地和 TeXPage 都能编译）。
# 用法：sh cdt503/report/make_texpage_zip.sh   →  生成 cdt503/report/texpage.zip
set -e
cd "$(dirname "$0")"
OUT="$(pwd)/texpage.zip"
TMP="$(mktemp -d)"
mkdir "$TMP/figures"
cp main.tex refs.bib fig_pipeline.tex "$TMP/"
# 只拷报告里实际用到的图（PDF 是矢量图，放大不糊）
for f in sweep_val_curves sweep_metrics final_loss_curve human_per_aspect_f1 human_error_analysis; do
  cp "../figures/$f.pdf" "$TMP/figures/"
done
[ -f ../figures/demo_screenshot.png ] && cp ../figures/demo_screenshot.png "$TMP/figures/"
rm -f "$OUT"
(cd "$TMP" && zip -qr "$OUT" .)
rm -r "$TMP"
echo "已生成 $OUT"
