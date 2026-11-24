# 讲稿：Beyond Star Ratings（6 分钟版，Li Mingtai）

Han Daiyuan：第 1–5 页，约 2:25。Li Mingtai：第 6–9 页，约 3:10。全程约 5:35。

每页先英文、后中文对照。完整的问答准备见 qa_prep.md。

## 第二部分：Li Mingtai（第 6–9 页，约 3:10）

### 第 6 页 · Tuning: the learning rate matters most（约 0:45）

Thank you, Han. We tuned one setting at a time on the validation set. A different random seed moves the score by about 0.02, so we only trust bigger gaps.

> 谢谢 Han。我们每次只改一个设置，只看验证集。换一个随机种子分数会变动约 0.02，所以只相信比这更大的差距。

The learning rate matters most: 5e-5 gave the best score, and all three of its seeds beat the default. A bigger rank was worse, because in MLX it also makes the update bigger. And training only the top eight layers halves the time.

> 学习率最重要：5e-5 得分最高，而且三个种子都超过了默认配置。rank 越大反而越差，因为在 MLX 里 rank 变大，更新幅度也变大。另外，只训练最上面 8 层，时间减半。

### 第 7 页 · Near-teacher quality, a fifth of the memory（约 0:40）

On the test set, the score rises from 0.51 for the base model to 0.80 after tuning.

> 在测试集上，分数从原始模型的 0.51 提高到调参后的 0.80。

On 100 new reviews that Han and I labelled ourselves, our student scores 0.70 and the teacher 0.69. Statistically, they are the same, but the student needs a fifth of the memory. Now, let me show you.

> 在我和 Han 自己标注的 100 条新评论上，学生模型 0.70，老师模型 0.69，统计上没有差别，但学生模型只需要五分之一的内存。下面我来现场演示。

### 第 8 页 · Live demo（约 1:05）

This is running live. The same model answers twice. Without our adapter, it invents an aspect, flavour, which is not on our list. With the adapter, we get Taste and Price, both positive.

> 这是实时运行的。同一个模型回答两次。不带适配器时，它自己编了一个方面叫“味道”，不在我们的清单里。带上适配器，得到的是口味和价格，都是好评。

And this is the report for 150 hotel reviews: 53 percent positive, and the top complaints are rooms and service.

> 这是 150 条酒店评论的报告：53% 是好评，差评最多的是房间和服务。

Scan the QR code to try it.

> 扫二维码就可以自己试。

### 第 9 页 · What we learned（约 0:40）

Our main problems were overfitting, which we fixed by always keeping the best checkpoint, and running out of GPU memory, which we fixed by running one job at a time.

> 我们遇到的主要问题是过拟合和显存不足。前者靠始终保留最好的检查点解决，后者靠一次只跑一个任务解决。

To sum up: a small model, fine-tuned on one laptop, scores about the same as its big teacher, with a fifth of the memory. Thank you. We are happy to take your questions.

> 总结一下：一个在笔记本上微调的小模型，得分和它的大老师差不多，内存只要五分之一。谢谢大家，欢迎提问。

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
