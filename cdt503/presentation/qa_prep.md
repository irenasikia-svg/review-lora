# 问答准备：21 个可能被问到的问题

每题：**英文回答**（30 秒内能说完）+ 中文解释（帮你们理解，不用背）。
按主题分组；建议 Han Daiyuan 主答 1–10（数据、方法），Li Mingtai 主答 11–21（训练、结果、部署），另一位补充。

不会的题：先承认，再说你知道的相关部分——"We didn't test that directly, but what we did see is …"。不要编数字。

---

## 数据与标签

**1. Why not just use the 30B teacher directly?**
> It works, but it is expensive to run. Its weights take 17.2 GB versus 3.5 GB for our student — about 5× — and at the same batch size it is 1.8× slower per review. It has 18× more parameters in total, although as a mixture-of-experts model it only activates 3.3B per token, under 2× our 1.7B. Against human labels on 100 unseen reviews the two are statistically indistinguishable (0.701 vs 0.689 aspect-F1), so for a shop processing thousands of reviews a day the small model is the practical choice.

中文：老师权重内存约 5 倍、速度慢 1.8 倍；总参数 18 倍，但混合专家每次只激活 3.3B，不到学生的 2 倍——所以别说"小 17 倍"。人工评估上两者统计上分不出高低。

**2. Your training labels come from another model. Isn't the student just copying the teacher's mistakes?**
> Partly, yes — that's the main limitation of distillation. We reduced it in two ways: a quality filter that drops labels contradicting the human star rating (182 of 2,425), and an evaluation against *human* labels on 100 reviews no model had seen. There the student is statistically indistinguishable from the teacher, so it didn't inherit noticeably more errors.

中文：承认这个局限，然后讲两个应对：过滤 + 人工评估。

**3. Why did you filter out reviews where the teacher's sentiment disagreed with the dataset label? Doesn't that make the test set easier?**
> Yes, and we say so in the report. That's exactly why we added the fresh human-labelled set: sentiment accuracy there is 0.90, lower than 0.97 on the filtered test set. The filter makes training data cleaner; the fresh set gives an honest estimate.

中文：过滤让训练数据干净，但测试集偏简单——所以才另外做了全新的人工评估集。

**4. How did you choose the 16 aspects?**
> We started with 12 generic e-commerce aspects and looked at where the models got confused. "Quality" mixed up build quality, defects and authenticity, so we split it, used the words people actually write, and added nine disambiguation rules. We checked the new schema was clearer by having a second model label the same reviews: agreement with the teacher rose from 0.768 to 0.806.

中文：先用通用方面，看哪里混淆，再拆分 + 加规则，用"第二个标注者的一致性"证明更清楚了。

**5. Your two annotators only agreed at 0.644 F1. Doesn't that make the human labels unreliable?**
> It shows the boundaries between some aspects are hard — for example, is "the colour runs after washing" about build quality or performance? That's why we adjudicated: we discussed the disagreeing items and agreed on final labels. For a fair comparison we also scored the models against each annotator's original labels on those same 20 reviews: annotator B agrees with A at 0.644, the student at 0.661 and the teacher at 0.693. With only 20 reviews the intervals overlap, so we don't claim the models are at, above or below human level — only that both are far above the base model at 0.419.

中文：一致性低说明有些方面边界难分，所以做了仲裁。公平比较（同样 20 条、同样拿某个人的原始标注当参照）：人 0.644、学生 0.661、老师 0.693、原始模型 0.419。样本只有 20 条，区间重叠，**不要说"学生达到人类水平"**，只说"都远高于原始模型"。另外 100 条里 80 条只有一个人标。

**6. Why not a classic BERT-style classifier for ABSA?**
> A classifier needs a separate output head per aspect and human-labelled training data, and it can't copy the opinion phrase. A generative model outputs the whole structure — aspects, sentiments and opinion spans — in one pass, and we could train it from teacher labels without human annotation. A BERT baseline would be a good comparison for future work.

中文：生成式模型一次输出完整结构，还能用老师标注训练；BERT 对比可以作为未来工作。

## 方法

**7. What exactly is LoRA, in one sentence?**
> LoRA freezes the original weight matrix W₀ and learns a low-rank update BA beside it, so the layer computes W₀x + s·BAx; we train only 17.4 million of 1.7 billion parameters, about 1%.

