import json
import re
import sys
from pathlib import Path
from kiwipiepy import Kiwi

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import RAW_DATA, INTERIM, load_json, save_json

INPUT = RAW_DATA
OUTPUT = INTERIM / "preprocessed.json"

kiwi = Kiwi()

def normalize(text):
    # ㅋㅋㅋㅋ, ㅠㅠㅠ -> ㅋㅋ, ㅠㅠ
    text = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1+", r"\1\1", text)

    # 반복된 문장부호를 하나로 줄이기. 예: ,,, | ... -> , | .
    text = re.sub(r"([^\w\s])\1+", r"\1", text)

    # 분석에 방해되는 특수문자를 제거한다.
    text = re.sub(r"[^가-힣a-zA-Z0-9\s.,!?~]", "", text)

    # 문장부호 앞의 불필요한 공백을 제거.
    text = re.sub(r"\s+([.,!?~])", r"\1", text)

    # 여러 개의 공백을 하나로 줄이기.
    text = re.sub(r"\s+", " ", text).strip()
    return text

# 한 문장 안에 서로 다른 속성/감정이 섞이는 경우를 줄이기 위해 절 단위로 나눔.
# 특히 "비싸지만 맛있다"처럼 대조/양보 연결어가 있는 문장은 가격 부정과 맛 긍정을 분리해야 함.
CLAUSE_EC = {
    "지만", "는데", "ㄴ데", "은데",
    "아도", "어도", "여도", "더라도", "라도",
    "거나", "고", "며",
}

# 문장을 입력받아 CLAUSE_EC에 해당하는 연결어 기준으로 절을 나눔.
def clause_split(tokens):
    clauses = []
    current_clause = []

    for t in tokens:
        current_clause.append(t)
        if t.tag == 'EC' and t.form in CLAUSE_EC:
            clauses.append(current_clause)
            # 다음 절을 담기 위해 현재 절을 비우기.
            current_clause = []

    # 마지막에 남아 있는 절이 있으면 결과에 추가.
    if current_clause:
        clauses.append(current_clause)

    return clauses


def preprocess(data):
    dataset = []

    for rid, restaurant in data.items():
        for idx, review in enumerate(restaurant.get("reviews", [])):
            # 리뷰별 고유 식별자를 만들기.
            # 이후 aggregate.py에서 원본 메타데이터와 연결할 때 필요.
            rev_id = f"{rid}_{idx}"

            raw = review.get("content", "").strip()
            text = normalize(raw)
            if not text:
                continue

            # BERT 입력 길이 제한과 속성-감정 연결 정확도를 고려해 문장 단위로 먼저 나누고,
            sentences = kiwi.split_into_sents(text)
            for s_idx, sentence in enumerate(sentences):
                sentence_tokens = kiwi.tokenize(sentence.text)         
                split_clauses = clause_split(sentence_tokens)

                for c_idx, clause_tokens in enumerate(split_clauses):
                    # 절 단위로 나누면 원문 문장 형태가 사라지므로 Kiwi로 읽기 쉬운 절 텍스트를 복원.
                    # 학습용 핵심 입력은 아니고, 결과 확인을 쉽게 하기 위한 값.
                    clause_text = kiwi.join((t.form, t.tag) for t in clause_tokens)
                    
                    dataset.append({
                        "rev_id": rev_id,
                        "raw": clause_text,
                        "sentence_id": s_idx,
                        "clause_id": c_idx,
                        "clause_count": len(split_clauses),
                        "tokens": [f"{t.form}/{t.tag}" for t in clause_tokens],
                        "token_count": len(clause_tokens),
                    })
                                
    return dataset


# 전처리 결과를 새 JSON 파일로 저장.
def main():
    data = load_json(INPUT)
    token_data = preprocess(data)
    save_json(token_data, OUTPUT, 4)

if __name__ == "__main__":
    main()
