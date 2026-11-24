# 讲稿：Beyond Star Ratings（8 分钟版，Han Daiyuan）

Han Daiyuan：第 1–5 页，约 3:25。Li Mingtai：第 6–9 页，约 4:05。全程约 7:30。

每页先是整段英文，再是整段中文。问答准备在最后（每题标了主答人）；完整的 22 题见 qa_prep.md。

## 第一部分：Han Daiyuan（第 1–5 页，约 3:25）

### 第 1 页 · Beyond Star Ratings（约 0:30）

Good morning. We are Han Daiyuan and Li Mingtai, and our project is Beyond Star Ratings. A star rating tells a shop whether a customer is happy, but not why. This one hotel review has three signals: a good location, a noisy room, and a slow check-in. Our model finds them automatically.

> 大家早上好。我们是 Han Daiyuan 和 Li Mingtai，我们的项目叫 Beyond Star Ratings。星级评分能告诉商家顾客满不满意，却说不出原因。比如这一条酒店评论里就有三个信号：位置好、房间吵、入住慢。我们的模型能自动把它们找出来。

### 第 2 页 · One review in, one countable record out（约 0:35）

For that review, our model writes this record. It gives the overall sentiment. Then, for each aspect, it gives the customer's own words, and whether they are positive or negative. Every aspect must come from this fixed list of sixteen. Because the names are fixed, a program can count them, for example, how many complaints this month are about logistics.

> 对这条评论，模型会输出这样一条记录：先给出整体情感，然后对每个方面，给出顾客的原话，以及是好评还是差评。每个方面都必须来自这张固定的 16 项清单。名称固定了，程序就能统计，比如这个月有多少差评是关于物流的。

### 第 3 页 · Messy data, cleaned and labelled（约 0:50）

We used 62,774 real Chinese shopping reviews from ten categories, and the data is messy. One copy-pasted template appears twenty-three times. There are also duplicates, invisible characters, and very long rants. After cleaning, we sampled 2,425 reviews, balanced by category and sentiment. A thirty-billion-parameter teacher model labelled them, using our written guideline. Our first guideline had twelve overlapping aspects. Clearer rules with sixteen aspects cut the teacher's errors from forty to fifteen. A quality filter then removed doubtful labels, which left 2,228 reviews.

> 我们用了 62,774 条真实的中文网购评论，来自十个类目，数据很脏。有一条复制粘贴的模板出现了 23 次，还有重复评论、看不见的字符和特别长的抱怨。清洗之后，我们按类目和好差评均衡地抽了 2,425 条，由一个 300 亿参数的老师模型按照我们写的标注规则来标注。第一版规则有 12 个互相重叠的方面。改成 16 个方面、把规则写清楚之后，老师模型的错误从 40 个降到 15 个。最后用质量过滤去掉可疑的标注，剩下 2,228 条。

### 第 4 页 · A 30B teacher labels, a 1.7B student learns（约 0:50）

Here is the whole system, and it all runs on one Apple laptop. The teacher labels, the filter checks, and we split the data into training, validation, and test sets. The student is a 1.7-billion-parameter Qwen model with LoRA. We trained ten versions and chose the best one on validation data only. That one 70-megabyte adapter is used three times: on the test set, on 100 new reviews that we labelled ourselves, and in the live demo.

> 这是整个系统，全部在一台苹果笔记本上运行。老师模型负责标注，过滤器负责把关，然后我们把数据分成训练集、验证集和测试集。学生模型是 17 亿参数的 Qwen，用 LoRA 微调。我们训练了十个版本，只用验证集挑出最好的一个。这一个 70 MB 的适配器用在三个地方：测试集、我们自己标注的 100 条新评论，以及现场演示。

### 第 5 页 · LoRA: train 1% of the weights（约 0:40）

How can a laptop train the student? Training all 1.7 billion weights would not fit. LoRA freezes the original weights, W-zero, and adds two small matrices, A and B. Only these two are trained. That is about one percent of the weights, a 70-megabyte file, and about an hour and a half of training. Next, Li Mingtai will show how we tuned it and what we found.

> 一台笔记本怎么训练学生模型？17 亿个权重全部训练是放不下的。LoRA 把原来的权重 W0 冻结，在旁边加两个小矩阵 A 和 B，只训练这两个。这只占全部权重的 1% 左右，是一个 70 MB 的文件，训练大约一个半小时。接下来由 Li Mingtai 介绍我们怎么调参，以及得到了什么结果。

