// 讲稿（8 分钟版）：按 PPT 页码，一页一段，英文和中文一句对一句。
// 分工：Han Daiyuan 讲第 1–6 页（问题、数据、蒸馏、系统、LoRA、现场演示），
//       Li Mingtai 讲第 7–9 页（调参、结果、总结）。中间只交接一次（第 6 页演示结尾）。
// PPT 的演讲者备注和讲稿文档（speech_script*.md）都从这里生成，改一处两边同步。
const HAN = "Han Daiyuan", LI = "Li Mingtai";

module.exports = [
  {
    title: "Beyond Star Ratings", speaker: HAN, time: "0:30",
    say: [
      "Good morning. We are Han Daiyuan and Li Mingtai, and our project is Beyond Star Ratings.",
      "A star rating tells a shop whether a customer is happy, but not why. This one hotel review has three signals: a good location, a noisy room, and a slow check-in.",
      "Our model finds them automatically.",
    ],
    zh: [
      "大家早上好。我们是 Han Daiyuan 和 Li Mingtai，我们的项目叫 Beyond Star Ratings。",
      "星级评分能告诉商家顾客满不满意，却说不出原因。比如这一条酒店评论里就有三个信号：位置好、房间吵、入住慢。",
      "我们的模型能自动把它们找出来。",
    ],
  },
  {
    title: "One review in, one countable record out", speaker: HAN, time: "0:35",
    say: [
      "For that review, our model writes this record. It gives the overall sentiment. Then, for each aspect, it gives the customer's own words, and whether they are positive or negative.",
      "Every aspect must come from this fixed list of sixteen. Because the names are fixed, a program can count them, for example, how many complaints this month are about logistics.",
    ],
    zh: [
      "对这条评论，模型会输出这样一条记录：先给出整体情感，然后对每个方面，给出顾客的原话，以及是好评还是差评。",
      "每个方面都必须来自这张固定的 16 项清单。名称固定了，程序就能统计，比如这个月有多少差评是关于物流的。",
    ],
  },
  {
    title: "Messy data, cleaned and labelled", speaker: HAN, time: "0:50",
    say: [
      "We used 62,774 real Chinese shopping reviews from ten categories, and the data is messy. One copy-pasted template appears twenty-three times. There are also duplicates, invisible characters, and very long rants.",
      "After cleaning, we sampled 2,425 reviews, balanced by category and sentiment. A thirty-billion-parameter teacher model labelled them, using our written guideline.",
      "Our first guideline had twelve overlapping aspects. Clearer rules with sixteen aspects cut the teacher's errors from forty to fifteen. A quality filter then removed doubtful labels, which left 2,228 reviews.",
    ],
    zh: [
      "我们用了 62,774 条真实的中文网购评论，来自十个类目，数据很脏。有一条复制粘贴的模板出现了 23 次，还有重复评论、看不见的字符和特别长的抱怨。",
      "清洗之后，我们按类目和好差评均衡地抽了 2,425 条，由一个 300 亿参数的老师模型按照我们写的标注规则来标注。",
      "第一版规则有 12 个互相重叠的方面。改成 16 个方面、把规则写清楚之后，老师模型的错误从 40 个降到 15 个。最后用质量过滤去掉可疑的标注，剩下 2,228 条。",
    ],
  },
  {
    title: "A 30B teacher labels, a 1.7B student learns", speaker: HAN, time: "0:50",
    say: [
      "Here is the whole system, and it all runs on one Apple laptop. The teacher labels, the filter checks, and we split the data into training, validation, and test sets.",
      "The student is a 1.7-billion-parameter Qwen model with LoRA. We trained ten versions and chose the best one on validation data only.",
      "That one 70-megabyte adapter is used three times: on the test set, on 100 new reviews that we labelled ourselves, and in the live demo.",
    ],
    zh: [
      "这是整个系统，全部在一台苹果笔记本上运行。老师模型负责标注，过滤器负责把关，然后我们把数据分成训练集、验证集和测试集。",
      "学生模型是 17 亿参数的 Qwen，用 LoRA 微调。我们训练了十个版本，只用验证集挑出最好的一个。",
      "这一个 70 MB 的适配器用在三个地方：测试集、我们自己标注的 100 条新评论，以及现场演示。",
    ],
  },
  {
    title: "LoRA: train 1% of the weights", speaker: HAN, time: "0:40",
    say: [
      "How can a laptop train the student? Training all 1.7 billion weights would not fit. LoRA freezes the original weights, W-zero, and adds two small matrices, A and B. Only these two are trained.",
      "That is about one percent of the weights, a 70-megabyte file, and about an hour and a half of training. Now let me show you what it can do.",
    ],
    zh: [
      "一台笔记本怎么训练学生模型？17 亿个权重全部训练是放不下的。LoRA 把原来的权重 W0 冻结，在旁边加两个小矩阵 A 和 B，只训练这两个。",
      "这只占全部权重的 1% 左右，是一个 70 MB 的文件，训练大约一个半小时。下面我来现场演示它能做什么。",
    ],
  },
  {
    title: "Live demo", speaker: HAN, time: "1:20",
    say: [
      "This is running live on this laptop. The same model answers twice: on the left without our adapter, on the right with it.",
      "A customer says the fruit is great and cheap. The base model invents its own aspect, flavour, which is not on our list. With our adapter, we get Taste and Price, both positive.",
      "And this is the report a shop owner would see for 150 hotel reviews. 53 percent are positive, close to the star ratings, and the top complaints are rooms and service.",
      "You can try it yourself. Just scan the QR code. Next, Li Mingtai will show how we tuned it and how well it works.",
    ],
    zh: [
      "这是在这台笔记本上实时运行的。同一个模型回答两次：左边不带我们的适配器，右边带上。",
      "这位顾客说水果很好、又便宜。原始模型自己编了一个方面叫“味道”，不在我们的清单里。加上适配器之后，得到的是口味和价格，都是好评。",
      "这是店主看到的 150 条酒店评论的报告。53% 是好评，和星级评分很接近，差评最多的是房间和服务。",
      "大家也可以自己试，扫这个二维码就行。接下来由 Li Mingtai 介绍我们怎么调参，以及效果怎么样。",
    ],
  },
  {
    title: "Tuning: the learning rate matters most", speaker: LI, time: "1:00",
    say: [
      "Thank you, Han. We tuned the model one setting at a time, using only the validation set. First, how much is just luck? With a different random seed, the score moves by about 0.02. So we only trust bigger gaps.",
      "Three findings. One: the learning rate matters most. 5e-5 gave the best score, 0.793, and all three of its seeds beat the default.",
      "Two: a bigger rank is not better. Rank 32 dropped to 0.697, because in MLX a bigger rank also means a bigger update. Fixing the scale brought it back.",
      "Three: training only the top eight layers takes half the time, with similar quality.",
    ],
    zh: [
      "谢谢 Han。我们每次只改一个设置来调参，而且只看验证集。先看运气的影响有多大：换一个随机种子，分数会变动大约 0.02，所以我们只相信比这更大的差距。",
      "三个发现。第一，学习率最重要。5e-5 得分最高，是 0.793，而且它的三个种子都超过了默认配置。",
      "第二，rank 越大不一定越好。rank 32 掉到了 0.697，因为在 MLX 里 rank 变大，更新幅度也跟着变大。把缩放系数调回来，分数就恢复了。",
      "第三，只训练最上面 8 层，时间减半，效果差不多。",
    ],
  },
  {
    title: "Near-teacher quality, a fifth of the memory", speaker: LI, time: "0:50",
    say: [
      "Here are the results. On 262 test reviews, the base model scores 0.51. LoRA with default settings scores 0.73, and the tuned model 0.80, averaged over three seeds. Almost every output is now valid JSON.",
      "On the right is a harder test: 100 new reviews that Han and I labelled ourselves. Our student scores 0.70, and the thirty-billion-parameter teacher 0.69. Statistically, they are the same.",
      "But the student needs about a fifth of the memory, and it is almost twice as fast. Just giving the base model examples only reaches 0.59.",
    ],
    zh: [
      "这是结果。在 262 条测试评论上，原始模型得分 0.51，默认设置的 LoRA 是 0.73，调参后的模型是 0.80，这是三个种子的平均。现在几乎每条输出都是合格的 JSON。",
      "右边是更难的测试：我和 Han 自己标注的 100 条新评论。学生模型得分 0.70，300 亿参数的老师模型是 0.69，统计上没有差别。",
      "但学生模型只需要大约五分之一的内存，速度快将近一倍。只给原始模型看几个示例，最多只能到 0.59。",
    ],
  },
  {
    title: "What we learned", speaker: LI, time: "0:55",
    say: [
      "We hit a few problems. In the second epoch the model started to memorise, so we always keep the checkpoint with the best validation loss. Running the teacher and the demo together ran out of memory, so we run one job at a time. And our long prompt made inference slower.",
      "To sum up: a small model, fine-tuned on one laptop, scores about the same as its big teacher on human labels, with a fifth of the memory. Our main lesson is that clean data matters more than model size. Thank you. We are happy to take your questions.",
    ],
    zh: [
      "我们也遇到了一些问题。第二轮训练时模型开始死记硬背，所以我们总是保留验证损失最低的那个检查点。老师模型和演示同时运行会内存不足，所以我们一次只跑一个任务。另外，较长的提示词也让推理变慢了。",
      "总结一下：一个在笔记本上微调的小模型，在人工标注上的得分和它的大老师差不多，内存只要五分之一。我们最大的体会是，干净的数据比模型大小更重要。谢谢大家，欢迎提问。",
    ],
  },
];
