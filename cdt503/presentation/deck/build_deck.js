// 生成 CDT503 展示 PPT（英文，9 页，16:9，明亮简洁版）。
// 用法（在本目录）：sh build.sh   —— 先跑这个文件排版，再用 add_charts.py 加原生图表
// 为什么图表分开加：pptxgenjs 写的图表 Keynote 打不开（显示空白），python-pptx 写的可以，PowerPoint/WPS 也都能编辑。
// 图片来自 cdt503/figures/demo_screens/（cdt503/scripts/capture_demo_screens.py 截的真实模型画面）；
// 数字全部来自报告 main.tex，改了实验要同步改这里和 add_charts.py。
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Lu = require("react-icons/lu");
const SPEECH = require("./speech.js");

// pptx skill 自带的主题工具：pptxgenjs 写不进主题颜色，要写完文件后再补上
const SKILL = process.env.PPTX_SKILL_DIR ||
  "/Users/kuumo/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/33e16445-e3ec-486e-b180-de8224061862/d84a8898-2fe1-42f1-882a-1712a84d8d54/skills/pptx";
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));

const ROOT = path.resolve(__dirname, "../../..");
const SHOTS = path.join(ROOT, "cdt503/figures/demo_screens");
const OUT = path.join(ROOT, "cdt503/presentation/CDT503_BeyondStarRatings_slides.pptx");
const CHART_SPECS = path.join(__dirname, "charts.json");

// 配色：白底；琥珀色（星级）是主强调色；绿/红只表示好评/差评，蓝只表示"我们的 LoRA 模型"
const THEME = {
  name: "Beyond Star Ratings", headFontFace: "Georgia", bodyFontFace: "Arial",
  colors: {
    dk1: "1F2330", lt1: "FFFFFF", dk2: "5A5F73", lt2: "F4F5F9",
    accent1: "F2A93B", accent2: "2E9E6A", accent3: "E0603F", accent4: "3B5BDB",
    accent5: "8E94A8", accent6: "DADDE6", hlink: "3B5BDB", folHlink: "6D4AFF",
  },
};
const HEX = THEME.colors;
const CJK = "PingFang SC";  // 中文统一用苹方；Windows 上会自动换成微软雅黑，汉字同样是等宽的

