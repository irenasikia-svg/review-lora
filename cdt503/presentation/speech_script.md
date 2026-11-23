# 讲稿：Beyond Star Ratings（8 分钟版，按 PPT 页码）

**A = Han Daiyuan，B = Li Mingtai。** 每一节对应 PPT 的一页。引用块里的英文是要说的话，*动作* 不念出来，「提示」是给自己看的中文说明。
语速按每分钟约 99 个英文词写（比平时说话慢一些）；每页讲完停一拍再翻页。PPT 每页的演讲者备注里是同一份内容（改 `deck/speech.js` 一处，两边同步）。

| PPT 页码 | 标题 | 讲者 | 时长 | 累计 | 字数 |
|---|---|---|---|---|---|
| 第 1 页 | Beyond Star Ratings | A | 0:30 | 0:30 | 52 词 |
| 第 2 页 | One review in, one countable record out | A | 0:35 | 1:05 | 60 词 |
| 第 3 页 | Messy data, cleaned and labelled | A | 0:50 | 1:55 | 83 词 |
| 第 4 页 | A 30B teacher labels, a 1.7B student learns | A | 0:50 | 2:45 | 84 词 |
| 第 5 页 | LoRA: train 1% of the weights | B | 0:40 | 3:25 | 69 词 |
| 第 6 页 | Tuning: the learning rate matters most | B | 1:00 | 4:25 | 104 词 |
| 第 7 页 | Near-teacher quality, a fifth of the memory | B | 0:55 | 5:20 | 94 词 |
| 第 8 页 | Live demo | A 操作，B 讲 | 1:15 | 6:35 | 97 词 |
| 第 9 页 | What we learned | A，然后 B | 0:55 | 7:30 | 99 词 |

总长 7:30，共 742 词，比 8 分钟上限留出约 0:30 余量。

---

## PPT 第 1 页：Beyond Star Ratings

**A · 0:30**（讲完时累计 0:30）

屏幕上：标题、三颗实心两颗空心的星星、右边一条酒店评论（绿、红、红三处高亮）

> Good morning. We are Han Daiyuan and Li Mingtai, and our project is Beyond Star Ratings.

> A star rating tells a shop whether a customer is happy, but not why. This one hotel review has three signals: a good location, a noisy room, and a slow check-in.

> Our model finds them automatically.

提示：开场慢一点。说到三个信号时，依次指右边卡片上的绿、红、红三处高亮。

→ 翻到第 2 页

---

## PPT 第 2 页：One review in, one countable record out

**A · 0:35**（讲完时累计 1:05）

屏幕上：左边是模型输出的 JSON，右边是 16 个固定方面（用到的三个有颜色）

> For that review, our model writes this record. It gives the overall sentiment. Then, for each aspect, it gives the customer's own words, and whether they are positive or negative.

> Every aspect must come from this fixed list of sixteen. Because the names are fixed, a program can count them, for example, how many complaints this month are about logistics.

提示：右边三个彩色方块就是左边 JSON 里的三个方面，可以指一下对应关系。

→ 翻到第 3 页

---

## PPT 第 3 页：Messy data, cleaned and labelled

**A · 0:50**（讲完时累计 1:55）

屏幕上：左边四层数字（62,774 → 54,472 → 2,425 → 2,228），右边两张卡：重复 23 次的模板、标签从 12 类改成 16 类

> We used 62,774 real Chinese shopping reviews from ten categories, and the data is messy. One copy-pasted template appears twenty-three times. There are also duplicates, invisible characters, and very long rants.

> After cleaning, we sampled 2,425 reviews, balanced by category and sentiment. A thirty-billion-parameter teacher model labelled them, using our written guideline.

> Our first guideline had twelve overlapping aspects. Clearer rules with sixteen aspects cut the teacher's errors from forty to fifteen. A quality filter then removed doubtful labels, which left 2,228 reviews.

提示：这一页对应评分里的"真实脏数据"。读数字时一个一个读清楚，不用赶。

→ 翻到第 4 页

---

## PPT 第 4 页：A 30B teacher labels, a 1.7B student learns

**A · 0:50**（讲完时累计 2:45）

屏幕上：流程图：上面六个方框（样本 → 老师 → 过滤 → 划分 → 学生 → 调参），下面适配器分出三种用途

> Here is the whole system, and it all runs on one Apple laptop. The teacher labels, the filter checks, and we split the data into training, validation, and test sets.

> The student is a 1.7-billion-parameter Qwen model with LoRA. We trained ten versions and chose the best one on validation data only.

> That one 70-megabyte adapter is used three times: on the test set, on 100 new reviews that we labelled ourselves, and in the live demo. Li Mingtai will now explain the training.

提示：从左到右、从上到下指着讲。最后一句交给 B，B 接着站过来。

→ 翻到第 5 页

---

## PPT 第 5 页：LoRA: train 1% of the weights

**B · 0:40**（讲完时累计 3:25）

