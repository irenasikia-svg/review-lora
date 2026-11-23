# 讲稿：Beyond Star Ratings（6 分钟版，按 PPT 页码）

**A = Han Daiyuan，B = Li Mingtai。** 每一节对应 PPT 的一页。引用块里的英文是要说的话，*动作* 不念出来，「提示」是给自己看的中文说明。
语速按每分钟约 84 个英文词写（比平时说话慢一些）；每页讲完停一拍再翻页。对应的 PPT 每页演讲者备注里是同一份内容（改 `deck/speech_6min.js` 一处，两边同步）。

| PPT 页码 | 标题 | 讲者 | 时长 | 累计 | 字数 |
|---|---|---|---|---|---|
| 第 1 页 | Beyond Star Ratings | A | 0:25 | 0:25 | 42 词 |
| 第 2 页 | One review in, one countable record out | A | 0:25 | 0:50 | 35 词 |
| 第 3 页 | Messy data, cleaned and labelled | A | 0:35 | 1:25 | 51 词 |
| 第 4 页 | A 30B teacher labels, a 1.7B student learns | A | 0:35 | 2:00 | 56 词 |
| 第 5 页 | LoRA: train 1% of the weights | B | 0:25 | 2:25 | 38 词 |
| 第 6 页 | Tuning: the learning rate matters most | B | 0:45 | 3:10 | 70 词 |
| 第 7 页 | Near-teacher quality, a fifth of the memory | B | 0:40 | 3:50 | 52 词 |
| 第 8 页 | Live demo | A 操作，B 讲 | 1:05 | 4:55 | 60 词 |
| 第 9 页 | What we learned | A，然后 B | 0:40 | 5:35 | 63 词 |

总长 5:35，共 467 词，比 6 分钟留出约 0:25 余量。

---

## PPT 第 1 页：Beyond Star Ratings

**A · 0:25**（讲完时累计 0:25）

屏幕上：标题、三颗实心两颗空心的星星、右边一条酒店评论（绿、红、红三处高亮）

> Good morning. We are Han Daiyuan and Li Mingtai.

> A star rating says whether a customer is happy, but not why. This hotel review has three signals: a good location, a noisy room, and a slow check-in. Our model finds them automatically.

提示：说到三个信号时，依次指右边的绿、红、红三处高亮。

→ 翻到第 2 页

---

## PPT 第 2 页：One review in, one countable record out

**A · 0:25**（讲完时累计 0:50）

屏幕上：左边是模型输出的 JSON，右边是 16 个固定方面（用到的三个有颜色）

> Our model turns each review into a record like this: the overall sentiment, and each aspect with the customer's own words.

> Aspects come from a fixed list of sixteen, so a program can count them.

提示：指一下右边三个彩色方块，对应左边 JSON 里的三个方面。

→ 翻到第 3 页

---

## PPT 第 3 页：Messy data, cleaned and labelled

**A · 0:35**（讲完时累计 1:25）

屏幕上：左边四层数字（62,774 → 54,472 → 2,425 → 2,228），右边两张卡：重复 23 次的模板、标签从 12 类改成 16 类

> We used 62,774 real shopping reviews, and the data is messy. One copy-pasted template appears twenty-three times.

> After cleaning, we sampled 2,425 reviews. A thirty-billion-parameter teacher model labelled them with our guideline. Clearer rules with sixteen aspects cut its errors from forty to fifteen, and a quality filter left 2,228 reviews.

提示："真实脏数据"是评分点，重复 23 次的模板一定要说到。

→ 翻到第 4 页

---

## PPT 第 4 页：A 30B teacher labels, a 1.7B student learns

**A · 0:35**（讲完时累计 2:00）

屏幕上：流程图：上面六个方框（样本 → 老师 → 过滤 → 划分 → 学生 → 调参），下面适配器分出三种用途

> Here is the whole system, all on one laptop. The teacher labels, the filter checks, and a 1.7-billion-parameter student learns with LoRA.

> We chose the best of ten versions on validation data only, then used it on the test set, on 100 reviews we labelled ourselves, and in the demo. Li Mingtai will explain the training.

