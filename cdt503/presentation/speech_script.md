# 讲稿：Beyond Star Ratings（8 分钟版）

**A = Han Daiyuan，B = Li Mingtai。** 英文是要说的话（语速约每分钟 140 词），方括号里是动作，「提示」是给自己看的中文说明。
PPT 的演讲者备注里是同一份内容（`deck/speech.js` 一处修改，两边同步）。

| 页 | 标题 | 讲者 | 时长 | 累计 |
|---|---|---|---|---|
| 1 | Beyond Star Ratings | A | 0:30 | 0:30 |
| 2 | One review in, one countable record out | A | 0:40 | 1:10 |
| 3 | Messy data, cleaned and labelled | A | 0:55 | 2:05 |
| 4 | A 30B teacher labels, a 1.7B student learns | A | 0:45 | 2:50 |
| 5 | LoRA: train 1% of the weights | B | 0:40 | 3:30 |
| 6 | Tuning: the learning rate matters most | B | 1:10 | 4:40 |
| 7 | Near-teacher quality, a fifth of the memory | B | 1:00 | 5:40 |
| 8 | Live demo | A operates, B narrates | 1:20 | 7:00 |
| 9 | What we learned | A, then B | 0:40 | 7:40 |

目标总长 7:40，比 8 分钟上限留出约 20 秒余量。

---

## 1. Beyond Star Ratings

**A · 0:30**

> Good morning, everyone. We are Han Daiyuan and Li Mingtai, and our project is called Beyond Star Ratings.
>
> A star rating tells a shop whether a customer is happy, but not why. Look at this one hotel review: the location is great, but the room is noisy, and check-in took half an hour. That is three different signals in one sentence.
>
> We built a small model that pulls them out automatically.

提示：开场慢一点；说到三个信号时，用手指一下右边卡片上绿、红、红三处高亮。

---

## 2. One review in, one countable record out

**A · 0:40**

> This is what our model produces for that review: one JSON record. It gives the overall sentiment, then each aspect, the exact words the customer used, and whether they are positive or negative.
>
> The aspect must come from a fixed list of sixteen, shown on the right. That matters: because the names are fixed, a program can count them, and say for example that forty percent of this month's complaints are about logistics.

提示：右边三个彩色方块就是左边 JSON 里用到的三个方面，可以指一下对应关系。

---

## 3. Messy data, cleaned and labelled

**A · 0:55**

> We started from 62,774 real Chinese e-commerce reviews in ten product categories, and the data is genuinely messy. One copy-pasted template, "why are all my reviews the same", appears twenty-three times. Some texts start with invisible characters, some are duplicates, some are long rants.
>
> After cleaning, 54,472 remained, and we drew a sample of 2,425 balanced by category and sentiment.
>
> Instead of paying annotators, a thirty-billion-parameter teacher model labelled them, following our written guideline. Our first guideline had twelve overlapping aspects, and the teacher kept mixing them up. Rewriting it as sixteen aspects with clear rules cut the teacher's errors from forty to fifteen.
>
> Finally, a quality filter dropped labels that were not valid JSON or that contradicted the review's own star rating, which left 2,228 examples.

提示：这一页对应评分里的"真实脏数据"，一定要读出那个重复 23 次的模板。最后一句数字：2,228。

---

## 4. A 30B teacher labels, a 1.7B student learns

**A · 0:45**

> Here is the whole system, and every stage runs on one Apple M5 laptop with 32 gigabytes of memory.
>
> The teacher labels, the filter keeps the trustworthy labels, and we split them into training, validation and test sets. The student is Qwen3 with 1.7 billion parameters, fine-tuned with LoRA. We ran ten training runs and chose the final adapter on the validation set only.
>
> That single 70-megabyte adapter is then used three ways: once on the held-out test set, on 100 new reviews that we labelled ourselves, and in the live demo. Li Mingtai will now explain the training.

提示：从左到右、从上到下讲；最后一句是交接给 B，B 接着站过来。

---

## 5. LoRA: train 1% of the weights

**B · 0:40**

> Thanks. Fine-tuning all 1.7 billion weights would not fit on a laptop. LoRA keeps the original weights frozen and adds a thin side path: two small matrices, A and B, whose product is added to the output.
>
> Only those are trained: 17 million weights, about one percent. The result is a 70-megabyte file, and one training run takes about an hour and a half.
>
> We also compute the loss only on the answer, not on the long instruction prompt, so the model learns to write the JSON instead of repeating the rules.

