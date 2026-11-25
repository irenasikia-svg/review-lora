# 讲稿：Beyond Star Ratings（6 分钟版，Han Daiyuan）

Han Daiyuan：第 1–6 页，约 4:10。Li Mingtai：第 7–9 页，约 2:05。全程约 6:15。

每页先是整段英文，再是整段中文。问答准备在最后（每题标了主答人）；完整的 22 题见 qa_prep.md。

## 第一部分：Han Daiyuan（第 1–6 页，约 4:10）

### 第 1 页 · Beyond Star Ratings（约 0:20）

Good morning. We are Han Daiyuan and Li Mingtai. A star rating says whether a customer is happy, but not why. This hotel review has three signals: a good location, a noisy room, and a slow check-in.

> 大家早上好，我们是 Han Daiyuan 和 Li Mingtai。星级评分能说明顾客满不满意，却说不出原因。这条酒店评论里有三个信号：位置好、房间吵、入住慢。

### 第 2 页 · One review in, one countable record out（约 0:35）

Our model reads a Chinese review and writes a record like this: the overall sentiment, and each aspect with the customer's own words. Aspects come from a fixed list of sixteen, so a program can count them. A shopper can compare three phones by what buyers praise and criticise. A seller can see which part of their own product draws the most complaints.

> 我们的模型读一条中文评论，输出这样一条记录：整体情感，以及每个方面和顾客的原话。方面都来自一张固定的 16 项清单，所以程序可以直接统计。买家可以货比三家，看三款手机各被夸什么、各被批评什么。卖家可以分析自己店里的评论，看产品哪个方面被抱怨得最多。

### 第 3 页 · Messy data, cleaned and labelled（约 0:45）

Our data is a public dataset, online shopping ten categories: 62,774 Chinese reviews of phones, books, fruit, hotels and more, each marked positive or negative by a person. It is messy: one copy-pasted template appears twenty-three times. We removed empty and duplicate reviews, kept those of 12 to 160 characters, and sampled 2,425, balanced by category and sentiment. Our first guideline had twelve overlapping aspects. Sixteen aspects with clear rules cut the teacher's errors from forty to fifteen.

> 我们的数据是一个公开数据集，叫 online shopping 10 cats：62,774 条中文网购评论，涉及手机、书籍、水果、酒店等十个类目，每条都有人工标注的好评或差评。数据很脏，有一条复制粘贴的模板出现了 23 次。我们删掉空评论和重复评论，只保留 12 到 160 个字的，再按类目和好差评均衡地抽了 2,425 条。第一版标注规则有 12 个互相重叠的方面，改成 16 个方面、把规则写清楚之后，老师模型的错误从 40 个降到了 15 个。

### 第 4 页 · A 30B teacher labels, a 1.7B student learns（约 0:45）

The teacher is Qwen3-30B, a mixture-of-experts model with 30 billion parameters, of which only 3 billion are active for each token. Running on our laptop, it labelled all 2,425 reviews in about fifty minutes. A filter removed labels that were not valid JSON or that contradicted the human star rating, which left 2,228 reviews. We split them into 1,824 for training, 142 for validation and 262 for testing. The student is Qwen3-1.7B, a much smaller model with 1.7 billion parameters.

> 老师模型是 Qwen3-30B，一个混合专家模型，总共 300 亿参数，但每个词只激活其中约 30 亿。它在我们的笔记本上运行，大约 50 分钟就标完了 2,425 条评论。过滤器去掉了格式不合格、或者和人工星级矛盾的标注，剩下 2,228 条。我们把它们分成训练集 1,824 条、验证集 142 条、测试集 262 条。学生模型是 Qwen3-1.7B，一个小得多的模型，只有 17 亿参数。

### 第 5 页 · LoRA: train 1% of the weights（约 0:40）

We fine-tuned the student with LoRA, using Apple's MLX on one M5 laptop with 32 gigabytes of memory. LoRA freezes the original weights and adds small trainable matrices to all 28 layers: 17 million weights, about one percent. Training runs 480 steps, about two passes over the data, in an hour and a half, and we keep the checkpoint with the lowest validation loss. Now let me show you what it can do.

> 我们用 LoRA 微调学生模型，用的是苹果的 MLX 框架，在一台 32 GB 内存的 M5 笔记本上完成。LoRA 把原来的权重冻结，在全部 28 层上加一些可以训练的小矩阵，一共 1,700 万个权重，大约占 1%。训练跑 480 步，大约把数据过两遍，用时一个半小时，最后保留验证损失最低的那个检查点。下面我来现场演示它能做什么。

### 第 6 页 · Live demo（约 1:05）

This is running live. The same model answers twice. Without our adapter, it invents an aspect, flavour, which is not on our list. With the adapter, we get Taste and Price, both positive. And this is the report for 150 hotel reviews: 53 percent positive, and the top complaints are rooms and service. Scan the QR code to try it. Li Mingtai will now explain the tuning and the results.

> 这是实时运行的。同一个模型回答两次。不带适配器时，它自己编了一个方面叫“味道”，不在我们的清单里。带上适配器，得到的是口味和价格，都是好评。这是 150 条酒店评论的报告：53% 是好评，差评最多的是房间和服务。扫二维码就可以自己试。接下来由 Li Mingtai 介绍调参和结果。

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