屏幕上：左边 LoRA 示意图和公式 h = W0x + s·BAx，右边三个数字（1%、70 MB、94 min）

> Thank you. Training all 1.7 billion weights would not fit on a laptop. LoRA freezes the original weights, W-zero, and adds two small matrices, A and B. Only these two are trained.

> That is about one percent of the weights, a 70-megabyte file, and about an hour and a half of training. We also compute the loss only on the answer, so the model learns to write the JSON.

提示：公式不用逐个字母念，指一下"W0 冻结、A 和 B 训练"就够了。

→ 翻到第 6 页

---

## PPT 第 6 页：Tuning: the learning rate matters most

**B · 1:00**（讲完时累计 4:25）

屏幕上：左边调参柱状图（琥珀色是选中的 lr 5e-5，红色是 r = 32），右边三条结论

> Next, we tuned the model one setting at a time, using only the validation set. First, how much is just luck? With a different random seed, the score moves by about 0.02. So we only trust bigger gaps.

> Three findings. One: the learning rate matters most. 5e-5 gave the best score, 0.793, and all three of its seeds beat the default.

> Two: a bigger rank is not better. Rank 32 dropped to 0.697, because in MLX a bigger rank also means a bigger update. Fixing the scale brought it back.

> Three: training only the top eight layers takes half the time, with similar quality.

提示：这一页是 Level 2"系统调参"的关键。三条结论之间各停一拍，边讲边指图上对应的柱子。

→ 翻到第 7 页

---

## PPT 第 7 页：Near-teacher quality, a fifth of the memory

**B · 0:55**（讲完时累计 5:20）

屏幕上：左图测试集（0.513 → 0.734 → 0.801），右图人工标注（学生 0.701、老师 0.689），下面三个数字（5×、1.8×、0.59）

> Here are the results. On 262 test reviews, the base model scores 0.51. LoRA with default settings scores 0.73, and the tuned model 0.80, averaged over three seeds. Almost every output is now valid JSON.

> On the right is a harder test: 100 new reviews that we labelled ourselves. Our student scores 0.70, and the thirty-billion-parameter teacher 0.69. Statistically, they are the same.

> But the student needs about a fifth of the memory, and it is almost twice as fast. Just giving the base model examples only reaches 0.59. Now, let us show you.

提示：不要说"达到人类水平"，也不要说"小 17 倍"。说完最后一句，A 切到浏览器。

→ 翻到第 8 页

---

## PPT 第 8 页：Live demo

**A 操作，B 讲 · 1:15**（讲完时累计 6:35）

屏幕上：这一页是演示截图（备用）；现场切到浏览器，第 1 个标签页停在页面顶部

*动作：A switches to browser tab 1*

> This is running live on this laptop. The same model answers twice: on the left without our adapter, on the right with it.

*动作：A clicks example 1, then Analyze*

> A customer says the fruit is great and cheap. The base model invents its own aspect, flavour, which is not on our list. With our adapter, we get Taste and Price, both positive.

*动作：A switches to tab 2, the prepared report*

> And this is the report a shop owner would see for 150 hotel reviews. 53 percent are positive, close to the star ratings, and the top complaints are rooms and service.

> You can try it yourself. Just scan the QR code.

提示：点 Analyze 后左右两边是先后出结果的，B 等左边出来再讲左边、等右边出来再讲右边，不要抢话。上台前在第 2 个标签页生成好 Hotel 报告（约 2 分钟），别刷新。出问题 15 秒内切备用视频。详见 demo_script.md。

→ 翻到第 9 页

---

## PPT 第 9 页：What we learned

**A，然后 B · 0:55**（讲完时累计 7:30）

屏幕上：三张卡片（Data beats model size / A laptop is enough / Measure honestly），下面一行三个困难，最后是 Thank you

*动作：A*

> We hit a few problems. In the second epoch the model started to memorise, so we always keep the checkpoint with the best validation loss. Running the teacher and the demo together ran out of memory, so we run one job at a time. And our long prompt made inference slower.

*动作：B*

> To sum up: a small model, fine-tuned on one laptop, scores about the same as its big teacher on human labels, with a fifth of the memory. Our main lesson is that clean data matters more than model size. Thank you. We are happy to take your questions.

提示：A 讲下面一行的三个困难，B 讲上面三张卡片的结论并收尾。问答准备见 qa_prep.md。

→ 进入问答（2 分钟）

---

## 彩排检查

- [ ] 用手机计时完整讲两遍，总长不超过 8 分钟；第 6 页（调参）和第 8 页（演示）最容易超时
- [ ] 第 4 页结尾 A 交给 B、第 7 页结尾切到浏览器、第 9 页 A 交给 B，这三处交接要顺
- [ ] 演示前已在第 2 个浏览器标签页生成好 Hotel 报告，第 1 个标签页停在页面顶部（见 demo_script.md）
- [ ] 问答准备见 qa_prep.md，两人各自熟悉自己主答的题