async function icon(Comp, hex, px = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + hex, size: px }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";  // 10 × 5.625 英寸
  pres.title = "Beyond Star Ratings: Aspect Extraction from Chinese Reviews";
  pres.author = "Han Daiyuan, Li Mingtai";
  pres.subject = "CDT503 final project presentation";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;
  const charts = [];  // 交给 add_charts.py 的图表位置和数据

  // —— 版式：所有页都是白底；内容页标题统一左上角 ——
  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: "FFFFFF" },
    margin: [0.5, 0.5, 0.5, 0.5],
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.32, w: 9.0, h: 0.62, fontSize: 26,
        bold: true, color: C.text1, align: "left", valign: "middle", margin: 0 }, text: "" } },
      { text: { text: "Beyond Star Ratings · CDT503", options: { x: 0.5, y: 5.24, w: 4, h: 0.22, fontSize: 9,
        color: C.accent5, margin: 0 } } },
    ],
    slideNumber: { x: 9.1, y: 5.22, w: 0.4, h: 0.25, fontSize: 9, color: "8E94A8", align: "right" },
  });
  pres.defineSlideMaster({ title: "COVER", background: { color: "FFFFFF" }, objects: [] });

  // —— 小部件 ——
  const card = (s, x, y, w, h, o = {}) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.08, fill: { color: o.fill || C.background2, transparency: o.transparency || 0 },
    line: o.line ? { color: o.line, width: 1 } : { type: "none" }, objectName: o.name || "card",
  });
  const text = (s, t, x, y, w, h, o = {}) => s.addText(t, { x, y, w, h, margin: 0, isTextBox: true, valign: "top", ...o });
  const chip = (s, label, x, y, kind = "neutral", o = {}) => {
    const fs = o.fontSize || 11;
    const w = o.w || 0.2 + label.length * fs * 0.0072;
    const fill = { pos: { color: C.accent2, transparency: 84 }, neg: { color: C.accent3, transparency: 84 },
      neutral: { color: C.background2 } }[kind];
    const color = { pos: C.accent2, neg: C.accent3, neutral: C.text1 }[kind];
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: o.h || 0.3, rectRadius: 0.15, fill, line: { type: "none" },
      objectName: "chip " + label });
    text(s, label, x, y, w, o.h || 0.3, { fontSize: fs, bold: kind !== "neutral", color, align: "center", valign: "middle" });
    return w;
  };
  const SLOT = { [C.accent1]: "accent1", [C.accent2]: "accent2", [C.accent3]: "accent3", [C.accent4]: "accent4" };
  const iconCircle = async (s, Comp, x, y, d, col) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: col, transparency: 84 }, line: { type: "none" },
      objectName: "icon circle" });
    s.addImage({ data: await icon(Comp, HEX[SLOT[col]]), x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5,
      altText: "icon" });
  };
  const arrow = (s, x, y, w, h, o = {}) => s.addShape(pres.shapes.LINE, { x, y, w, h, flipV: !!o.flipV, flipH: !!o.flipH,
    line: { color: o.color || C.accent5, width: 1.25, endArrowType: "triangle" }, objectName: "arrow" });
  // 中文评论里画荧光笔高亮：汉字和全角标点都是 1 个字号宽，所以按字数就能算出位置
  const cjkLine = (s, line, x, y, fs, marks = []) => {
    const cw = fs / 72, bh = cw * 1.35, hh = cw * 1.2;
    for (const [from, to, kind] of marks) {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + from * cw - 0.03, y: y + (bh - hh) / 2, w: (to - from) * cw + 0.06,
        h: hh, rectRadius: 0.05, fill: { color: kind === "pos" ? C.accent2 : C.accent3, transparency: 75 },
        line: { type: "none" }, objectName: "highlight" });
    }
    text(s, line, x, y, line.length * cw + 0.2, bh, { fontSize: fs, color: C.text1, fontFace: CJK, valign: "middle" });
  };
  const notes = (s, i) => s.addNotes(`[${SPEECH[i].speaker} · ${SPEECH[i].time}]\n\n` + SPEECH[i].say.join("\n\n") +
    "\n\n—— " + SPEECH[i].tips);
  const W0 = (o = {}) => [{ text: "W", options: o }, { text: "0", options: { ...o, subscript: true } }];

  // ============ 1. 封面 ============
  pres.addSection({ title: "Problem" });
  let s = pres.addSlide({ masterName: "COVER", sectionTitle: "Problem" });
  text(s, "CDT503 FINAL PROJECT  ·  TRACK B: NLP / PEFT", 0.6, 0.6, 5.2, 0.3,
    { fontSize: 11, bold: true, color: C.accent1, charSpacing: 2 });
  text(s, "Beyond Star Ratings", 0.6, 1.0, 5.0, 1.55, { fontSize: 44, bold: true, color: C.text1, fontFace: THEME.headFontFace });
  text(s, "Aspect Extraction from Chinese Reviews", 0.6, 2.6, 5.0, 0.45, { fontSize: 19, color: C.text2 });
  for (let i = 0; i < 5; i++) {
    s.addShape(pres.shapes.STAR_5_POINT, { x: 0.6 + i * 0.42, y: 3.35, w: 0.32, h: 0.32,
      fill: i < 3 ? { color: C.accent1 } : { type: "none" }, line: { color: C.accent1, width: 1.25 }, objectName: "star" });
  }
  text(s, "… but why?", 2.85, 3.35, 2.5, 0.32, { fontSize: 15, italic: true, color: C.text2, valign: "middle" });
  text(s, "Han Daiyuan (3231363)   ·   Li Mingtai (3231959)", 0.6, 4.5, 5.2, 0.3, { fontSize: 13, color: C.text1 });
  text(s, "Lingnan University", 0.6, 4.83, 5.2, 0.28, { fontSize: 11, color: C.accent5 });
  card(s, 5.85, 0.95, 3.65, 3.8, { name: "review card" });
  text(s, "ONE REVIEW, THREE SIGNALS", 6.15, 1.2, 3.2, 0.28, { fontSize: 10, bold: true, color: C.accent1, charSpacing: 1.5 });
  [["酒店离地铁站很近，", [[2, 8, "pos"]]], ["早餐种类挺多，", []], ["但是房间隔音很差，", [[2, 8, "neg"]]],
    ["前台办入住等了半小时", [[0, 10, "neg"]]]].forEach(([line, marks], i) => cjkLine(s, line, 6.15, 1.65 + i * 0.5, 17, marks));
  chip(s, "Location +", 6.15, 3.8, "pos");
  chip(s, "Service −", 7.35, 3.8, "neg");
  chip(s, "Room & facilities −", 6.15, 4.2, "neg");
  notes(s, 0);

  // ============ 2. 任务 ============
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Problem" });
  s.addText(SPEECH[1].title, { placeholder: "title" });
  card(s, 0.5, 1.2, 4.75, 3.8, { name: "json card" });
  text(s, "MODEL OUTPUT (JSON)", 0.78, 1.42, 4.2, 0.25, { fontSize: 10, bold: true, color: C.accent1, charSpacing: 1.5 });
  const code = (t, o = {}) => ({ text: t, options: { fontFace: "Courier New", color: HEX.dk2, ...o } });
  const k = (t) => code(`"${t}"`, { color: "6B7085" });
  const v = (t) => code(`"${t}"`, { color: HEX.dk1 });
  const cn = (t) => code(`"${t}"`, { color: HEX.dk1, fontFace: CJK });
  const sent = (t) => code(`"${t}"`, { color: t === "positive" ? HEX.accent2 : HEX.accent3, bold: true });
  const line = (...runs) => { runs[runs.length - 1].options.breakLine = true; return runs; };
  const json = [
    ...line(code("{")),
    ...line(code("  "), k("overall"), code(": "), sent("negative"), code(",")),
    ...line(code("  "), k("aspects"), code(": [")),
    ...line(code("    { "), k("aspect"), code(": "), v("Location"), code(",")),
    ...line(code("      "), k("opinion"), code(": "), cn("离地铁站很近"), code(",")),
    ...line(code("      "), k("sentiment"), code(": "), sent("positive"), code(" },")),
    ...line(code("    { "), k("aspect"), code(": "), v("Room & facilities"), code(",")),
    ...line(code("      "), k("opinion"), code(": "), cn("房间隔音很差"), code(",")),
    ...line(code("      "), k("sentiment"), code(": "), sent("negative"), code(" },")),
    ...line(code("    { "), k("aspect"), code(": "), v("Service"), code(",")),
    ...line(code("      "), k("opinion"), code(": "), cn("前台办入住等了半小时"), code(",")),
    ...line(code("      "), k("sentiment"), code(": "), sent("negative"), code(" }")),
    ...line(code("  ]")),
    code("}"),
  ];
  text(s, json, 0.78, 1.8, 4.3, 3.1, { fontSize: 11.5, lineSpacingMultiple: 1.0 });
  text(s, "16 fixed aspects", 5.65, 1.2, 3.85, 0.35, { fontSize: 16, bold: true, color: C.text1 });
  const ASPECTS = ["Performance", "Build & material", "Defect", "Authenticity", "Price", "Gifts & accessories",
    "Logistics", "Service", "Appearance", "Size & weight", "Taste", "Packaging", "Content", "Room & facilities",
    "Location", "Other"];
  const used = { "Location": "pos", "Room & facilities": "neg", "Service": "neg" };
  ASPECTS.forEach((a, i) => chip(s, a, 5.65 + (i % 2) * 1.97, 1.75 + Math.floor(i / 2) * 0.405, used[a] || "neutral",
    { w: 1.85, h: 0.31, fontSize: 10.5 }));
  notes(s, 1);

  // ============ 3. 数据 ============
  pres.addSection({ title: "Method" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
  s.addText(SPEECH[2].title, { placeholder: "title" });
  [["62,774", "real reviews, 10 categories", 4.75], ["54,472", "after cleaning", 4.35],
    ["2,425", "balanced sample", 3.95], ["2,228", "after filtering", 3.55]].forEach(([n, label, w], i) => {
    const y = 1.2 + i * 0.95;
    card(s, 0.5, y, w, 0.8, { fill: C.accent1, transparency: 66 + i * 8, name: "funnel step" });
    text(s, n, 0.75, y, 1.6, 0.8, { fontSize: 24, bold: true, color: C.text1, fontFace: THEME.headFontFace, valign: "middle" });
    text(s, label, 2.4, y, w - 2.05, 0.8, { fontSize: 12, color: C.text1, valign: "middle" });
  });
  const facts = [
    [Lu.LuCopy, C.accent3, "One template, 23 copies", [{ text: "“我为什么每个商品的评价都一样……”", options: { fontFace: CJK } }]],
    [Lu.LuListChecks, C.accent2, "Clearer labels: 12 → 16 aspects", "teacher errors fell from 40 to 15"],
  ];
  for (let i = 0; i < facts.length; i++) {
    const [Ic, col, head, body] = facts[i];
    const y = 1.2 + i * 1.95;
    card(s, 5.6, y, 3.9, 1.7, { name: "fact" });
    await iconCircle(s, Ic, 5.85, y + 0.3, 0.6, col);
    text(s, head, 5.85, y + 1.0, 3.45, 0.3, { fontSize: 14, bold: true, color: C.text1 });
    text(s, body, 5.85, y + 1.32, 3.45, 0.3, { fontSize: 11.5, color: C.text2 });
  }
  notes(s, 2);

  // ============ 4. 系统 ============
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
  s.addText(SPEECH[3].title, { placeholder: "title" });
  const boxes = [["Clean sample", "2,425 reviews", null], ["Teacher", "Qwen3-30B-A3B", C.accent1],
    ["Quality filter", "2,228 kept", null], ["Split", "1,824 / 142 / 262", null],
    ["Student", "Qwen3-1.7B + LoRA", C.accent4], ["Sweep", "10 runs, val. only", null]];
  const BW = 1.33, BG = 0.2, BY = 1.25, BH = 0.95;
  boxes.forEach(([head, body, col], i) => {
    const x = 0.5 + i * (BW + BG);
    card(s, x, BY, BW, BH, { fill: col || C.background2, transparency: col ? 82 : 0, name: "pipeline " + head });
    text(s, head, x + 0.12, BY + 0.17, BW - 0.24, 0.28, { fontSize: 12, bold: true, color: C.text1 });
    text(s, body, x + 0.12, BY + 0.5, BW - 0.24, 0.35, { fontSize: 10.5, color: C.text2 });
    if (i < boxes.length - 1) arrow(s, x + BW + 0.03, BY + BH / 2, BG - 0.06, 0);
  });
  const sweepX = 0.5 + 5 * (BW + BG) + BW / 2;
  card(s, 3.85, 2.8, 2.3, 0.6, { fill: C.accent4, name: "final adapter" });
  text(s, "Final adapter · 70 MB", 3.85, 2.8, 2.3, 0.6, { fontSize: 13, bold: true, color: C.background1, align: "center",
    valign: "middle" });
  s.addShape(pres.shapes.LINE, { x: sweepX, y: BY + BH, w: 0, h: 3.1 - BY - BH, line: { color: C.accent5, width: 1.25 },
    objectName: "connector" });
  arrow(s, 6.17, 3.1, sweepX - 6.17, 0, { flipH: true });
  const uses = [[Lu.LuTarget, "Test set", "262 held-out reviews"], [Lu.LuUsers, "Human evaluation", "100 new reviews"],
    [Lu.LuMonitorSmartphone, "Live demo", "LoRA on / off"]];
  for (let i = 0; i < uses.length; i++) {
    const [Ic, head, body] = uses[i];
    const x = 0.5 + i * 3.05, y = 3.9;
    card(s, x, y, 2.9, 1.05, { name: "use " + head });
    await iconCircle(s, Ic, x + 0.2, y + 0.25, 0.55, C.accent4);
    text(s, head, x + 0.92, y + 0.25, 1.85, 0.3, { fontSize: 13, bold: true, color: C.text1 });
    text(s, body, x + 0.92, y + 0.57, 1.85, 0.3, { fontSize: 11, color: C.text2 });
    const cx = x + 1.45, x0 = 5.0, y0 = 3.4, dx = cx - x0;
    s.addShape(pres.shapes.LINE, { x: Math.min(x0, cx), y: y0, w: Math.abs(dx) || 0.001, h: y - y0 - 0.04, flipH: dx < 0,
      line: { color: C.accent5, width: 1.25, endArrowType: "triangle" }, objectName: "arrow to use" });
  }
  notes(s, 3);

  // ============ 5. LoRA ============
  pres.addSection({ title: "Training" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Training" });
  s.addText(SPEECH[4].title, { placeholder: "title" });
  const node = (label, x, y, d, fill, color) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: "node " + label });
    text(s, label, x, y, d, d, { fontSize: 16, bold: true, color, align: "center", valign: "middle",
      fontFace: THEME.headFontFace, italic: true });
  };
  node("x", 0.5, 2.2, 0.55, C.background2, C.text1);
  card(s, 1.45, 1.3, 2.25, 0.95, { name: "W0" });
  text(s, [...W0({ bold: true, fontSize: 15 }), { text: "  frozen", options: { bold: true, fontSize: 15, breakLine: true } },
    { text: "1,720M weights", options: { fontSize: 11, color: HEX.dk2 } }], 1.65, 1.45, 1.9, 0.7, { color: C.text1 });
  for (const [label, sub, x] of [["A", "r × k", 1.45], ["B", "d × r", 2.75]]) {
    card(s, x, 2.95, 0.95, 0.8, { fill: C.accent4, transparency: 82, name: label });
    text(s, [{ text: label, options: { bold: true, fontSize: 16, italic: true, fontFace: THEME.headFontFace, breakLine: true } },
      { text: sub, options: { fontSize: 10 } }], x, 3.0, 0.95, 0.7, { color: C.accent4, align: "center", valign: "middle" });
  }
  arrow(s, 2.42, 3.35, 0.3, 0, { color: C.accent4 });
  text(s, "trained (r = 16)", 1.45, 3.82, 2.25, 0.25, { fontSize: 10, color: C.accent4, align: "center" });
  node("+", 4.1, 2.2, 0.55, C.accent1, C.background1);
  node("h", 4.95, 2.2, 0.55, C.background2, C.text1);
  arrow(s, 1.05, 1.78, 0.38, 0.69, { flipV: true });
  arrow(s, 1.05, 2.47, 0.38, 0.88);
  arrow(s, 3.72, 1.78, 0.42, 0.5);
  arrow(s, 3.72, 2.62, 0.42, 0.73, { flipV: true });
  arrow(s, 4.67, 2.47, 0.26, 0);
  const it = { italic: true };
  text(s, [{ text: "h = ", options: it }, ...W0(it), { text: "x + s · BAx", options: it }], 0.5, 4.3, 4.9, 0.5,
    { fontSize: 24, color: C.text1, fontFace: THEME.headFontFace });
  [["1%", "of the weights are trained"], ["70 MB", "adapter file"], ["94 min", "training on one laptop"]].forEach(([big, small], i) => {
    const y = 1.25 + i * 1.27;
    card(s, 5.95, y, 3.55, 1.08, { name: "stat " + big });
    text(s, big, 6.25, y + 0.1, 3.0, 0.55, { fontSize: 30, bold: true, color: C.accent4, fontFace: THEME.headFontFace });
    text(s, small, 6.25, y + 0.68, 3.0, 0.3, { fontSize: 12, color: C.text2 });
  });
  notes(s, 4);

  // ============ 6. 调参 ============
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Training" });
  s.addText(SPEECH[5].title, { placeholder: "title" });
  charts.push({ slide: 6, kind: "bar", x: 0.35, y: 1.05, w: 6.0, h: 3.9, title: "Validation aspect-F1 (142 reviews)",
    min: 0.65, max: 0.82, major: 0.05, rows: [["Default", 0.758, "1F2330"], ["r = 4", 0.780, "C3C7D4"],
      ["r = 8", 0.762, "C3C7D4"], ["r = 32", 0.697, HEX.accent3], ["r = 32, s = 10", 0.766, "C3C7D4"],
      ["lr 5e-5", 0.793, HEX.accent1], ["Top 8 layers", 0.749, "C3C7D4"], ["Top 16 layers", 0.760, "C3C7D4"]] });
  // Keynote 只给纵轴标签留约 13 个字符宽，标签要短；默认配置的含义写在下面
  text(s, "Default = r 16, lr 1e-4, all 28 layers", 0.5, 5.0, 5.8, 0.22, { fontSize: 9.5, color: C.accent5 });
  const finds = [[Lu.LuGauge, C.accent1, "lr 5e-5 is best", "all 3 seeds beat the default"],
    [Lu.LuLayers, C.accent3, "r = 32 is worse", "fixed by halving the scale"],
    [Lu.LuTimer, C.accent2, "Top 8 layers", "same quality, half the time"]];
  for (let i = 0; i < finds.length; i++) {
    const [Ic, col, head, body] = finds[i];
    const y = 1.3 + i * 1.12;
    await iconCircle(s, Ic, 6.6, y, 0.55, col);
    text(s, head, 7.3, y + 0.02, 2.2, 0.28, { fontSize: 14, bold: true, color: C.text1 });
    text(s, body, 7.3, y + 0.3, 2.2, 0.3, { fontSize: 11.5, color: C.text2 });
  }
  text(s, "Seed noise ≈ 0.02", 6.6, 4.65, 2.9, 0.3, { fontSize: 11, italic: true, color: C.accent5 });
  notes(s, 5);

  // ============ 7. 结果 ============
  pres.addSection({ title: "Results" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText(SPEECH[6].title, { placeholder: "title" });
  charts.push({ slide: 7, kind: "col", x: 0.4, y: 1.1, w: 4.5, h: 2.95, title: "Test set (262 reviews)", min: 0, max: 1,
    major: 0.25, rows: [["Base 1.7B", 0.513, "C3C7D4"], ["LoRA default", 0.734, "9DB0F0"], ["LoRA tuned", 0.801, HEX.accent4]] });
  charts.push({ slide: 7, kind: "col", x: 5.1, y: 1.1, w: 4.5, h: 2.95, title: "Human labels (100 new reviews)", min: 0, max: 1,
    major: 0.25, rows: [["Base 1.7B", 0.458, "C3C7D4"], ["Student 1.7B", 0.701, HEX.accent4], ["Teacher 30B", 0.689, HEX.accent1]] });
  text(s, "Aspect-F1 · tuned = mean of 3 seeds", 0.5, 4.07, 4.4, 0.3, { fontSize: 10.5, color: C.accent5, align: "center" });
  text(s, "Student vs teacher: no significant difference", 5.2, 4.07, 4.4, 0.3, { fontSize: 10.5, color: C.accent5, align: "center" });
  [["5×", "less memory"], ["1.8×", "faster"], ["0.59", "few-shot only"]].forEach(([big, small], i) => {
    const x = 0.5 + i * 3.05;
    card(s, x, 4.5, 2.9, 0.58, { name: "strip " + big });
    text(s, [{ text: big + "  ", options: { bold: true, fontSize: 18, color: i === 2 ? HEX.accent3 : HEX.accent4,
      fontFace: THEME.headFontFace } }, { text: small, options: { fontSize: 12, color: HEX.dk1 } }],
    x, 4.5, 2.9, 0.58, { align: "center", valign: "middle" });
  });
  notes(s, 6);

  // ============ 8. 演示 ============
  pres.addSection({ title: "Demo" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Demo" });
  s.addText(SPEECH[7].title, { placeholder: "title" });
  const img = (file, x, y, w, ratio, alt) => {
    card(s, x - 0.05, y - 0.05, w + 0.1, w / ratio + 0.1, { fill: "FFFFFF", line: "DADDE6", name: "frame" });
    s.addImage({ path: path.join(SHOTS, file), x, y, w, h: w / ratio, altText: alt });
  };
  img("compare_done.png", 0.55, 1.2, 5.5, 2480 / 766, "Base model output invalid; LoRA output valid with highlighted opinions");
  text(s, [{ text: "1  ", options: { bold: true, color: HEX.accent1, fontFace: THEME.headFontFace, fontSize: 16 } },
    { text: "Same model: without the adapter it invents “flavour”; with it, Taste + and Price +.", options: { fontSize: 12 } }],
  0.55, 3.0, 5.5, 0.55, { color: C.text1 });
  text(s, [{ text: "2  ", options: { bold: true, color: HEX.accent1, fontFace: THEME.headFontFace, fontSize: 16 } },
    { text: "150 hotel reviews → 53% positive (stars: 55%).", options: { fontSize: 12 } }], 0.55, 3.65, 5.5, 0.4,
  { color: C.text1 });
  text(s, [{ text: "Scan the QR code to try it", options: { bold: true } }], 0.55, 4.45, 5.5, 0.35,
    { fontSize: 13, color: C.accent4 });
  img("report_kpis.png", 6.4, 1.2, 3.1, 2420 / 940, "Product report: KPIs and top aspects");
  img("report_chart.png", 6.4, 2.55, 3.1, 1204 / 920, "Product report: aspects mentioned, by sentiment");
  notes(s, 7);

  // ============ 9. 结论 ============
  pres.addSection({ title: "Conclusion" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Conclusion" });
  s.addText(SPEECH[8].title, { placeholder: "title" });
  [["Data beats model size", "clear labels + a quality filter"], ["A laptop is enough", "≈ the 30B teacher at 1/5 of the memory"],
    ["Measure honestly", "validation for tuning, fresh human labels"]].forEach(([head, body], i) => {
    const x = 0.5 + i * 3.05;
    card(s, x, 1.25, 2.9, 2.05, { name: "lesson " + (i + 1) });
    text(s, String(i + 1), x + 0.25, 1.4, 0.6, 0.6, { fontSize: 32, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
    text(s, head, x + 0.25, 2.1, 2.45, 0.35, { fontSize: 15, bold: true, color: C.text1 });
    text(s, body, x + 0.25, 2.48, 2.45, 0.6, { fontSize: 11.5, color: C.text2 });
  });
  text(s, "CHALLENGES", 0.5, 3.6, 2.0, 0.3, { fontSize: 10, bold: true, color: C.accent5, charSpacing: 1.5, valign: "middle" });
  let cx = 1.9;
  for (const t of ["overfitting after epoch 1", "GPU out of memory", "long prompt, slower inference"]) {
    cx += chip(s, t, cx, 3.6, "neutral", { fontSize: 11 }) + 0.15;
  }
  text(s, "Thank you — questions?", 0.5, 4.3, 5.5, 0.55, { fontSize: 24, bold: true, color: C.accent1, fontFace: THEME.headFontFace,
    valign: "middle" });
  text(s, "github.com/irenasikia-svg/review-lora", 6.0, 4.3, 3.5, 0.55, { fontSize: 10.5, color: C.accent5, align: "right",
    valign: "middle" });
  notes(s, 8);

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  fs.writeFileSync(CHART_SPECS, JSON.stringify({ deck: OUT, charts }, null, 2));
  console.log("已生成", OUT, "（图表待 add_charts.py 添加）");
}

main().catch((e) => { console.error(e); process.exit(1); });
