import json
import re
from kiwipiepy import Kiwi
from src.utils import RAW_DATA, PREP, load_json, save_json

INPUT = RAW_DATA
OUTPUT = PREP / "preprocessed.json"

kiwi = Kiwi()

def normalize(text):
    # 여러 개의 자음 하나로 줄이기 (ㅋㅋㅋㅋ, ㅠㅠㅠ -> ㅋㅋ, ㅠㅠ)
    text = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1+", r"\1\1", text)

    # 한글, 숫자, [.,!?~] 외의 특수문자 제거.
    text = re.sub(r"[^가-힣0-9\s.,!?~]", "", text)

    # 문장부호 주위의 불필요한 공백 제거.
    text = re.sub(r"\s+([.,!?~])", r"\1", text)

    # 여러 개의 공백 하나로 줄이기.
    text = re.sub(r"\s+", " ", text).strip()
    return text


# 리뷰를 잘게 나누다 보니 맥락을 알 수 없는 문장이 너무 많이 생겨나서,
# 문장 분리와 절 분리는 안 하는 편이 나을 것 같습니다.


def preprocess(data):
    dataset = []

    for rid, restaurant in data.items():
        for idx, review in enumerate(restaurant.get("reviews", [])):

            # 리뷰마다 고유 ID 저장: 이후 메타데이터와 연결할 때 활용.
            rev_id = f"{rid}_{idx}"

            raw = review.get("content", "").strip()
            text = normalize(raw)

            if not text or len(text) <= 1:
                continue

            review_tokens = kiwi.tokenize(text)
            dataset.append({
                    "rev_id": rev_id,
                    "raw": text,
                    "tokens": [f"{t.form}/{t.tag}" for t in review_tokens],
            })
                                
    return dataset


def main():
    data = load_json(INPUT)
    token_data = preprocess(data)
    save_json(token_data, OUTPUT)

if __name__ == "__main__":
    main()
