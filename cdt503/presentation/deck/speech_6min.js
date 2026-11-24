// 讲稿（6 分钟版）：同一套 9 页 PPT，页标题沿用 speech.js（8 分钟版），要说的话缩短。英文和中文一句对一句。
// 分工和 8 分钟版一样：Han Daiyuan 第 1–5 页，Li Mingtai 第 6–9 页，第 5 页结尾交接一次。
// 语速和 8 分钟版一样慢，省下的时间来自删内容，不是说得更快。
const FULL = require("./speech.js");

const SHORT = [
  {
    time: "0:25",
    say: [
      "Good morning. We are Han Daiyuan and Li Mingtai.",
      "A star rating says whether a customer is happy, but not why. This hotel review has three signals: a good location, a noisy room, and a slow check-in. Our model finds them automatically.",
    ],
    zh: [
      "大家早上好，我们是 Han Daiyuan 和 Li Mingtai。",
      "星级评分能说明顾客满不满意，却说不出原因。这条酒店评论里有三个信号：位置好、房间吵、入住慢。我们的模型能自动把它们找出来。",
    ],
  },
  {
    time: "0:25",
    say: [
      "Our model turns each review into a record like this: the overall sentiment, and each aspect with the customer's own words.",
      "Aspects come from a fixed list of sixteen, so a program can count them.",
    ],
    zh: [
      "模型会把每条评论变成这样一条记录：整体情感，以及每个方面和顾客的原话。",
      "方面都来自一张固定的 16 项清单，所以程序可以直接统计。",
    ],
  },
  {
    time: "0:35",
    say: [
      "We used 62,774 real shopping reviews, and the data is messy. One copy-pasted template appears twenty-three times.",
      "After cleaning, we sampled 2,425 reviews. A thirty-billion-parameter teacher model labelled them with our guideline. Clearer rules with sixteen aspects cut its errors from forty to fifteen, and a quality filter left 2,228 reviews.",
    ],
    zh: [
      "我们用了 62,774 条真实的网购评论，数据很脏，有一条复制粘贴的模板出现了 23 次。",
      "清洗之后我们抽了 2,425 条，由 300 亿参数的老师模型按我们的规则标注。改成 16 个方面、规则写清楚之后，它的错误从 40 个降到 15 个，质量过滤后剩下 2,228 条。",
    ],
  },
  {
    time: "0:35",
    say: [
      "Here is the whole system, all on one laptop. The teacher labels, the filter checks, and a 1.7-billion-parameter student learns with LoRA.",
      "We chose the best of ten versions on validation data only, then used it on the test set, on 100 reviews we labelled ourselves, and in the demo.",
    ],
    zh: [
      "这是整个系统，全部在一台笔记本上运行。老师模型标注，过滤器把关，17 亿参数的学生模型用 LoRA 学习。",
      "我们从十个版本里只用验证集挑出最好的一个，然后用在测试集、我们自己标注的 100 条评论和现场演示上。",
    ],
  },
  {
    time: "0:25",
    say: [
      "LoRA freezes the original weights and trains two small matrices, A and B.",
      "That is only one percent of the weights, a 70-megabyte file, and about an hour and a half of training on a laptop. Li Mingtai will now explain the tuning and the results.",
    ],
    zh: [
      "LoRA 把原来的权重冻结，只训练两个小矩阵 A 和 B。",
      "这只占全部权重的 1%，是一个 70 MB 的文件，在笔记本上训练大约一个半小时。接下来由 Li Mingtai 介绍调参和结果。",
    ],
  },
  {
    time: "0:45",
    say: [
      "Thank you, Han. We tuned one setting at a time on the validation set. A different random seed moves the score by about 0.02, so we only trust bigger gaps.",
      "The learning rate matters most: 5e-5 gave the best score, and all three of its seeds beat the default. A bigger rank was worse, because in MLX it also makes the update bigger. And training only the top eight layers halves the time.",
    ],
    zh: [
      "谢谢 Han。我们每次只改一个设置，只看验证集。换一个随机种子分数会变动约 0.02，所以只相信比这更大的差距。",
      "学习率最重要：5e-5 得分最高，而且三个种子都超过了默认配置。rank 越大反而越差，因为在 MLX 里 rank 变大，更新幅度也变大。另外，只训练最上面 8 层，时间减半。",
    ],
  },
  {
    time: "0:40",
    say: [
      "On the test set, the score rises from 0.51 for the base model to 0.80 after tuning.",
      "On 100 new reviews that Han and I labelled ourselves, our student scores 0.70 and the teacher 0.69. Statistically, they are the same, but the student needs a fifth of the memory. Now, let me show you.",
    ],
    zh: [
      "在测试集上，分数从原始模型的 0.51 提高到调参后的 0.80。",
      "在我和 Han 自己标注的 100 条新评论上，学生模型 0.70，老师模型 0.69，统计上没有差别，但学生模型只需要五分之一的内存。下面我来现场演示。",
    ],
  },
  {
    time: "1:05",
    say: [
      "This is running live. The same model answers twice. Without our adapter, it invents an aspect, flavour, which is not on our list. With the adapter, we get Taste and Price, both positive.",
      "And this is the report for 150 hotel reviews: 53 percent positive, and the top complaints are rooms and service.",
      "Scan the QR code to try it.",
    ],
    zh: [
      "这是实时运行的。同一个模型回答两次。不带适配器时，它自己编了一个方面叫“味道”，不在我们的清单里。带上适配器，得到的是口味和价格，都是好评。",
      "这是 150 条酒店评论的报告：53% 是好评，差评最多的是房间和服务。",
      "扫二维码就可以自己试。",
    ],
  },
  {
    time: "0:40",
    say: [
      "Our main problems were overfitting, which we fixed by always keeping the best checkpoint, and running out of GPU memory, which we fixed by running one job at a time.",
      "To sum up: a small model, fine-tuned on one laptop, scores about the same as its big teacher, with a fifth of the memory. Thank you. We are happy to take your questions.",
    ],
    zh: [
      "我们遇到的主要问题是过拟合和显存不足。前者靠始终保留最好的检查点解决，后者靠一次只跑一个任务解决。",
      "总结一下：一个在笔记本上微调的小模型，得分和它的大老师差不多，内存只要五分之一。谢谢大家，欢迎提问。",
    ],
  },
];

module.exports = FULL.map((p, i) => ({ title: p.title, speaker: p.speaker, ...SHORT[i] }));
