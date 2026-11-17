# 现场演示脚本（8 分钟版第 8 页，1 分 20 秒）

A（Han Daiyuan）操作电脑，B（Li Mingtai）对着观众讲。下面的英文就是 B 要说的话；"预期"是页面上应该出现的结果（2026-10-29 实测，见 `cdt503/DEMO.md` 的表格）。

**上台前**：演示已启动、终端显示"预热完成"；浏览器放大到投影看得清；屏幕角落放好扫码二维码。
**另开一个浏览器标签页**，切到 **Product report**，选 **Hotel** 样例点 Generate report，等约 2 分钟出结果后**别刷新**——演示时直接切过去讲，不现场等。生成完再让同学扫码（生成期间单条请求要排队）。

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

### 0:55 — 商品报告：从一条评论到一整个商品（15 秒）

A 切到提前生成好的 Hotel 报告标签页（见"上台前"）。

预期（2026-11-18 离线实测，`cdt503/results/product_report/hotel/`）：150 reviews、53% positive / 47% negative、0 unusable；Most praised：Room & facilities 53×、Location 45×、Service 37×；Most criticised：Room & facilities 71×、Service 35×、Price 24×；下方一行写星级 55% 好评、整体判断一致 93%。

> "And this is what a merchant actually wants. 150 hotel reviews the model has never seen: 53% positive — the star ratings say 55% — and the complaints are specific: rooms first, then service, each with the customers' own words."

### 1:10 — 请观众试（10 秒）

> "You can try single reviews on your phone — scan the QR code. If many of you try at once there's a short queue: about four seconds each."

**备用（时间够或被问到时）**：例子 6 *还没用，用了再来评价* → 右边 "No specific aspect mentioned."
> "And when a review says nothing concrete, it doesn't make anything up."

如果时间还够、有人报一句评论，A 就现场输入；时间紧就跳过，直接回到 PPT。

---

## 出问题时怎么办（不要现场调试）

| 情况 | 做法 | 说法 |
|---|---|---|
| 页面打不开 / 卡住超过 10 秒 | 立刻切到备用视频 | "Let me show you a recording of the same demo." |
| 结果和预期不一样 | 照实讲出现的结果，不要假装 | "The model is deterministic, but here it shows … — that's exactly the kind of boundary case we discuss in our error analysis." |
| 观众输入的评论模型答错了 | 承认并联系错误分析 | "Good example — it confuses build quality with performance, which is our most common error." |
| 同学扫码打不开 | 不等，继续讲 | "The link may be blocked by the campus network — we'll share it after class." |
| 报告标签页被刷新、结果没了 | 不要现场重新生成（要 2 分钟）；跳过这一段，口头说结论 | "On 150 hotel reviews it found 53% positive — the stars say 55% — and rooms and service are the top complaints." |

## 彩排检查

- [ ] A 点击和 B 讲话的节奏对上（B 说完一句，A 再点下一个）
- [ ] 每次 Analyze 等待约 3–4 秒，讲稿里留出等待时间，不要冷场：可以边等边说"the same model answers twice…"
- [ ] 整段控制在 1 分 20 秒内
- [ ] 切到报告标签页那一下要快：提前把两个标签页挨着放，用 ⌘ + 数字键切换
