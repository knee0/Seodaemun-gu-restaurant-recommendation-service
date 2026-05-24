import json
import re
from kiwipiepy import Kiwi
from src.utils import RAW_DATA, PREP, load_json, save_json

INPUT = RAW_DATA
OUTPUT = PREP / "preprocessed.json"

kiwi = Kiwi()

def normalize(text):
    # ㅋㅋㅋㅋ, ㅠㅠㅠ -> ㅋㅋ, ㅠㅠ
    text = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1+", r"\1\1", text)

    # 여러 개의 문장부호 하나로 줄이기 (예: ,,, | ... -> , | .)
    text = re.sub(r"([^\w\s])\1+", r"\1", text)

    # 분석에 방해되는 특수문자 제거.
    text = re.sub(r"[^가-힣a-zA-Z0-9\s.,!?~]", "", text)

    # 문장부호 주위의 불필요한 공백 제거.
    text = re.sub(r"\s+([.,!?~])", r"\1", text)

    # 여러 개의 공백 한 개로 줄이기.
    text = re.sub(r"\s+", " ", text).strip()
    return text

# 하나의 문장에 여러 개의 속성/감정이 담기는 경우를 줄이기 위해 절 단위로 분리.
# 대조/양보 연결어 기준으로 분류. (비싸'지만' 맛있다)
CLAUSE_EC = {"지만", "는데", "ㄴ데", "은데"}

# 문장을 입력 받아, CLAUSE_EC에 해당하는 연결어 기준으로 분리.
# 현재는 미사용: 사전 기반 점수 보니 불필요해 보임.
def clause_split(tokens):
    clauses = [[]]
    for t in tokens:
        clauses[-1].append(t)
        if t.tag == 'EC' and t.form in CLAUSE_EC:
            clauses.append([])
    return [clause for clause in clauses if clause]


def preprocess(data):
    dataset = []

    for rid, restaurant in data.items():
        for idx, review in enumerate(restaurant.get("reviews", [])):
            # 리뷰마다 고유 ID 만들기: 나중에 메타데이터와 연결할 때 활용.
            rev_id = f"{rid}_{idx}"

            raw = review.get("content", "").strip()
            text = normalize(raw)
            if not text: continue

            # 전체 리뷰는 여러 개의 속성/감정이 담겨 있으니, 문장 단위로 분리.
            # 감성과 무관한 문장이 너무 많이 생겨남: 리뷰 전체 사용하기
            # sentences = kiwi.split_into_sents(text)

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
