# 讲稿：Beyond Star Ratings（6 分钟版）

Han Daiyuan：第 1–5 页，约 2:25。Li Mingtai：第 6–9 页，约 3:10。全程约 5:35。

每页先是整段英文，再是整段中文。问答准备在最后（每题标了主答人）；完整的 22 题见 qa_prep.md。

## 第一部分：Han Daiyuan（第 1–5 页，约 2:25）

### 第 1 页 · Beyond Star Ratings（约 0:25）

Good morning. We are Han Daiyuan and Li Mingtai. A star rating says whether a customer is happy, but not why. This hotel review has three signals: a good location, a noisy room, and a slow check-in. Our model finds them automatically.

> 大家早上好，我们是 Han Daiyuan 和 Li Mingtai。星级评分能说明顾客满不满意，却说不出原因。这条酒店评论里有三个信号：位置好、房间吵、入住慢。我们的模型能自动把它们找出来。

### 第 2 页 · One review in, one countable record out（约 0:25）

Our model turns each review into a record like this: the overall sentiment, and each aspect with the customer's own words. Aspects come from a fixed list of sixteen, so a program can count them.

> 模型会把每条评论变成这样一条记录：整体情感，以及每个方面和顾客的原话。方面都来自一张固定的 16 项清单，所以程序可以直接统计。

### 第 3 页 · Messy data, cleaned and labelled（约 0:35）

We used 62,774 real shopping reviews, and the data is messy. One copy-pasted template appears twenty-three times. After cleaning, we sampled 2,425 reviews. A thirty-billion-parameter teacher model labelled them with our guideline. Clearer rules with sixteen aspects cut its errors from forty to fifteen, and a quality filter left 2,228 reviews.

> 我们用了 62,774 条真实的网购评论，数据很脏，有一条复制粘贴的模板出现了 23 次。清洗之后我们抽了 2,425 条，由 300 亿参数的老师模型按我们的规则标注。改成 16 个方面、规则写清楚之后，它的错误从 40 个降到 15 个，质量过滤后剩下 2,228 条。

### 第 4 页 · A 30B teacher labels, a 1.7B student learns（约 0:35）

Here is the whole system, all on one laptop. The teacher labels, the filter checks, and a 1.7-billion-parameter student learns with LoRA. We chose the best of ten versions on validation data only, then used it on the test set, on 100 reviews we labelled ourselves, and in the demo.

> 这是整个系统，全部在一台笔记本上运行。老师模型标注，过滤器把关，17 亿参数的学生模型用 LoRA 学习。我们从十个版本里只用验证集挑出最好的一个，然后用在测试集、我们自己标注的 100 条评论和现场演示上。

### 第 5 页 · LoRA: train 1% of the weights（约 0:25）

LoRA freezes the original weights and trains two small matrices, A and B. That is only one percent of the weights, a 70-megabyte file, and about an hour and a half of training on a laptop. Li Mingtai will now explain the tuning and the results.

> LoRA 把原来的权重冻结，只训练两个小矩阵 A 和 B。这只占全部权重的 1%，是一个 70 MB 的文件，在笔记本上训练大约一个半小时。接下来由 Li Mingtai 介绍调参和结果。

## 第二部分：Li Mingtai（第 6–9 页，约 3:10）

### 第 6 页 · Tuning: the learning rate matters most（约 0:45）

Thank you, Han. We tuned one setting at a time on the validation set. A different random seed moves the score by about 0.02, so we only trust bigger gaps. The learning rate matters most: 5e-5 gave the best score, and all three of its seeds beat the default. A bigger rank was worse, because in MLX it also makes the update bigger. And training only the top eight layers halves the time.

> 谢谢 Han。我们每次只改一个设置，只看验证集。换一个随机种子分数会变动约 0.02，所以只相信比这更大的差距。学习率最重要：5e-5 得分最高，而且三个种子都超过了默认配置。rank 越大反而越差，因为在 MLX 里 rank 变大，更新幅度也变大。另外，只训练最上面 8 层，时间减半。

### 第 7 页 · Near-teacher quality, a fifth of the memory（约 0:40）

On the test set, the score rises from 0.51 for the base model to 0.80 after tuning. On 100 new reviews that Han and I labelled ourselves, our student scores 0.70 and the teacher 0.69. Statistically, they are the same, but the student needs a fifth of the memory. Now, let me show you.

> 在测试集上，分数从原始模型的 0.51 提高到调参后的 0.80。在我和 Han 自己标注的 100 条新评论上，学生模型 0.70，老师模型 0.69，统计上没有差别，但学生模型只需要五分之一的内存。下面我来现场演示。

### 第 8 页 · Live demo（约 1:05）

This is running live. The same model answers twice. Without our adapter, it invents an aspect, flavour, which is not on our list. With the adapter, we get Taste and Price, both positive. And this is the report for 150 hotel reviews: 53 percent positive, and the top complaints are rooms and service. Scan the QR code to try it.

> 这是实时运行的。同一个模型回答两次。不带适配器时，它自己编了一个方面叫“味道”，不在我们的清单里。带上适配器，得到的是口味和价格，都是好评。这是 150 条酒店评论的报告：53% 是好评，差评最多的是房间和服务。扫二维码就可以自己试。

### 第 9 页 · What we learned（约 0:40）

Our main problems were overfitting, which we fixed by always keeping the best checkpoint, and running out of GPU memory, which we fixed by running one job at a time. To sum up: a small model, fine-tuned on one laptop, scores about the same as its big teacher, with a fifth of the memory. Thank you. We are happy to take your questions.

> 我们遇到的主要问题是过拟合和显存不足。前者靠始终保留最好的检查点解决，后者靠一次只跑一个任务解决。总结一下：一个在笔记本上微调的小模型，得分和它的大老师差不多，内存只要五分之一。谢谢大家，欢迎提问。

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