## 问答准备

### Q1（主答：Han Daiyuan）

**Q:** Your training labels come from another model. Isn't the student just copying the teacher's mistakes?

**A:** Partly, yes. That is the main limit of distillation. We reduced it in two ways. A quality filter removed labels that contradicted the human star rating, 182 of 2,425. And we tested on 100 reviews labelled by us, not by the teacher. There, the student is statistically the same as the teacher, so it did not pick up noticeably more errors.

> **问：** 训练标签来自另一个模型，学生模型不就是在照搬老师的错误吗？
>
> **答：** 部分是的，这是蒸馏的主要局限。我们用两种方法降低影响。一是质量过滤，去掉和人工星级矛盾的标注，2,425 条里去掉了 182 条。二是在我们自己标注、而不是老师标注的 100 条评论上测试。在那里，学生和老师统计上没有差别，说明它没有多学到明显的错误。

### Q2（主答：Han Daiyuan）

**Q:** Your two annotators agreed at only 0.644. Are the human labels reliable?

**A:** That number shows that some aspects are hard to tell apart, for example whether "the colour runs after washing" is about build quality or performance. So we discussed every disagreement and agreed on final labels. On the same 20 reviews, the student agrees with us at 0.66 and the teacher at 0.69. With only 20 reviews we do not claim the models reach human level, only that both are far above the base model.

> **问：** 你们两个标注者的一致性只有 0.644，人工标注可靠吗？
>
> **答：** 这个数字说明有些方面本来就难区分，比如“洗了掉色”算做工还是使用效果。所以我们逐条讨论了分歧，商定了最终标注。在同样的 20 条上，学生模型和我们的一致性是 0.66，老师是 0.69。只有 20 条样本，所以我们不说模型达到了人类水平，只说两者都远高于原始模型。

### Q3（主答：Han Daiyuan）

**Q:** What is LoRA, in one sentence?

**A:** LoRA keeps the original weights frozen and learns a small low-rank update beside them, so we train only 17 million of 1.7 billion parameters, about one percent.

> **问：** 用一句话解释 LoRA？
>
> **答：** LoRA 保持原有权重不变，在旁边学习一个很小的低秩更新，所以 17 亿参数里我们只训练了 1,700 万个，大约 1%。

### Q4（主答：Li Mingtai）

**Q:** How do you know the differences between settings are not just random?

**A:** We trained the default setting twice and the final setting three times, with different random seeds. Chance alone moved the score by up to about 0.02, so we treat smaller gaps as ties. The learning-rate result is bigger than that: all three seeds of 5e-5 beat both seeds of the default.

> **问：** 你们怎么知道不同设置之间的差别不是随机造成的？
>
> **答：** 我们用不同的随机种子，把默认设置训练了两次、最终设置训练了三次。光是随机性就能让分数变动约 0.02，所以比这小的差距我们都当作打平。学习率的效果比这大：5e-5 的三个种子都超过了默认设置的两个种子。

### Q5（主答：Li Mingtai）

**Q:** Why did the learning rate 2e-4 fail?

**A:** The steps were too big from the start. We used a constant learning rate with no warm-up, and MLX also multiplies the update by a fixed scale of 20. Within 40 steps the validation loss jumped from 2.6 to 7.1, and the model only printed repeated punctuation. A warm-up might help, but we did not test it. Halving the rate to 5e-5 gave our best result instead.

> **问：** 为什么学习率 2e-4 会训练失败？
>
> **答：** 一开始步子就太大了。我们用的是恒定学习率、没有预热，而且 MLX 还会把更新乘上固定的系数 20。40 步之内验证损失从 2.6 跳到 7.1，模型只会输出重复的标点。加预热也许有用，但我们没有测试。我们改为把学习率减半到 5e-5，反而得到了最好的结果。

### Q6（主答：Li Mingtai）

**Q:** How does the demo show both models without loading two models?

**A:** LoRA's output is the original output plus a small extra term. If we set its scale to zero, the adapter is switched off, and the same model in memory behaves exactly like the base model. We switch it for each request, so we only need memory for one model.

> **问：** 演示里怎么不加载两个模型就能同时展示两种结果？
>
> **答：** LoRA 的输出等于原来的输出再加上一个小的额外项。把它的系数设成 0，适配器就关掉了，内存里同一个模型就和原始模型完全一样。我们每个请求切换一次，所以只需要一个模型的内存。
