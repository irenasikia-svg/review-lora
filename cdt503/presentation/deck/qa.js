// 讲稿末尾的问答准备（双语）：每人三题，按分工由负责那部分的人主答。完整的 22 题见 ../qa_prep.md。
const HAN = "Han Daiyuan", LI = "Li Mingtai";

module.exports = [
  {
    who: HAN,
    q: "Your training labels come from another model. Isn't the student just copying the teacher's mistakes?",
    qZh: "训练标签来自另一个模型，学生模型不就是在照搬老师的错误吗？",
    a: "Partly, yes. That is the main limit of distillation. We reduced it in two ways. A quality filter removed labels that contradicted the human star rating, 182 of 2,425. And we tested on 100 reviews labelled by us, not by the teacher. There, the student is statistically the same as the teacher, so it did not pick up noticeably more errors.",
    aZh: "部分是的，这是蒸馏的主要局限。我们用两种方法降低影响。一是质量过滤，去掉和人工星级矛盾的标注，2,425 条里去掉了 182 条。二是在我们自己标注、而不是老师标注的 100 条评论上测试。在那里，学生和老师统计上没有差别，说明它没有多学到明显的错误。",
  },
  {
    who: HAN,
    q: "Your two annotators agreed at only 0.644. Are the human labels reliable?",
    qZh: "你们两个标注者的一致性只有 0.644，人工标注可靠吗？",
    a: "That number shows that some aspects are hard to tell apart, for example whether \"the colour runs after washing\" is about build quality or performance. So we discussed every disagreement and agreed on final labels. On the same 20 reviews, the student agrees with us at 0.66 and the teacher at 0.69. With only 20 reviews we do not claim the models reach human level, only that both are far above the base model.",
    aZh: "这个数字说明有些方面本来就难区分，比如“洗了掉色”算做工还是使用效果。所以我们逐条讨论了分歧，商定了最终标注。在同样的 20 条上，学生模型和我们的一致性是 0.66，老师是 0.69。只有 20 条样本，所以我们不说模型达到了人类水平，只说两者都远高于原始模型。",
  },
  {
    who: HAN,
    q: "What is LoRA, in one sentence?",
    qZh: "用一句话解释 LoRA？",
    a: "LoRA keeps the original weights frozen and learns a small low-rank update beside them, so we train only 17 million of 1.7 billion parameters, about one percent.",
    aZh: "LoRA 保持原有权重不变，在旁边学习一个很小的低秩更新，所以 17 亿参数里我们只训练了 1,700 万个，大约 1%。",
  },
  {
    who: LI,
    q: "How do you know the differences between settings are not just random?",
    qZh: "你们怎么知道不同设置之间的差别不是随机造成的？",
    a: "We trained the default setting twice and the final setting three times, with different random seeds. Chance alone moved the score by up to about 0.02, so we treat smaller gaps as ties. The learning-rate result is bigger than that: all three seeds of 5e-5 beat both seeds of the default.",
    aZh: "我们用不同的随机种子，把默认设置训练了两次、最终设置训练了三次。光是随机性就能让分数变动约 0.02，所以比这小的差距我们都当作打平。学习率的效果比这大：5e-5 的三个种子都超过了默认设置的两个种子。",
  },
  {
    who: LI,
    q: "Why did the learning rate 2e-4 fail?",
    qZh: "为什么学习率 2e-4 会训练失败？",
    a: "The steps were too big from the start. We used a constant learning rate with no warm-up, and MLX also multiplies the update by a fixed scale of 20. Within 40 steps the validation loss jumped from 2.6 to 7.1, and the model only printed repeated punctuation. A warm-up might help, but we did not test it. Halving the rate to 5e-5 gave our best result instead.",
    aZh: "一开始步子就太大了。我们用的是恒定学习率、没有预热，而且 MLX 还会把更新乘上固定的系数 20。40 步之内验证损失从 2.6 跳到 7.1，模型只会输出重复的标点。加预热也许有用，但我们没有测试。我们改为把学习率减半到 5e-5，反而得到了最好的结果。",
  },
  {
    who: LI,
    q: "How does the demo show both models without loading two models?",
    qZh: "演示里怎么不加载两个模型就能同时展示两种结果？",
    a: "LoRA's output is the original output plus a small extra term. If we set its scale to zero, the adapter is switched off, and the same model in memory behaves exactly like the base model. We switch it for each request, so we only need memory for one model.",
    aZh: "LoRA 的输出等于原来的输出再加上一个小的额外项。把它的系数设成 0，适配器就关掉了，内存里同一个模型就和原始模型完全一样。我们每个请求切换一次，所以只需要一个模型的内存。",
  },
];
