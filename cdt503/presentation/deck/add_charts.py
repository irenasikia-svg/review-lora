"""给 build_deck.js 生成的 PPT 加原生柱状图（Keynote、WPS、PowerPoint 都能显示和编辑）。

读 charts.json（build_deck.js 写的：哪一页、位置、数据、每根柱子的颜色），用 python-pptx 加图后原地保存。
用法：uv run --with python-pptx python add_charts.py
"""
import json
import os

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
LABEL = RGBColor(0x5A, 0x5F, 0x73)
GRID = RGBColor(0xE3, 0xE5, 0xEC)
INK = RGBColor(0x1F, 0x23, 0x30)


def rgb(hexstr):
    return RGBColor.from_string(hexstr)


def add_chart(slide, spec):
    rows = spec["rows"]
    if spec["kind"] == "bar":
        rows = rows[::-1]  # 横向条形图从下往上画，倒过来后第一行在最上面
    data = CategoryChartData()
    data.categories = [r[0] for r in rows]
    data.add_series("Aspect-F1", [r[1] for r in rows])
    kind = XL_CHART_TYPE.BAR_CLUSTERED if spec["kind"] == "bar" else XL_CHART_TYPE.COLUMN_CLUSTERED
    gf = slide.shapes.add_chart(kind, Inches(spec["x"]), Inches(spec["y"]), Inches(spec["w"]), Inches(spec["h"]), data)
    gf.name = "chart: " + spec["title"]
    chart = gf.chart
    chart.font.name = "Arial"
    chart.font.size = Pt(11)
    chart.font.color.rgb = LABEL
    chart.has_legend = False
    chart.has_title = True
    chart.chart_title.text_frame.text = spec["title"]
    tp = chart.chart_title.text_frame.paragraphs[0]
    tp.runs[0].font.size = Pt(12)
    tp.runs[0].font.bold = False
    tp.runs[0].font.color.rgb = LABEL

    plot = chart.plots[0]
    plot.gap_width = 50
    plot.vary_by_categories = False
    series = plot.series[0]
    for point, r in zip(series.points, rows):
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = rgb(r[2])
        point.format.line.fill.background()
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.number_format = "0.000"
    labels.number_format_is_linked = False
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    labels.font.size = Pt(11)
    labels.font.color.rgb = INK

    va = chart.value_axis
    va.minimum_scale, va.maximum_scale, va.major_unit = spec["min"], spec["max"], spec["major"]
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = GRID
    va.major_gridlines.format.line.width = Pt(0.75)
    va.format.line.fill.background()
    va.tick_labels.number_format = "0.00"
    va.tick_labels.number_format_is_linked = False
    va.tick_labels.font.size = Pt(10)
    ca = chart.category_axis
    ca.format.line.color.rgb = GRID
    ca.tick_labels.font.size = Pt(11)
    ca.has_major_gridlines = False


def main():
    spec = json.load(open(os.path.join(HERE, "charts.json")))
    prs = Presentation(spec["deck"])
    for c in spec["charts"]:
        add_chart(prs.slides[c["slide"] - 1], c)
    prs.save(spec["deck"])
    print(f"已加 {len(spec['charts'])} 张图表：{spec['deck']}")


if __name__ == "__main__":
    main()
