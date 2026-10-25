"""16 个方面的英文名。报告、图表、Gradio 界面都用这一份，保证三处叫法一致。

中文名仍然是模型输出和数据里的"正式"名字（见 scripts/common.py），英文只用于展示。
"""
ASPECT_EN = {
    "使用效果": "Performance",
    "做工用料": "Build & material",
    "故障瑕疵": "Defect",
    "正品真伪": "Authenticity",
    "价格": "Price",
    "赠品配件": "Gifts & accessories",
    "物流": "Logistics",
    "服务": "Service",
    "外观": "Appearance",
    "尺寸重量": "Size & weight",
    "口味口感": "Taste",
    "包装": "Packaging",
    "内容": "Content",
    "房间设施": "Room & facilities",
    "位置交通": "Location",
    "其他": "Other",
}
SENTIMENT_EN = {"正面": "positive", "负面": "negative"}
CATEGORY_EN = {
    "书籍": "Books", "平板": "Tablets", "手机": "Phones", "水果": "Fruit", "洗发水": "Shampoo",
    "热水器": "Water heaters", "蒙牛": "Dairy (Mengniu)", "衣服": "Clothing", "计算机": "Computers", "酒店": "Hotels",
}


def en(aspect: str) -> str:
    return ASPECT_EN.get(aspect, aspect)