提示：从左到右指着讲，最后一句交给 B。

→ 翻到第 5 页

---

## PPT 第 5 页：LoRA: train 1% of the weights

**B · 0:25**（讲完时累计 2:25）

屏幕上：左边 LoRA 示意图和公式 h = W0x + s·BAx，右边三个数字（1%、70 MB、94 min）

> Thank you. LoRA freezes the original weights and trains two small matrices, A and B.

> That is only one percent of the weights, a 70-megabyte file, and about an hour and a half of training on a laptop.

提示：公式不用念，指一下"W0 冻结、A 和 B 训练"。

→ 翻到第 6 页

---

## PPT 第 6 页：Tuning: the learning rate matters most

**B · 0:45**（讲完时累计 3:10）

屏幕上：左边调参柱状图（琥珀色是选中的 lr 5e-5，红色是 r = 32），右边三条结论

> We tuned one setting at a time on the validation set. A different random seed moves the score by about 0.02, so we only trust bigger gaps.

> The learning rate matters most: 5e-5 gave the best score, and all three of its seeds beat the default. A bigger rank was worse, because in MLX it also makes the update bigger. And training only the top eight layers halves the time.

提示："系统调参"是 Level 2 的关键，边讲边指琥珀色和红色的柱子。

→ 翻到第 7 页

---

## PPT 第 7 页：Near-teacher quality, a fifth of the memory

**B · 0:40**（讲完时累计 3:50）

屏幕上：左图测试集（0.513 → 0.734 → 0.801），右图人工标注（学生 0.701、老师 0.689），下面三个数字（5×、1.8×、0.59）

> On the test set, the score rises from 0.51 for the base model to 0.80 after tuning.

> On 100 new reviews that we labelled ourselves, our student scores 0.70 and the teacher 0.69. Statistically, they are the same, but the student needs a fifth of the memory. Now, let us show you.

提示：不要说"达到人类水平"。说完最后一句，A 切到浏览器。

→ 翻到第 8 页

---

## PPT 第 8 页：Live demo

**A 操作，B 讲 · 1:05**（讲完时累计 4:55）

屏幕上：这一页是演示截图（备用）；现场切到浏览器，第 1 个标签页停在页面顶部

*动作：A switches to browser tab 1, clicks example 1, then Analyze*

> This is running live. The same model answers twice. Without our adapter, it invents an aspect, flavour, which is not on our list. With the adapter, we get Taste and Price, both positive.

*动作：A switches to tab 2, the prepared report*

> And this is the report for 150 hotel reviews: 53 percent positive, and the top complaints are rooms and service.

> Scan the QR code to try it.

提示：左右两边先后出结果，B 等左边出来再讲左边。第 2 个标签页的 Hotel 报告要上台前生成好。出问题 15 秒内切备用视频。

→ 翻到第 9 页

---

## PPT 第 9 页：What we learned

**A，然后 B · 0:40**（讲完时累计 5:35）

屏幕上：三张卡片（Data beats model size / A laptop is enough / Measure honestly），下面一行三个困难，最后是 Thank you

*动作：A*

> Our main problems were overfitting, which we fixed by always keeping the best checkpoint, and running out of GPU memory, which we fixed by running one job at a time.

*动作：B*

> To sum up: a small model, fine-tuned on one laptop, scores about the same as its big teacher, with a fifth of the memory. Thank you. We are happy to take your questions.

提示：A 讲两个困难，B 收尾。

→ 进入问答（2 分钟）

---

## 彩排检查

- [ ] 用手机计时完整讲两遍，总长不超过 6 分钟；第 6 页（调参）和第 8 页（演示）最容易超时
- [ ] 第 4 页结尾 A 交给 B、第 7 页结尾切到浏览器、第 9 页 A 交给 B，这三处交接要顺
- [ ] 演示前已在第 2 个浏览器标签页生成好 Hotel 报告，第 1 个标签页停在页面顶部（见 demo_script.md）
- [ ] 问答准备见 qa_prep.md，两人各自熟悉自己主答的题