提示：公式不用逐个字母念，指一下"W0 冻结、A 和 B 训练"就够了。

---

## 6. Tuning: the learning rate matters most

**B · 1:10**

> Next, we tuned the model systematically: one factor at a time, judged only on the validation set.
>
> First, how much does chance matter? Retraining the same setting with a different random seed moves the score by up to about 0.02, so we only trust bigger gaps.
>
> Three findings. One: the learning rate matters most. Halving it to 5e-5 gave the best score, 0.793, and all three seeds of that setting beat the default. Doubling it made training diverge within forty steps.
>
> Two: a bigger rank is not better. Rank 32 dropped to 0.697. In MLX the update is multiplied by a fixed scale, so a bigger rank also means a bigger update. When we halved the scale, rank 32 recovered to 0.766.
>
> Three: training only the top eight layers gives the same quality in half the time.

提示：这一页是 Level 2"系统调参"的关键，讲慢一点。琥珀色那根是选中的配置，红色那根是 rank 32。

---

## 7. Near-teacher quality, a fifth of the memory

**B · 1:00**

> Here are the results. On the 262 held-out test reviews, the base model scores 0.513, LoRA with default settings 0.734, and the tuned model 0.801 on average over three seeds. Valid outputs go from about 91 to almost 100 percent.
>
> On the right is the more honest test: 100 reviews that no model had seen, labelled by the two of us. Our student scores 0.701 and the thirty-billion-parameter teacher 0.689: statistically indistinguishable. And the student needs about a fifth of the memory and is almost twice as fast.
>
> We also tried the cheap alternative, simply showing the base model four examples. That only reaches 0.59. Now let us show you.

提示：不要说"达到人类水平"，也不要说"小 17 倍"。说"statistically indistinguishable"和"a fifth of the memory"。

---

## 8. Live demo

**A operates, B narrates · 1:20**

> This is running live on this laptop. It is the same 1.7B model on both sides: on the left without our adapter, on the right with it.
>
> [A clicks example 1, then Analyze] A customer says the fruit is great and cheaper than the supermarket. The base model reads it first, and it invents its own aspect name, flavour, which is not on our list, so a program cannot use it. Now the same model with our adapter: Taste and Price, both positive, highlighted in the text.
>
> [A clicks example 4] One hotel review, three signals: location good, room bad, service bad.
>
> [A switches to the prepared report tab] And this is what a shop owner would see: 150 hotel reviews the model has never seen. 53 percent positive, where the star ratings say 55, and the top complaints are rooms and service, each with the customers' own words.
>
> You can try single reviews on your phone: just scan the QR code.

提示：上台前在另一个浏览器标签页生成好 Hotel 报告（约 2 分钟），别刷新。出问题 15 秒内切备用视频，不要现场调试。详见 demo_script.md。

---

## 9. What we learned

**A, then B · 0:40**

> [A] A few things went wrong along the way. In the second epoch the model started to memorise, so the best checkpoint was never the last one. The teacher and the demo together ran out of GPU memory, so we ran one job at a time and made everything resumable. And our long prompt slowed inference from 0.34 to 0.58 seconds per review.
>
> [B] To sum up: a 1.7B model, 1,800 teacher-labelled reviews and one laptop give valid JSON almost every time, and the model is statistically indistinguishable from its 30B teacher against human labels, at a fifth of the memory. Most of what we learned was about data: clear labels, a quality filter, and honest evaluation. Thank you, and we are happy to take questions.

提示：A 讲挑战（右边卡片），B 讲结论（左边三点）并收尾。问答准备见 qa_prep.md。

---

## 彩排检查

- [ ] 用手机计时完整讲两遍，总长不超过 8 分钟；第 6 页（调参）最容易超时
- [ ] 第 4 页结尾 A 交给 B、第 8 页演示、第 9 页 A 交给 B，这三处交接要顺
- [ ] 演示前已在另一个浏览器标签页生成好 Hotel 报告（见 demo_script.md）
- [ ] 问答准备见 qa_prep.md，两人各自熟悉自己主答的题
