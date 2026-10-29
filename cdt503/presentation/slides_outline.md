# 展示 PPT 大纲

幻灯片上的文字和讲稿用英文（课程要求）；方括号里的中文是给你们自己看的提示。
**A = Han Daiyuan，B = Li Mingtai**（和人工标注时的编号一致，见 `cdt503/CONTRIBUTIONS.md`）。两人都要讲，时间大致各一半。

评分对照：原型能跑 10 分（第 8 页现场演示）、讲得清楚 5 分、问答 5 分（见 `qa_prep.md`）、团队合作 5 分（两人分段讲、演示时一人操作一人讲解）。

---

## 8 分钟版（目标 7:40，留 20 秒余量）

| # | 讲者 | 时长 | 累计 |
|---|---|---|---|
| 1 | A | 0:40 | 0:40 |
| 2 | A | 0:35 | 1:15 |
| 3 | A | 0:50 | 2:05 |
| 4 | A | 0:40 | 2:45 |
| 5 | B | 0:40 | 3:25 |
| 6 | B | 1:10 | 4:35 |
| 7 | B | 1:00 | 5:35 |
| 8 | A 操作 + B 讲解 | 1:20 | 6:55 |
| 9 | A（前半）+ B（结论） | 0:45 | 7:40 |

### Slide 1 — Title & the problem (A, 0:40)
- **Title:** Distilling a 30B Teacher into a 1.7B Student — LoRA fine-tuning for aspect extraction from Chinese reviews, on a laptop
- **Visual:** one real review with three coloured highlights: *close to the metro* (+ Location), *poor sound insulation* (− Room), *check-in took half an hour* (− Service)
- **Say:** "Star ratings tell a shop *whether* customers are happy, not *why*. One sentence can hide three different signals. We built a small model that turns any Chinese review into structured JSON a program can count."

### Slide 2 — Real, dirty data (A, 0:35)
- 62,774 reviews, 10 categories → 54,472 after cleaning → 2,425 stratified sample
- Show 2–3 ugly examples: duplicated template ("我为什么每个商品的评价都一样…" appears 23×), empty text, emoji noise
- **Say:** "This is real e-commerce data — duplicates, copy-pasted templates, rants. We cleaned it and sampled evenly across categories and sentiment."
- [这一页对应评分里的"真实脏数据"，一定要出现具体的脏数据例子]

### Slide 3 — System architecture (A, 0:50)
- **Visual:** Fig. 1 from the report (the TikZ pipeline)
- **Say:** walk left to right — teacher labels → quality filter → train/val/test → LoRA student → sweep → final adapter used three ways (test set, human evaluation, live demo)
- Emphasise: "Everything runs on one Apple M5 laptop with 32 GB."

### Slide 4 — Knowledge distillation & a better label schema (A, 0:40)
- Teacher = Qwen3-30B-A3B; quality filter keeps 2,228 / 2,425 (drops invalid JSON and labels that contradict the human star rating)
- Schema v1 → v2: 12 → 16 aspects + disambiguation rules
- Proof the schema got clearer: a second model agrees with the teacher more (0.768 → 0.806), teacher errors 40 → 15
- **Say:** "Our biggest early win was not a model change — it was writing clearer label definitions."

### Slide 5 — LoRA fine-tuning (B, 0:40)
- Equation: **h = W₀x + s·BAx** — W₀ frozen, only the small matrices A and B are trained
- 17.4M of 1,720M parameters (1%), adapter = 70 MB, 94 min on the laptop
- Loss only on the answer tokens ("mask prompt")
- **Say:** "Instead of changing 1.7 billion weights, LoRA adds a thin side path. That is why it fits on a laptop."

### Slide 6 — Systematic hyper-parameter study (B, 1:10)
- **Visual:** the bar chart (Fig. 2 bottom) with the grey seed band
- Three findings, one line each:
  1. **Learning rate matters most:** 5e-5 best (0.793); 2e-4 diverged within 40 steps
  2. **Bigger rank is *not* better** — r=32 fell to 0.697, but fixing the scale (α constant) brought it back to 0.766 → it was the update size, not the rank
  3. **Top-8 layers only:** same quality, half the training time
- **Say:** "The grey band is what randomness alone does — we ran the default twice with different seeds. Anything inside the band we treat as noise."
- [这一页对应"系统调参并附对比图"，是 Level 2 的关键，讲慢一点]

### Slide 7 — Results (B, 1:00)
- Left: **test set (262)** — aspect-F1 0.513 → 0.734 → **0.807**; JSON validity 90.8% → 100%; tuning adds +0.073 (95% CI +0.038 to +0.110)
- Right: **100 never-used reviews, labelled by us two** — student 0.701 ≈ teacher 0.689 (not significantly different), base 0.458
- **Say:** "A model 17 times smaller matches the teacher when judged by humans. And it agrees with humans about as well as we two agreed with each other before discussing."

### Slide 8 — Live demo (A operates, B narrates, 1:20)
- 见 `demo_script.md`。屏幕上只放 Gradio 页面，旁边放二维码
- [如果现场出问题，第 15 秒内切换到备用视频，不要现场调试]

### Slide 9 — Challenges & conclusion (A 0:25 + B 0:20)
- A — challenges, one line each: overfitting (best checkpoint never the last one) · ambiguous labels · GPU out-of-memory with teacher + demo · long prompt slowed inference 0.34 → 0.58 s
- B — conclusion: "1.7B student, 1.8k teacher-labelled reviews, one laptop: 100% valid JSON and teacher-level quality. The lessons were mostly about data: a clear schema, a quality filter, and honest evaluation on unseen data. Thank you — questions?"

---

## 5 分钟版（压缩版）

合并原来的 1–2、3–4、6–7 页，演示缩短到 3 个例子。

| # | 内容（对应 8 分钟版） | 讲者 | 时长 |
|---|---|---|---|
| 1 | Problem + dirty data（1 + 2） | A | 0:50 |
| 2 | Architecture + distillation（3 + 4，只讲框图，schema 一句带过） | A | 0:50 |
| 3 | Hyper-parameter study（6，只讲学习率和 rank/scale 两点） | B | 1:00 |
| 4 | Results（7，测试集一个数字 + 人工评估一句话） | B | 0:40 |
| 5 | Live demo：例子 1、6 + 观众一句 | A 操作 + B 讲解 | 1:10 |
| 6 | Conclusion（9 的 B 部分） | B | 0:30 |

删掉的内容（LoRA 公式、层数实验、挑战）留给问答环节——被问到时正好能展开。

---

## 制作建议

- 每页文字不超过 3 行要点，数字用大字号；图直接用 `cdt503/figures/` 里的 PNG
- 第 3 页用报告图 1：可以把 `cdt503/report/main.pdf` 第 2 页上的框图截下来
- 第 6 页用 `cdt503/figures/sweep_metrics.png`；第 7 页可以做成两个大数字卡片 + 一张小表
- 最后一页放 GitHub 链接或二维码之前，先确认仓库是否已经公开（截止前建议不公开）
- 彩排至少两次，用手机计时；8 分钟是硬上限
