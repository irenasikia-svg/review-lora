# 讲稿：Beyond Star Ratings（8 分钟版，Li Mingtai）

Han Daiyuan：第 1–5 页，约 3:25。Li Mingtai：第 6–9 页，约 4:05。全程约 7:30。

每页先是整段英文，再是整段中文。问答准备在最后（每题标了主答人）；完整的 22 题见 qa_prep.md。

## 第二部分：Li Mingtai（第 6–9 页，约 4:05）

### 第 6 页 · Tuning: the learning rate matters most（约 1:00）

Thank you, Han. We tuned the model one setting at a time, using only the validation set. First, how much is just luck? With a different random seed, the score moves by about 0.02. So we only trust bigger gaps. Three findings. One: the learning rate matters most. 5e-5 gave the best score, 0.793, and all three of its seeds beat the default. Two: a bigger rank is not better. Rank 32 dropped to 0.697, because in MLX a bigger rank also means a bigger update. Fixing the scale brought it back. Three: training only the top eight layers takes half the time, with similar quality.

> 谢谢 Han。我们每次只改一个设置来调参，而且只看验证集。先看运气的影响有多大：换一个随机种子，分数会变动大约 0.02，所以我们只相信比这更大的差距。三个发现。第一，学习率最重要。5e-5 得分最高，是 0.793，而且它的三个种子都超过了默认配置。第二，rank 越大不一定越好。rank 32 掉到了 0.697，因为在 MLX 里 rank 变大，更新幅度也跟着变大。把缩放系数调回来，分数就恢复了。第三，只训练最上面 8 层，时间减半，效果差不多。

### 第 7 页 · Near-teacher quality, a fifth of the memory（约 0:55）

Here are the results. On 262 test reviews, the base model scores 0.51. LoRA with default settings scores 0.73, and the tuned model 0.80, averaged over three seeds. Almost every output is now valid JSON. On the right is a harder test: 100 new reviews that Han and I labelled ourselves. Our student scores 0.70, and the thirty-billion-parameter teacher 0.69. Statistically, they are the same. But the student needs about a fifth of the memory, and it is almost twice as fast. Just giving the base model examples only reaches 0.59. Now, let me show you.

> 这是结果。在 262 条测试评论上，原始模型得分 0.51，默认设置的 LoRA 是 0.73，调参后的模型是 0.80，这是三个种子的平均。现在几乎每条输出都是合格的 JSON。右边是更难的测试：我和 Han 自己标注的 100 条新评论。学生模型得分 0.70，300 亿参数的老师模型是 0.69，统计上没有差别。但学生模型只需要大约五分之一的内存，速度快将近一倍。只给原始模型看几个示例，最多只能到 0.59。下面我来现场演示。

### 第 8 页 · Live demo（约 1:15）

This is running live on this laptop. The same model answers twice: on the left without our adapter, on the right with it. A customer says the fruit is great and cheap. The base model invents its own aspect, flavour, which is not on our list. With our adapter, we get Taste and Price, both positive. And this is the report a shop owner would see for 150 hotel reviews. 53 percent are positive, close to the star ratings, and the top complaints are rooms and service. You can try it yourself. Just scan the QR code.

> 这是在这台笔记本上实时运行的。同一个模型回答两次：左边不带我们的适配器，右边带上。这位顾客说水果很好、又便宜。原始模型自己编了一个方面叫“味道”，不在我们的清单里。加上适配器之后，得到的是口味和价格，都是好评。这是店主看到的 150 条酒店评论的报告。53% 是好评，和星级评分很接近，差评最多的是房间和服务。大家也可以自己试，扫这个二维码就行。

### 第 9 页 · What we learned（约 0:55）

We hit a few problems. In the second epoch the model started to memorise, so we always keep the checkpoint with the best validation loss. Running the teacher and the demo together ran out of memory, so we run one job at a time. And our long prompt made inference slower. To sum up: a small model, fine-tuned on one laptop, scores about the same as its big teacher on human labels, with a fifth of the memory. Our main lesson is that clean data matters more than model size. Thank you. We are happy to take your questions.

> 我们也遇到了一些问题。第二轮训练时模型开始死记硬背，所以我们总是保留验证损失最低的那个检查点。老师模型和演示同时运行会内存不足，所以我们一次只跑一个任务。另外，较长的提示词也让推理变慢了。总结一下：一个在笔记本上微调的小模型，在人工标注上的得分和它的大老师差不多，内存只要五分之一。我们最大的体会是，干净的数据比模型大小更重要。谢谢大家，欢迎提问。

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
