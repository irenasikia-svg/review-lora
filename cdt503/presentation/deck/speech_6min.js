// 讲稿（6 分钟版）：同一套 9 页 PPT，页标题沿用 speech.js（8 分钟版），要说的话缩短。英文和中文一句对一句。
// 分工和 8 分钟版一样：Han Daiyuan 第 1–6 页（含现场演示），Li Mingtai 第 7–9 页，第 6 页结尾交接一次。
// 语速和 8 分钟版一样慢，省下的时间来自删内容，不是说得更快。
const FULL = require("./speech.js");

const SHORT = [
  {
    time: "0:20",
    say: [
      "Good morning. We are Han Daiyuan and Li Mingtai.",
      "A star rating says whether a customer is happy, but not why. This hotel review has three signals: a good location, a noisy room, and a slow check-in.",
    ],
    zh: [
      "大家早上好，我们是 Han Daiyuan 和 Li Mingtai。",
      "星级评分能说明顾客满不满意，却说不出原因。这条酒店评论里有三个信号：位置好、房间吵、入住慢。",
    ],
  },
  {
    time: "0:35",
    say: [
      "Our model reads a Chinese review and writes a record like this: the overall sentiment, and each aspect with the customer's own words.",
      "Aspects come from a fixed list of sixteen, so a program can count them. A shopper can compare three phones by what buyers praise and criticise. A seller can see which part of their own product draws the most complaints.",
    ],
    zh: [
      "我们的模型读一条中文评论，输出这样一条记录：整体情感，以及每个方面和顾客的原话。",
      "方面都来自一张固定的 16 项清单，所以程序可以直接统计。买家可以货比三家，看三款手机各被夸什么、各被批评什么。卖家可以分析自己店里的评论，看产品哪个方面被抱怨得最多。",
    ],
  },
  {
    time: "0:45",
    say: [
      "Our data is a public dataset, online shopping ten categories: 62,774 Chinese reviews of phones, books, fruit, hotels and more, each marked positive or negative by a person.",
      "It is messy: one copy-pasted template appears twenty-three times. We removed empty and duplicate reviews, kept those of 12 to 160 characters, and sampled 2,425, balanced by category and sentiment.",
      "Our first guideline had twelve overlapping aspects. Sixteen aspects with clear rules cut the teacher's errors from forty to fifteen.",
    ],
    zh: [
      "我们的数据是一个公开数据集，叫 online shopping 10 cats：62,774 条中文网购评论，涉及手机、书籍、水果、酒店等十个类目，每条都有人工标注的好评或差评。",
      "数据很脏，有一条复制粘贴的模板出现了 23 次。我们删掉空评论和重复评论，只保留 12 到 160 个字的，再按类目和好差评均衡地抽了 2,425 条。",
      "第一版标注规则有 12 个互相重叠的方面，改成 16 个方面、把规则写清楚之后，老师模型的错误从 40 个降到了 15 个。",
    ],
  },
  {
    time: "0:45",
    say: [
      "The teacher is Qwen3-30B, a mixture-of-experts model with 30 billion parameters, of which only 3 billion are active for each token. Running on our laptop, it labelled all 2,425 reviews in about fifty minutes.",
      "A filter removed labels that were not valid JSON or that contradicted the human star rating, which left 2,228 reviews. We split them into 1,824 for training, 142 for validation and 262 for testing.",
      "The student is Qwen3-1.7B, a much smaller model with 1.7 billion parameters.",
    ],
    zh: [
      "老师模型是 Qwen3-30B，一个混合专家模型，总共 300 亿参数，但每个词只激活其中约 30 亿。它在我们的笔记本上运行，大约 50 分钟就标完了 2,425 条评论。",
      "过滤器去掉了格式不合格、或者和人工星级矛盾的标注，剩下 2,228 条。我们把它们分成训练集 1,824 条、验证集 142 条、测试集 262 条。",
      "学生模型是 Qwen3-1.7B，一个小得多的模型，只有 17 亿参数。",
    ],
  },
  {
    time: "0:40",
    say: [
      "We fine-tuned the student with LoRA, using Apple's MLX on one M5 laptop with 32 gigabytes of memory. LoRA freezes the original weights and adds small trainable matrices to all 28 layers: 17 million weights, about one percent.",
      "Training runs 480 steps, about two passes over the data, in an hour and a half, and we keep the checkpoint with the lowest validation loss. Now let me show you what it can do.",
    ],
    zh: [
      "我们用 LoRA 微调学生模型，用的是苹果的 MLX 框架，在一台 32 GB 内存的 M5 笔记本上完成。LoRA 把原来的权重冻结，在全部 28 层上加一些可以训练的小矩阵，一共 1,700 万个权重，大约占 1%。",
      "训练跑 480 步，大约把数据过两遍，用时一个半小时，最后保留验证损失最低的那个检查点。下面我来现场演示它能做什么。",
    ],
  },
  {
    time: "1:05",
    say: [
      "This is running live. The same model answers twice. Without our adapter, it invents an aspect, flavour, which is not on our list. With the adapter, we get Taste and Price, both positive.",
      "And this is the report for 150 hotel reviews: 53 percent positive, and the top complaints are rooms and service.",
      "Scan the QR code to try it. Li Mingtai will now explain the tuning and the results.",
    ],
    zh: [
      "这是实时运行的。同一个模型回答两次。不带适配器时，它自己编了一个方面叫“味道”，不在我们的清单里。带上适配器，得到的是口味和价格，都是好评。",
      "这是 150 条酒店评论的报告：53% 是好评，差评最多的是房间和服务。",
      "扫二维码就可以自己试。接下来由 Li Mingtai 介绍调参和结果。",
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
      "On 100 new reviews that Han and I labelled ourselves, our student scores 0.70 and the teacher 0.69. Statistically, they are the same, but the student needs a fifth of the memory.",
    ],
    zh: [
      "在测试集上，分数从原始模型的 0.51 提高到调参后的 0.80。",
      "在我和 Han 自己标注的 100 条新评论上，学生模型 0.70，老师模型 0.69，统计上没有差别，但学生模型只需要五分之一的内存。",
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
