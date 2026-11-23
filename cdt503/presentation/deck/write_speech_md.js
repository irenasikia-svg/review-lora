// 从 speech.js 生成讲稿文档 cdt503/presentation/speech_script.md（按 PPT 页码排，和 PPT 备注同一份内容）
const fs = require("fs");
const path = require("path");
const SPEECH = require("./speech.js");

const toSec = (t) => { const [m, s] = t.split(":").map(Number); return m * 60 + s; };
const fmt = (sec) => `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;
// 只数要念出来的词（方括号里的动作不算）
const words = (p) => p.say.join(" ").replace(/\[[^\]]*\]/g, " ").split(/\s+/).filter(Boolean).length;

let total = 0, totalWords = 0;
const rows = SPEECH.map((p, i) => {
  const sec = toSec(p.time), w = words(p);
  total += sec; totalWords += w;
  return `| 第 ${i + 1} 页 | ${p.title} | ${p.speaker} | ${p.time} | ${fmt(total)} | ${w} 词 |`;
});
const wpm = Math.round(totalWords / total * 60);

// 动作 [..] 单独成行，用斜体标出；念的部分放引用块
const render = (t) => {
  const m = t.match(/^\[([^\]]*)\]\s*(.*)$/);
  return m ? [`*动作：${m[1]}*`, "", `> ${m[2]}`] : [`> ${t}`];
};

const out = [
  "# 讲稿：Beyond Star Ratings（8 分钟版，按 PPT 页码）",
  "",
  "**A = Han Daiyuan，B = Li Mingtai。** 每一节对应 PPT 的一页。引用块里的英文是要说的话，*动作* 不念出来，「提示」是给自己看的中文说明。",
  `语速按每分钟约 ${wpm} 个英文词写（比平时说话慢一些）；每页讲完停一拍再翻页。PPT 每页的演讲者备注里是同一份内容（改 \`deck/speech.js\` 一处，两边同步）。`,
  "",
  "| PPT 页码 | 标题 | 讲者 | 时长 | 累计 | 字数 |",
  "|---|---|---|---|---|---|",
  ...rows,
  "",
  `总长 ${fmt(total)}，共 ${totalWords} 词，比 8 分钟上限留出约 ${fmt(480 - total)} 余量。`,
  "",
  ...SPEECH.flatMap((p, i) => [
    "---", "",
    `## PPT 第 ${i + 1} 页：${p.title}`, "",
    `**${p.speaker} · ${p.time}**（讲完时累计 ${fmt(SPEECH.slice(0, i + 1).reduce((a, q) => a + toSec(q.time), 0))}）`, "",
    `屏幕上：${p.screen}`, "",
    ...p.say.flatMap((t) => [...render(t), ""]),
    `提示：${p.tips}`, "",
    i < SPEECH.length - 1 ? `→ 翻到第 ${i + 2} 页` : "→ 进入问答（2 分钟）",
    "",
  ]),
  "---",
  "",
  "## 彩排检查",
  "",
  "- [ ] 用手机计时完整讲两遍，总长不超过 8 分钟；第 6 页（调参）和第 8 页（演示）最容易超时",
  "- [ ] 第 4 页结尾 A 交给 B、第 7 页结尾切到浏览器、第 9 页 A 交给 B，这三处交接要顺",
  "- [ ] 演示前已在第 2 个浏览器标签页生成好 Hotel 报告，第 1 个标签页停在页面顶部（见 demo_script.md）",
  "- [ ] 问答准备见 qa_prep.md，两人各自熟悉自己主答的题",
  "",
];
fs.writeFileSync(path.resolve(__dirname, "../speech_script.md"), out.join("\n"));
console.log(`已生成讲稿 speech_script.md：${fmt(total)}，${totalWords} 词，约 ${wpm} 词/分钟`);
