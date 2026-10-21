"""老师标注、学生训练、评估都要用的公共部分：任务说明、输出格式、解析和打分。

把这些放在一个文件里，可以保证三个环节用的是同一套规则。
"""
import json
import re

# 固定的"方面"列表。限定成固定选项，模型输出才能和标准答案逐项比对、算分。
#
# 第二版（第一版存档在 runs/v1/common.py）。针对第一版暴露的问题做了三处改动：
#   1. 拆开过载的"质量"：分成 做工用料 / 故障瑕疵 / 正品真伪，并把"性能"改名为"使用效果"
#   2. 方面名直接用人自然会说的词组（口味口感、尺寸重量、位置交通、赠品配件），
#      第一版里老师自造的"口感""位置""交通""配件""重量"都有了明确的归宿
#   3. 增加"易混规则"，给每对容易混淆的方面划清界线
ASPECTS = {
    "使用效果": "产品正常使用时的表现：运行速度、流畅或卡顿、续航待机、屏幕、音质、信号、加热快慢、洗护效果、穿着舒适度、实用性",
    "做工用料": "做工、材质、面料、手感、耐用程度；书的印刷、纸张、排版、装订",
    "故障瑕疵": "收到时或使用中出现的损坏和缺陷：坏果烂果、磕碰压坏、死机黑屏、无法开机、按键失灵、开线、污渍、二手返修",
    "正品真伪": "仅当评论明确提到正品、假货、翻新、水货时使用",
    "价格": "价格高低、性价比、促销、降价、价格保护",
    "赠品配件": "赠品、配件、附件、发票、说明书是否齐全或好坏",
    "物流": "发货快慢、送货速度、快递员或配送员的态度",
    "服务": "商家客服、售后、退换货、安装师傅、酒店员工的态度和处理；发错货、少发货",
    "外观": "颜色、款式、设计、颜值、与图片是否一致",
    "尺寸重量": "商品的大小、尺码是否合身、重量、分量、个头",
    "口味口感": "食品饮料的味道、口感、新鲜度、甜度、保质期",
    "包装": "包装本身是否完好、美观、防护是否到位",
    "内容": "书籍或影音作品的内容、观点、文笔、翻译、知识性",
    "房间设施": "酒店的房间、卫生、设施、早餐、隔音、网络、房间大小",
    "位置交通": "酒店或店铺的地理位置、周边环境、交通是否方便",
    "其他": "品牌口碑、支持国产、购买渠道等；以上都不合适时才用",
}
SENTIMENTS = ("正面", "负面")

CONFUSION_RULES = [
    "只有完全不涉及具体属性的笼统评价（\"东西很好\"\"宝贝不错\"\"很满意\"\"垃圾\"）才不抽取；\"不卡\"\"流畅\"\"好用\"这类说到了具体表现的要抽取",
    "卡顿、慢、续航短、效果差 → 使用效果；死机、黑屏、坏了、无法使用 → 故障瑕疵",
    "耐用、做工粗糙、面料差 → 做工用料；穿着或使用舒服 → 使用效果；合身、尺码大小 → 尺寸重量",
    "包装破损 → 包装；包装里的商品被压坏 → 故障瑕疵",
    "快递员、配送员相关的一切 → 物流；商家客服、售后、发错货 → 服务",
    "送了或没送赠品、配件缺失 → 赠品配件，不算价格",
    "水果坏了、烂了 → 故障瑕疵；不新鲜、不甜、不脆 → 口味口感；水果个头大小 → 尺寸重量",
    "酒店房间小 → 房间设施，尺寸重量只用于商品",
    "方面名必须从列表中原样选择，不得使用列表外的词。常见对应：口感→口味口感，位置/交通→位置交通，配件/赠品→赠品配件，重量→尺寸重量，材质/手感→做工用料，品牌→其他",
]

SYSTEM_PROMPT = (
    "你是电商评论分析助手。阅读一条中文用户评论，抽取结构化信息，只输出一个 JSON 对象，不要输出其他文字。\n"
    "JSON 格式：{\"整体情感\": \"正面\"或\"负面\", \"方面\": [{\"方面\": 方面名, \"观点\": 评论原文中的短语, \"情感\": \"正面\"或\"负面\"}]}\n"
    "方面名只能从下面选：\n"
    + "\n".join(f"- {k}：{v}" for k, v in ASPECTS.items())
    + "\n易混规则：\n"
    + "\n".join(f"- {r}" for r in CONFUSION_RULES)
    + "\n其他规则：每个方面最多出现一次，同一方面有多个观点时只写最主要的一个；\"观点\"尽量摘自原文，不超过 15 个字；"
    "评论没有具体评价任何方面时，\"方面\"为空列表 []。"
)

