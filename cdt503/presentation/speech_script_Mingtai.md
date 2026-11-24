# 讲稿：Beyond Star Ratings（8 分钟版，Li Mingtai）

Han Daiyuan：第 1–5 页，约 3:25。Li Mingtai：第 6–9 页，约 4:05。全程约 7:30。

每页先英文、后中文对照。完整的问答准备见 qa_prep.md。

## 第二部分：Li Mingtai（第 6–9 页，约 4:05）

### 第 6 页 · Tuning: the learning rate matters most（约 1:00）

Thank you, Han. We tuned the model one setting at a time, using only the validation set. First, how much is just luck? With a different random seed, the score moves by about 0.02. So we only trust bigger gaps.

> 谢谢 Han。我们每次只改一个设置来调参，而且只看验证集。先看运气的影响有多大：换一个随机种子，分数会变动大约 0.02，所以我们只相信比这更大的差距。

Three findings. One: the learning rate matters most. 5e-5 gave the best score, 0.793, and all three of its seeds beat the default.

> 三个发现。第一，学习率最重要。5e-5 得分最高，是 0.793，而且它的三个种子都超过了默认配置。

Two: a bigger rank is not better. Rank 32 dropped to 0.697, because in MLX a bigger rank also means a bigger update. Fixing the scale brought it back.

> 第二，rank 越大不一定越好。rank 32 掉到了 0.697，因为在 MLX 里 rank 变大，更新幅度也跟着变大。把缩放系数调回来，分数就恢复了。

Three: training only the top eight layers takes half the time, with similar quality.

> 第三，只训练最上面 8 层，时间减半，效果差不多。

### 第 7 页 · Near-teacher quality, a fifth of the memory（约 0:55）

Here are the results. On 262 test reviews, the base model scores 0.51. LoRA with default settings scores 0.73, and the tuned model 0.80, averaged over three seeds. Almost every output is now valid JSON.

> 这是结果。在 262 条测试评论上，原始模型得分 0.51，默认设置的 LoRA 是 0.73，调参后的模型是 0.80，这是三个种子的平均。现在几乎每条输出都是合格的 JSON。

On the right is a harder test: 100 new reviews that Han and I labelled ourselves. Our student scores 0.70, and the thirty-billion-parameter teacher 0.69. Statistically, they are the same.

> 右边是更难的测试：我和 Han 自己标注的 100 条新评论。学生模型得分 0.70，300 亿参数的老师模型是 0.69，统计上没有差别。

But the student needs about a fifth of the memory, and it is almost twice as fast. Just giving the base model examples only reaches 0.59. Now, let me show you.

> 但学生模型只需要大约五分之一的内存，速度快将近一倍。只给原始模型看几个示例，最多只能到 0.59。下面我来现场演示。

### 第 8 页 · Live demo（约 1:15）

This is running live on this laptop. The same model answers twice: on the left without our adapter, on the right with it.

> 这是在这台笔记本上实时运行的。同一个模型回答两次：左边不带我们的适配器，右边带上。

A customer says the fruit is great and cheap. The base model invents its own aspect, flavour, which is not on our list. With our adapter, we get Taste and Price, both positive.

> 这位顾客说水果很好、又便宜。原始模型自己编了一个方面叫“味道”，不在我们的清单里。加上适配器之后，得到的是口味和价格，都是好评。

And this is the report a shop owner would see for 150 hotel reviews. 53 percent are positive, close to the star ratings, and the top complaints are rooms and service.

> 这是店主看到的 150 条酒店评论的报告。53% 是好评，和星级评分很接近，差评最多的是房间和服务。

You can try it yourself. Just scan the QR code.

> 大家也可以自己试，扫这个二维码就行。

### 第 9 页 · What we learned（约 0:55）

We hit a few problems. In the second epoch the model started to memorise, so we always keep the checkpoint with the best validation loss. Running the teacher and the demo together ran out of memory, so we run one job at a time. And our long prompt made inference slower.

> 我们也遇到了一些问题。第二轮训练时模型开始死记硬背，所以我们总是保留验证损失最低的那个检查点。老师模型和演示同时运行会内存不足，所以我们一次只跑一个任务。另外，较长的提示词也让推理变慢了。

To sum up: a small model, fine-tuned on one laptop, scores about the same as its big teacher on human labels, with a fifth of the memory. Our main lesson is that clean data matters more than model size. Thank you. We are happy to take your questions.

> 总结一下：一个在笔记本上微调的小模型，在人工标注上的得分和它的大老师差不多，内存只要五分之一。我们最大的体会是，干净的数据比模型大小更重要。谢谢大家，欢迎提问。

### Li Mingtai 的问答准备

**Q1. How do you know the differences between settings are not just random?**

> 你们怎么知道不同设置之间的差别不是随机造成的？

We trained the default setting twice and the final setting three times, with different random seeds. Chance alone moved the score by up to about 0.02, so we treat smaller gaps as ties. The learning-rate result is bigger than that: all three seeds of 5e-5 beat both seeds of the default.

> 我们用不同的随机种子，把默认设置训练了两次、最终设置训练了三次。光是随机性就能让分数变动约 0.02，所以比这小的差距我们都当作打平。学习率的效果比这大：5e-5 的三个种子都超过了默认设置的两个种子。

**Q2. Why did the learning rate 2e-4 fail?**

> 为什么学习率 2e-4 会训练失败？

The steps were too big from the start. We used a constant learning rate with no warm-up, and MLX also multiplies the update by a fixed scale of 20. Within 40 steps the validation loss jumped from 2.6 to 7.1, and the model only printed repeated punctuation. A warm-up might help, but we did not test it. Halving the rate to 5e-5 gave our best result instead.

> 一开始步子就太大了。我们用的是恒定学习率、没有预热，而且 MLX 还会把更新乘上固定的系数 20。40 步之内验证损失从 2.6 跳到 7.1，模型只会输出重复的标点。加预热也许有用，但我们没有测试。我们改为把学习率减半到 5e-5，反而得到了最好的结果。

**Q3. How does the demo show both models without loading two models?**

> 演示里怎么不加载两个模型就能同时展示两种结果？

LoRA's output is the original output plus a small extra term. If we set its scale to zero, the adapter is switched off, and the same model in memory behaves exactly like the base model. We switch it for each request, so we only need memory for one model.

> LoRA 的输出等于原来的输出再加上一个小的额外项。把它的系数设成 0，适配器就关掉了，内存里同一个模型就和原始模型完全一样。我们每个请求切换一次，所以只需要一个模型的内存。
