// 生成双语讲稿：每页一节，英文一段、中文一段对照；每人一部分，末尾是这个人主答的问答准备。
// 用法：node write_speech_md.js [讲稿文件] [输出前缀] [分钟数]
// 输出（在 cdt503/presentation/ 下）：<前缀>.md（两人合在一起）、<前缀>_Han.md、<前缀>_Mingtai.md
const fs = require("fs");
const path = require("path");
const [SRC = "speech.js", PREFIX = "speech_script", MINUTES = "8"] = process.argv.slice(2);
const SPEECH = require("./" + SRC);
const QA = require("./qa.js");

const toSec = (t) => { const [m, s] = t.split(":").map(Number); return m * 60 + s; };
const fmt = (sec) => `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;

// 按讲者分成连续的几部分（每个人只出现一次）
const parts = [];
SPEECH.forEach((p, i) => {
  const last = parts[parts.length - 1];
  if (last && last.speaker === p.speaker) last.pages.push(i);
  else parts.push({ speaker: p.speaker, pages: [i] });
});
const span = (part) => `第 ${part.pages[0] + 1}–${part.pages[part.pages.length - 1] + 1} 页`;
const secs = (part) => part.pages.reduce((a, i) => a + toSec(SPEECH[i].time), 0);
const total = SPEECH.reduce((a, p) => a + toSec(p.time), 0);

// 英文一段，下面跟中文一段（中文缩进显示）
const pair = (en, zh) => [en, "", `> ${zh}`, ""];

const partLines = (part, n) => [
  `## 第${"一二三四"[n]}部分：${part.speaker}（${span(part)}，约 ${fmt(secs(part))}）`, "",
  ...part.pages.flatMap((i) => {
    const p = SPEECH[i];
    return [`### 第 ${i + 1} 页 · ${p.title}（约 ${p.time}）`, "", ...p.say.flatMap((en, k) => pair(en, p.zh[k]))];
  }),
  `### ${part.speaker} 的问答准备`, "",
  ...QA.filter((q) => q.who === part.speaker).flatMap((q, k) => [
    `**Q${k + 1}. ${q.q}**`, "", `> ${q.qZh}`, "", q.a, "", `> ${q.aZh}`, "",
  ]),
];

const header = (who) => [
  `# 讲稿：Beyond Star Ratings（${MINUTES} 分钟版${who ? `，${who}` : ""}）`, "",
  parts.map((part) => `${part.speaker}：${span(part)}，约 ${fmt(secs(part))}`).join("。") + `。全程约 ${fmt(total)}。`, "",
  "每页先英文、后中文对照。完整的问答准备见 qa_prep.md。", "",
];

const write = (name, lines) => {
  fs.writeFileSync(path.resolve(__dirname, "..", name), lines.join("\n"));
  console.log("已生成", name);
};
write(`${PREFIX}.md`, [...header(), ...parts.flatMap((part, n) => partLines(part, n))]);
parts.forEach((part, n) => {
  const short = part.speaker.split(" ").pop();  // Daiyuan / Mingtai
  const tag = part.speaker.startsWith("Han") ? "Han" : short;
  write(`${PREFIX}_${tag}.md`, [...header(part.speaker), ...partLines(part, n)]);
});
console.log(`总长 ${fmt(total)}`);
