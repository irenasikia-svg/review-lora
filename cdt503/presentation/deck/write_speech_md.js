// 从 speech.js 生成讲稿文档 cdt503/presentation/speech_script.md（和 PPT 备注同一份内容）
const fs = require("fs");
const path = require("path");
const SPEECH = require("./speech.js");

const toSec = (t) => { const [m, s] = t.split(":").map(Number); return m * 60 + s; };
const fmt = (sec) => `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;
let total = 0;
const rows = SPEECH.map((p, i) => { total += toSec(p.time); return `| ${i + 1} | ${p.title} | ${p.speaker} | ${p.time} | ${fmt(total)} |`; });

const out = [
  "# 讲稿：Beyond Star Ratings（8 分钟版）",
  "",
  "**A = Han Daiyuan，B = Li Mingtai。** 英文是要说的话（语速约每分钟 140 词），方括号里是动作，「提示」是给自己看的中文说明。",
  "PPT 的演讲者备注里是同一份内容（`deck/speech.js` 一处修改，两边同步）。",
  "",
  "| 页 | 标题 | 讲者 | 时长 | 累计 |",
  "|---|---|---|---|---|",
  ...rows,
  "",
  `目标总长 ${fmt(total)}，比 8 分钟上限留出约 20 秒余量。`,
  "",
  ...SPEECH.flatMap((p, i) => [
    "---", "", `## ${i + 1}. ${p.title}`, "", `**${p.speaker} · ${p.time}**`, "",
    ...p.say.flatMap((t) => [`> ${t}`, ">"]).slice(0, -1), "", `提示：${p.tips}`, "",
  ]),
  "---",
  "",
  "## 彩排检查",
  "",
  "- [ ] 用手机计时完整讲两遍，总长不超过 8 分钟；第 6 页（调参）最容易超时",
  "- [ ] 第 4 页结尾 A 交给 B、第 8 页演示、第 9 页 A 交给 B，这三处交接要顺",
  "- [ ] 演示前已在另一个浏览器标签页生成好 Hotel 报告（见 demo_script.md）",
  "- [ ] 问答准备见 qa_prep.md，两人各自熟悉自己主答的题",
  "",
];
fs.writeFileSync(path.resolve(__dirname, "../speech_script.md"), out.join("\n"));
console.log("已生成讲稿 speech_script.md");