中文：原权重不动，旁边加两个小矩阵，只训练这 1%。

**8. Why compute the loss only on the answer?**
> The 780-token prompt is identical for every example. Training on it would waste capacity on memorising the instructions and dilute the signal from the part that actually varies — the JSON answer.

中文：提示词每条都一样，学它没意义，还会冲淡答案部分的信号。

**9. How do you know you didn't overfit to the test set?**
> All tuning used the 142-review validation set. Each model was scored on the 262-review test set exactly once, after the configuration was fixed. And the fresh human-labelled set was drawn from reviews never used anywhere.

中文：调参只看验证集；测试集只跑一次；人工集是全新的。

**10. What does the 95% confidence interval mean here?**
> We resampled the test reviews 2,000 times with replacement and recomputed F1 each time. For the tuning gain, 95% of the resamples fall between +0.038 and +0.110, so it is unlikely to be luck in *which reviews were tested*. One caveat: each model was trained only once, so the interval doesn't include training randomness — retraining with another seed moved validation F1 by about 0.01.

中文：自助法重抽样 2000 次；区间不含 0。但要主动说明：每个模型只训练了一次，区间只反映"测试样本的随机性"，不包括"训练的随机性"（换种子验证集 F1 变化约 0.01）。

## 训练与调参

**11. Why did the learning rate of 2e-4 diverge?**
> The updates were too large from the very first steps. We used a constant learning rate with no warm-up, so the model took full-size steps immediately; and in MLX the LoRA update is also multiplied by a fixed scale of 20. Validation loss jumped from 2.6 to 7.1 within 40 steps and the model started emitting repeated punctuation, and it never recovered. A warm-up phase might have rescued it, but we didn't test that; halving the rate to 5e-5 instead gave our best result.

中文：一开始就步子太大：学习率恒定、没有预热，第一步就是全速；MLX 还要乘 scale=20。第 40 步验证损失 2.6 → 7.1，输出变成重复标点，再没恢复。加预热也许能救回来，但我们没测——别说"肯定能"。

**12. Why is rank 32 worse than rank 16? Shouldn't more capacity help?**
> In MLX the update is multiplied by a fixed scale, not α/r as in the original LoRA paper, so doubling the rank also enlarges the update. When we halved the scale to keep α constant, rank 32 recovered from 0.697 to 0.766 — within noise of the default. So the problem was update size, not rank.

中文：固定 scale 下 rank 越大更新越大；把 scale 按 α/r 调回去就恢复了——用实验验证了这个解释。

**13. How do you know the differences between configurations aren't just random?**
> We ran the default configuration twice with different random seeds: validation F1 was 0.758 and 0.747. That ~0.01 spread is our noise level, shown as a grey band in the chart. Learning rate 5e-5 is 0.035 above the default — about three times that spread — and the test-set gain has a confidence interval excluding zero. Also, the validation set has only 142 reviews, so we only trust large differences; small ones like rank 8 vs 16 we treat as ties.

中文：换种子跑两次，波动约 0.01；验证集只有 142 条，所以只相信大差异，小差异一律当成打平。

**14. You only changed one factor at a time. What about interactions?**
> True — that's a stated limitation. A full grid of 4 ranks × 3 learning rates × 3 layer settings would be 36 runs, about 56 hours on our laptop. One-factor-at-a-time needed only 7 new runs, plus 2 diagnostic runs (a second seed and the rank-32 scale check). The natural next experiment is combining the two best settings: learning rate 5e-5 with rank 4.

中文：全组合要 56 小时，单因素只要 7 组（另加 2 组诊断实验）；下一步可以试 lr 5e-5 + r=4 组合。

**15. How did you pick the checkpoint?**
> We saved a checkpoint every 40 steps and picked the one with the lowest validation loss. The last checkpoint was never the best in any converged run — at the start of the second epoch, training loss halves while validation loss stays flat, which is the model starting to memorise.

中文：每 40 步存一次，按验证损失挑；第二轮开始训练损失骤降、验证不降，就是过拟合信号。

## 结果与部署

**16. Why is the human-evaluation F1 (0.70) lower than the test-set F1 (0.81)?**
> Two reasons: the test reference comes from the teacher, so it rewards agreeing with the teacher's style; and the test set only contains reviews where the teacher agreed with the human rating, which are easier. The human set is harder and more realistic — and there the student is still statistically indistinguishable from the teacher.

