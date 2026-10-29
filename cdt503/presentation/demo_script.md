# 现场演示脚本（8 分钟版第 8 页，1 分 20 秒）

A（Han Daiyuan）操作电脑，B（Li Mingtai）对着观众讲。下面的英文就是 B 要说的话；"预期"是页面上应该出现的结果（2026-10-29 实测，见 `cdt503/DEMO.md` 的表格）。

**上台前**：演示已启动、终端显示"预热完成"；浏览器放大到投影看得清；屏幕角落放好扫码二维码。

---

### 0:00 — 开场（10 秒）

> "This is the live prototype, running on this laptop right now. Same 1.7B model on both sides — left without our adapter, right with it."

### 0:10 — 例子 1：原始模型不守规则（25 秒）

A 点第 1 个示例 *果子特别棒没有伤比超市便宜又好吃*，再点 **Analyze**。

预期：左边 **✗ Invalid output — Aspect "味道" is not in the allowed list**；右边 ✓ Taste +、Price +，原文里高亮。

> "A customer says the fruit is great and cheaper than the supermarket. The base model invents its own aspect name, 'flavour', which is not in our list — so a program can't count it. The fine-tuned model uses the allowed names, Taste and Price, and highlights the exact words."

### 0:35 — 例子 4：一句话拆出多个方面（20 秒）

A 点第 4 个示例（酒店），**Analyze**。

预期：左边 ✗ sentiment "中性"（neutral 不在规则里）；右边 Location +、Room & facilities −、Service −。

> "One hotel review, three signals: location good, room bad, service bad. The base model answers 'neutral', which our schema doesn't allow. The adapter splits it correctly."

### 0:55 — 例子 6：什么都没说的时候不乱抽（10 秒）

A 点第 6 个示例 *还没用，用了再来评价*，**Analyze**。

预期：右边 "No specific aspect mentioned."

> "And when a review says nothing concrete — 'haven't used it yet' — it doesn't make anything up."

### 1:05 — 请观众试（15 秒）

> "You can try it on your phone — scan the QR code. If many of you try at once there's a short queue: about four seconds per request."

如果时间还够、有人报一句评论，A 就现场输入；时间紧就跳过，直接回到 PPT。

---

## 出问题时怎么办（不要现场调试）

| 情况 | 做法 | 说法 |
|---|---|---|
| 页面打不开 / 卡住超过 10 秒 | 立刻切到备用视频 | "Let me show you a recording of the same demo." |
| 结果和预期不一样 | 照实讲出现的结果，不要假装 | "The model is deterministic, but here it shows … — that's exactly the kind of boundary case we discuss in our error analysis." |
| 观众输入的评论模型答错了 | 承认并联系错误分析 | "Good example — it confuses build quality with performance, which is our most common error." |
| 同学扫码打不开 | 不等，继续讲 | "The link may be blocked by the campus network — we'll share it after class." |

## 彩排检查

- [ ] A 点击和 B 讲话的节奏对上（B 说完一句，A 再点下一个）
- [ ] 每次 Analyze 等待约 3–4 秒，讲稿里留出等待时间，不要冷场：可以边等边说"the same model answers twice…"
- [ ] 整段控制在 1 分 20 秒内