# 标注示例：只给老师（和第二标注者）看，相当于给标注员的培训材料。
# 学生不看示例，它要通过训练数据学会这些规则。
EXAMPLES = [
    ("平板运行有点卡，用了一周就黑屏了，客服还推脱，送的皮套倒挺好",
     {"整体情感": "负面", "方面": [
         {"方面": "使用效果", "观点": "运行有点卡", "情感": "负面"},
         {"方面": "故障瑕疵", "观点": "用了一周就黑屏了", "情感": "负面"},
         {"方面": "服务", "观点": "客服还推脱", "情感": "负面"},
         {"方面": "赠品配件", "观点": "送的皮套倒挺好", "情感": "正面"}]}),
    ("宝贝不错，很满意，快递小哥态度好，就是价格偏贵",
     {"整体情感": "正面", "方面": [
         {"方面": "物流", "观点": "快递小哥态度好", "情感": "正面"},
         {"方面": "价格", "观点": "价格偏贵", "情感": "负面"}]}),
    ("酒店离地铁站很近，就是隔音太差，晚上很吵",
     {"整体情感": "负面", "方面": [
         {"方面": "位置交通", "观点": "离地铁站很近", "情感": "正面"},
         {"方面": "房间设施", "观点": "隔音太差", "情感": "负面"}]}),
    ("还没用，用了再来评价",
     {"整体情感": "正面", "方面": []}),
]


def build_messages(text: str, with_examples: bool = False):
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    if with_examples:
        for ex_text, ex_out in EXAMPLES:
            msgs.append({"role": "user", "content": f"评论：{ex_text}"})
            msgs.append({"role": "assistant", "content": to_target_json(ex_out)})
    msgs.append({"role": "user", "content": f"评论：{text}"})
    return msgs


def parse_output(raw: str):
    """把模型输出解析成合法的结果；格式不对就返回 None。"""
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.S).strip()
    match = re.search(r"\{.*\}", raw, flags=re.S)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if obj.get("整体情感") not in SENTIMENTS or not isinstance(obj.get("方面"), list):
        return None
    aspects, seen = [], set()
    for a in obj["方面"]:
        if not isinstance(a, dict):
            return None
        name, opinion, senti = a.get("方面"), a.get("观点"), a.get("情感")
        if name not in ASPECTS or senti not in SENTIMENTS or not isinstance(opinion, str):
            return None
        if name in seen:
            continue
        seen.add(name)
        aspects.append({"方面": name, "观点": opinion, "情感": senti})
    return {"整体情感": obj["整体情感"], "方面": aspects}


def to_target_json(result) -> str:
    """训练时学生要学会输出的那段文字（紧凑写法，省 token）。"""
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


def score(preds, golds, human_labels):
    """
    preds/golds: 解析后的结果列表（pred 可能为 None，表示格式错误）
    human_labels: 数据集自带的人工情感标签（1=正面，0=负面）

    返回四个指标：
      - JSON 合格率：输出能否被程序直接使用
      - 整体情感准确率：和人工标签比（真正的人工标准答案）
      - 方面 F1：(方面, 情感) 二元组和标准答案比对
      - 方面 F1（只看方面名）：不管情感对不对，只看找没找对方面
    """
    n = len(golds)
    valid = sum(p is not None for p in preds)
    senti_ok = sum(
        p is not None and p["整体情感"] == ("正面" if h == 1 else "负面")
        for p, h in zip(preds, human_labels)
    )

    def f1(key):
        tp = fp = fn = 0
        for p, g in zip(preds, golds):
            gs = {key(a) for a in g["方面"]}
            ps = {key(a) for a in p["方面"]} if p else set()
            tp += len(ps & gs)
            fp += len(ps - gs)
            fn += len(gs - ps)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        return 2 * prec * rec / (prec + rec) if prec + rec else 0.0

    return {
        "JSON合格率": valid / n,
        "整体情感准确率": senti_ok / n,
        "方面F1": f1(lambda a: (a["方面"], a["情感"])),
        "方面F1_只看方面名": f1(lambda a: a["方面"]),
    }
