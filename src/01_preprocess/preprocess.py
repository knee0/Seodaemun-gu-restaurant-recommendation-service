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
CLAUSE_EC = {
    "지만", "는데", "ㄴ데", "은데","아도", "어도", "여도", 
    "더라도", "라도", "거나", "고", "며",
}

# 문장을 입력 받아, CLAUSE_EC에 해당하는 연결어 기준으로 분리.
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
            sentences = kiwi.split_into_sents(text)

            for s_idx, sentence in enumerate(sentences):
                # 각 문장을 토큰화    
                sentence_tokens = kiwi.tokenize(sentence.text)
                # 토큰화한 문장을 절 단위로 분리.
                split_clauses = clause_split(sentence_tokens)

                for c_idx, clause_tokens in enumerate(split_clauses):
                    # 절 단위로 나누면서 원문 리뷰 소실.
                    # kiwi.join으로 토큰화된 절을 자연어로 복원. (읽기 편하도록)
                    clause_text = kiwi.join((t.form, t.tag) for t in clause_tokens)
                    
                    # 이거 3개 말고는 필요 없지 않나요? 메타데이터 연결할 때도 rev_id만 있으면 되니.
                    # metadata.py로 메타데이터 전용 .json을 따로 만들죠! preprocessed는 학습할 것만 남기고.
                    dataset.append({
                        "rev_id": rev_id,
                        "raw": clause_text,
                        "tokens": [f"{t.form}/{t.tag}" for t in clause_tokens],
                    })
                                
    return dataset


def main():
    data = load_json(INPUT)
    token_data = preprocess(data)
    save_json(token_data, OUTPUT, 4)

if __name__ == "__main__":
    main()
