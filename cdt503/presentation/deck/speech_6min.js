// 6 分钟版讲稿：同一套 9 页 PPT，每页的标题和"屏幕上有什么"沿用 speech.js（8 分钟版），只把要说的话缩短。
// 语速和 8 分钟版一样慢（每分钟约 100 词以内），省下的时间来自删内容，不是说得更快。
const FULL = require("./speech.js");

const SHORT = [
  {
    time: "0:25",
    say: [
      "Good morning. We are Han Daiyuan and Li Mingtai.",
      "A star rating says whether a customer is happy, but not why. This hotel review has three signals: a good location, a noisy room, and a slow check-in. Our model finds them automatically.",
    ],
    tips: "说到三个信号时，依次指右边的绿、红、红三处高亮。",
  },
  {
    time: "0:25",
    say: [
      "Our model turns each review into a record like this: the overall sentiment, and each aspect with the customer's own words.",
      "Aspects come from a fixed list of sixteen, so a program can count them.",
    ],
    tips: "指一下右边三个彩色方块，对应左边 JSON 里的三个方面。",
  },
  {
    time: "0:35",
    say: [
      "We used 62,774 real shopping reviews, and the data is messy. One copy-pasted template appears twenty-three times.",
      "After cleaning, we sampled 2,425 reviews. A thirty-billion-parameter teacher model labelled them with our guideline. Clearer rules with sixteen aspects cut its errors from forty to fifteen, and a quality filter left 2,228 reviews.",
    ],
    tips: "\"真实脏数据\"是评分点，重复 23 次的模板一定要说到。",
  },
  {
    time: "0:35",
    say: [
      "Here is the whole system, all on one laptop. The teacher labels, the filter checks, and a 1.7-billion-parameter student learns with LoRA.",
      "We chose the best of ten versions on validation data only, then used it on the test set, on 100 reviews we labelled ourselves, and in the demo. Li Mingtai will explain the training.",
    ],
    tips: "从左到右指着讲，最后一句交给 B。",
  },
  {
    time: "0:25",
    say: [
      "Thank you. LoRA freezes the original weights and trains two small matrices, A and B.",
      "That is only one percent of the weights, a 70-megabyte file, and about an hour and a half of training on a laptop.",
    ],
    tips: "公式不用念，指一下\"W0 冻结、A 和 B 训练\"。",
  },
  {
    time: "0:45",
    say: [
      "We tuned one setting at a time on the validation set. A different random seed moves the score by about 0.02, so we only trust bigger gaps.",
      "The learning rate matters most: 5e-5 gave the best score, and all three of its seeds beat the default. A bigger rank was worse, because in MLX it also makes the update bigger. And training only the top eight layers halves the time.",
    ],
    tips: "\"系统调参\"是 Level 2 的关键，边讲边指琥珀色和红色的柱子。",
  },
  {
    time: "0:40",
    say: [
      "On the test set, the score rises from 0.51 for the base model to 0.80 after tuning.",
      "On 100 new reviews that we labelled ourselves, our student scores 0.70 and the teacher 0.69. Statistically, they are the same, but the student needs a fifth of the memory. Now, let us show you.",
    ],
    tips: "不要说\"达到人类水平\"。说完最后一句，A 切到浏览器。",
  },
  {
    time: "1:05",
    say: [
      "[A switches to browser tab 1, clicks example 1, then Analyze] This is running live. The same model answers twice. Without our adapter, it invents an aspect, flavour, which is not on our list. With the adapter, we get Taste and Price, both positive.",
      "[A switches to tab 2, the prepared report] And this is the report for 150 hotel reviews: 53 percent positive, and the top complaints are rooms and service.",
      "Scan the QR code to try it.",
    ],
    tips: "左右两边先后出结果，B 等左边出来再讲左边。第 2 个标签页的 Hotel 报告要上台前生成好。出问题 15 秒内切备用视频。",
  },
  {
    time: "0:40",
    say: [
      "[A] Our main problems were overfitting, which we fixed by always keeping the best checkpoint, and running out of GPU memory, which we fixed by running one job at a time.",
      "[B] To sum up: a small model, fine-tuned on one laptop, scores about the same as its big teacher, with a fifth of the memory. Thank you. We are happy to take your questions.",
    ],
    tips: "A 讲两个困难，B 收尾。",
  },
];

module.exports = FULL.map((p, i) => ({ ...p, ...SHORT[i] }));
