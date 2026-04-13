from collections import Counter
from pathlib import Path
import json
import re

all_tags = []

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
NO_ASP = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "01_sentence_split.json"
WITH_ASP = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "02_aspects_added.json"

# Rules made from popular tags
ASPECT_RULES = {
    "taste": ["맛있", "맛이에요", "반찬", "안주", "코스"],
    "quality": ["신선", "질", "잡내", "건강", "현지", "향신료"],
    "portion": ["양", "푸짐"],
    "service": ["친절", "빨리", "잘해줘", "상담", "직접"],
    "price": ["가성비", "비싼 만큼", "합리적"],
    "atmosphere": ["인테리어", "분위기", "아늑", "음악", "뷰",
        "컨셉", "오래", "사진", "잘 나와", "고급", "트렌디", "특별"],
    "space": ["넓", "좌석", "주차", "야외공간", "룸"],
    "variety": ["다양", "구성", "종류"],
    "hygiene": ["청결", "깨끗", "깔끔"],
    "experience": ["혼밥", "대화", "모임", "혼술",
        "아이와", "집중", "데이트"]
}

# Basic preprocess: remove non-Korean text
def normalize_text(text):
    text = re.sub(r"[^가-힣0-9 ]", "", text)
    return text

# Make aspects from tags
def tag_to_aspect(tag):
    for aspect, keywords in ASPECT_RULES.items():
        for kw in keywords:
            if kw in tag: return aspect
    return "other"

# Make new attribute 'review_aspects'
def add_aspects(data):
    for row in data:
        aspects = set()

        for tag in row.get("tags", []):
            aspect = tag_to_aspect(tag)
            aspects.add(aspect)

        row["review_aspects"] = list(aspects)

    return data

# Make aspects from sentences
def sentence_has_aspects(sentence, aspect, aspect_rules):
    sentence = normalize_text(sentence)
    keywords = aspect_rules.get(aspect, [])

    return any(kw in sentence for kw in keywords)

# Make new attribute 'sentence_aspects'
def add_sentence_aspects(data, aspect_rules):
    for row in data:
        sentence = row["sentence"]
        detected_aspects = []

        for aspect in row.get("review_aspects", []):
            if sentence_has_aspects(sentence, aspect, aspect_rules):
                detected_aspects.append(aspect)

        row["sentence_aspects"] = detected_aspects

    return data

# Write new .json
def main():
    with open(NO_ASP, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = add_aspects(data)
    data = add_sentence_aspects(data, ASPECT_RULES)

    
    with open(WITH_ASP, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