中文：参照标准不同 + 测试集偏简单；人工集更真实。

**17. How fast is it, and could it run in production?**
> About 0.6–0.75 seconds per review in batches on a laptop (the teacher takes 1.37 s at the same batch size), and about 4 seconds per request in the demo because it runs both models. The adapter is only 70 MB. A known bottleneck is the 780-token prompt; since the student has learned the rules, a much shorter prompt should make it faster.

中文：笔记本上每条约 0.6 秒；演示约 4 秒是因为跑了两个模型；缩短提示词还能更快。

**18. How does the demo show both models without loading two models?**
> LoRA's output is the original output plus s·BAx. Setting the scale s to zero switches every adapter off, so the same model in memory behaves exactly like the base model. We flip it per request, which halves memory use.

中文：把 scale 设成 0 就等于关掉 LoRA，所以内存里只要一份模型。

**19. What was the hardest problem you faced?**
> Not the model — the data. Our first label schema was ambiguous, and no amount of training fixed errors caused by overlapping definitions. Practically, memory was also hard: the 17 GB teacher plus the demo crashed the GPU, so we had to schedule jobs one at a time and make training resumable.

中文：最难的是数据和标签定义；工程上是显存不够。

**20. If you had another month, what would you do?**
> Three things: try combined settings like learning rate 5e-5 with rank 4; shorten the prompt now that the rules are learned, to speed up inference; and label a larger human evaluation set, especially for rare aspects like Location and Packaging that appear fewer than five times in our 100 reviews.

中文：组合调参、缩短提示词、扩大人工评估集（特别是稀有方面）。

**21. Couldn't you just give the small model a few examples instead of fine-tuning it?**
> We tested exactly that: the base 1.7B model with the same four worked examples the teacher sees. On the validation set aspect-F1 rose only from 0.538 to 0.594, and its invalid-output rate stayed at 8.5%. LoRA reached 0.802 with no invalid outputs. A few examples don't teach a small model to follow a 16-aspect schema reliably; training on 1,800 examples does — at the same inference cost.

中文：做过这个对照（少样本提示）：原始模型给 4 个示例，验证集 F1 只从 0.538 到 0.594，格式错误率还是 8.5%；LoRA 是 0.802、零错误，而且推理成本一样。

---

## 关键数字速查（被追问时用）

| 项目 | 数字 |
|---|---|
| 原始数据 / 清洗后 / 抽样 / 保留 | 62,774 / 54,472 / 2,425 / 2,228 |
| 训练 / 验证 / 测试 | 1,824 / 142 / 262 |
| 可训练参数 | 17.4M / 1,720M（1.01%），适配器 70 MB |
| 训练时间 | 480 步约 94 分钟（M5，32 GB） |
| 测试集方面 F1 | 原始 0.513 → 默认 LoRA 0.734 → 调参后 0.807 |
| 调参提升 | +0.073，95% 区间 [+0.038, +0.110] |
| 人工评估方面 F1 | 原始 0.458 / 学生 0.701 / 老师 0.689 |
| 组员一致性 | 0.644（20 条共同标注，仲裁前；100 条里另 80 条只有一人标） |
| 公平对比（同 20 条，对各人原始标注的平均） | 组员 B 0.644 / 学生 0.661 / 老师 0.693 / 原始 0.419（区间重叠） |
| 少样本对照（验证集） | 原始 0.538 → 给 4 个示例 0.594；LoRA 0.802 |
| 成本（老师 vs 学生，批大小 8） | 权重 17.2 vs 3.5 GB（4.9×），峰值 19.8 vs 5.7 GB（3.5×），1.37 vs 0.75 秒/条（1.8×） |
| 参数（老师 vs 学生） | 总 30.5B vs 1.74B（18×），激活 3.3B vs 1.74B（1.9×） |
| 训练次数 | 每个配置只训练一次（单种子） |
| 种子波动 | 0.747–0.758 |
| lr 2e-4 | 第 40 步发散，验证损失 2.6 → 7.1 |
| r=32 | 0.697 → scale 改 10 后 0.766 |
| 只训练顶部 8 层 | 0.749，训练 46 分钟 |
