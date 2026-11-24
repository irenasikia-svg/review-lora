# 讲稿：Beyond Star Ratings（6 分钟版，Han Daiyuan）

Han Daiyuan：第 1–5 页，约 2:25。Li Mingtai：第 6–9 页，约 3:10。全程约 5:35。

每页先英文、后中文对照。完整的问答准备见 qa_prep.md。

## 第一部分：Han Daiyuan（第 1–5 页，约 2:25）

### 第 1 页 · Beyond Star Ratings（约 0:25）

Good morning. We are Han Daiyuan and Li Mingtai.

> 大家早上好，我们是 Han Daiyuan 和 Li Mingtai。

A star rating says whether a customer is happy, but not why. This hotel review has three signals: a good location, a noisy room, and a slow check-in. Our model finds them automatically.

> 星级评分能说明顾客满不满意，却说不出原因。这条酒店评论里有三个信号：位置好、房间吵、入住慢。我们的模型能自动把它们找出来。

### 第 2 页 · One review in, one countable record out（约 0:25）

Our model turns each review into a record like this: the overall sentiment, and each aspect with the customer's own words.

> 模型会把每条评论变成这样一条记录：整体情感，以及每个方面和顾客的原话。

Aspects come from a fixed list of sixteen, so a program can count them.

> 方面都来自一张固定的 16 项清单，所以程序可以直接统计。

### 第 3 页 · Messy data, cleaned and labelled（约 0:35）

We used 62,774 real shopping reviews, and the data is messy. One copy-pasted template appears twenty-three times.

> 我们用了 62,774 条真实的网购评论，数据很脏，有一条复制粘贴的模板出现了 23 次。

After cleaning, we sampled 2,425 reviews. A thirty-billion-parameter teacher model labelled them with our guideline. Clearer rules with sixteen aspects cut its errors from forty to fifteen, and a quality filter left 2,228 reviews.

> 清洗之后我们抽了 2,425 条，由 300 亿参数的老师模型按我们的规则标注。改成 16 个方面、规则写清楚之后，它的错误从 40 个降到 15 个，质量过滤后剩下 2,228 条。

### 第 4 页 · A 30B teacher labels, a 1.7B student learns（约 0:35）

Here is the whole system, all on one laptop. The teacher labels, the filter checks, and a 1.7-billion-parameter student learns with LoRA.

> 这是整个系统，全部在一台笔记本上运行。老师模型标注，过滤器把关，17 亿参数的学生模型用 LoRA 学习。

We chose the best of ten versions on validation data only, then used it on the test set, on 100 reviews we labelled ourselves, and in the demo.

> 我们从十个版本里只用验证集挑出最好的一个，然后用在测试集、我们自己标注的 100 条评论和现场演示上。

### 第 5 页 · LoRA: train 1% of the weights（约 0:25）

LoRA freezes the original weights and trains two small matrices, A and B.

> LoRA 把原来的权重冻结，只训练两个小矩阵 A 和 B。

That is only one percent of the weights, a 70-megabyte file, and about an hour and a half of training on a laptop. Li Mingtai will now explain the tuning and the results.

> 这只占全部权重的 1%，是一个 70 MB 的文件，在笔记本上训练大约一个半小时。接下来由 Li Mingtai 介绍调参和结果。

### Han Daiyuan 的问答准备

**Q1. Your training labels come from another model. Isn't the student just copying the teacher's mistakes?**

> 训练标签来自另一个模型，学生模型不就是在照搬老师的错误吗？

Partly, yes. That is the main limit of distillation. We reduced it in two ways. A quality filter removed labels that contradicted the human star rating, 182 of 2,425. And we tested on 100 reviews labelled by us, not by the teacher. There, the student is statistically the same as the teacher, so it did not pick up noticeably more errors.

> 部分是的，这是蒸馏的主要局限。我们用两种方法降低影响。一是质量过滤，去掉和人工星级矛盾的标注，2,425 条里去掉了 182 条。二是在我们自己标注、而不是老师标注的 100 条评论上测试。在那里，学生和老师统计上没有差别，说明它没有多学到明显的错误。

**Q2. Your two annotators agreed at only 0.644. Are the human labels reliable?**

> 你们两个标注者的一致性只有 0.644，人工标注可靠吗？

That number shows that some aspects are hard to tell apart, for example whether "the colour runs after washing" is about build quality or performance. So we discussed every disagreement and agreed on final labels. On the same 20 reviews, the student agrees with us at 0.66 and the teacher at 0.69. With only 20 reviews we do not claim the models reach human level, only that both are far above the base model.

> 这个数字说明有些方面本来就难区分，比如“洗了掉色”算做工还是使用效果。所以我们逐条讨论了分歧，商定了最终标注。在同样的 20 条上，学生模型和我们的一致性是 0.66，老师是 0.69。只有 20 条样本，所以我们不说模型达到了人类水平，只说两者都远高于原始模型。

**Q3. What is LoRA, in one sentence?**

> 用一句话解释 LoRA？

LoRA keeps the original weights frozen and learns a small low-rank update beside them, so we train only 17 million of 1.7 billion parameters, about one percent.

> LoRA 保持原有权重不变，在旁边学习一个很小的低秩更新，所以 17 亿参数里我们只训练了 1,700 万个，大约 1%。
