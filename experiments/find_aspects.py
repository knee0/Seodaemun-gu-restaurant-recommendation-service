from collections import Counter
from pathlib import Path
import json

all_tags = []

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
SENTENCES = PROJECT_ROOT / "data" / "processed" / "01_sentence_split.json"

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

def tag_to_aspect(tag):
    for aspect, keywords in ASPECT_RULES.items():
        for kw in keywords:
            if kw in tag: return aspect
    return "other"

def aspect_distribution(data):
    aspect_counter = Counter()

    for row in data:
        tags = row.get("tags", [])
        for tag in tags:
            aspect = tag_to_aspect(tag)
            aspect_counter[aspect] += 1

    return aspect_counter

def unmapped_tags(data):
    unmapped = Counter()

    for row in data:
        for tag in row.get("tags", []):
            if tag_to_aspect(tag) == "other":
                unmapped[tag] += 1

    return unmapped

def main():
    with open(SENTENCES, "r", encoding="utf-8") as f:
        data = json.load(f)

    aspect_counts = aspect_distribution(data)
    unmapped = unmapped_tags(data)

    print("Aspect Distribution")
    for aspect, count in aspect_counts.most_common():
        print(f"{aspect:12}: {count}")

    print("Most Unmapped Tags:")
    for tag, count in unmapped.most_common(20):
        print(f"{tag}: {count}")

if __name__ == "__main__":
    main()

