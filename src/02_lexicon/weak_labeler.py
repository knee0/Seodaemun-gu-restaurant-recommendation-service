import numpy as np
from src.utils import PREP, LEXICON, SCORES, load_json, save_json

INPUT = PREP / "preprocessed.json"
ASPECT_LEXICON = LEXICON / "aspect_lexicon.json"
SENTIMENT_LEXICON = LEXICON / "sentiment_lexicon.json"
OUTPUT = SCORES / "lexicon_scores.json"

# 감정 단어 주위를 얼마나 살펴볼 것인지 정의합니다. (3: 주위의 세 단어)
DEFAULT_WINDOW_SIZE = 5


# 감정 단어가 있으면, 단어의 '감정 점수'를 가장 가까운 카테고리 단어의 '카테고리'에 부여합니다.
def find_aspect_sentiment(words, aspect_lexicon, sentiment_lexicon,
                           find_aspect, window_size=DEFAULT_WINDOW_SIZE):

    # 감정 단어의 위치(index)를 저장.
    sentiment_positions = []

    # 문장에서 감정 단어, 카테고리 단어의 위치(index) 찾기.
    for idx, word in enumerate(words):
        if word in sentiment_lexicon:
            sentiment_positions.append(idx)

    aspect_scores = {aspect: [] for aspect in aspect_lexicon.keys()}

    for idx in sentiment_positions:
        word = words[idx]
        score = sentiment_lexicon[word]


        # 감정 단어가 카테고리 단어라면, 해당 카테고리에 바로 연결.
        if word in {"맛있", "맛나", "맛없"}:
            aspect_scores["음식"].append(score)
            continue

        # 다른 감정 단어는 가장 가까운 카테고리 단어의 카테고리와 연결.
        closest_aspects = []
        for k in range(1, window_size + 1):
            left_idx = idx - k
            right_idx = idx + k
            left_find = (left_idx >= 0) and words[left_idx] in find_aspect
            right_find = (right_idx < len(words)) and words[right_idx] in find_aspect

            # k 주위의 단어까지 발견되지 않았다면, 다음 단어 탐색
            if not (left_find or right_find):
                continue

            # 발견된 경우, 발견된 단어의 카테고리에 점수 부여.
            if left_find:
                aspect = find_aspect[words[left_idx]]
                aspect_scores[aspect].append(score)
            if right_find:
                aspect = find_aspect[words[right_idx]]
                aspect_scores[aspect].append(score)
            
            # 발견된 경우, 거기서 탐색 종료.
            break


    # 여기까지 코멘트 작성.
    aspect_sentiment = []
    for aspect in aspect_lexicon.keys():
        if not aspect_scores[aspect]: continue
        mean_score = round(np.mean(aspect_scores[aspect]), 4)

        if mean_score >= 0.75:
            aspect_sentiment.append(f"{aspect}_긍정")
        elif mean_score <= -0.75:
            aspect_sentiment.append(f"{aspect}_부정")
        else:
            pass

    return aspect_sentiment


def run_absa():
    reviews = load_json(INPUT)
    raw_aspect_lexicon = load_json(ASPECT_LEXICON)
    raw_sentiment_lexicon = load_json(SENTIMENT_LEXICON)

    # 사용하기 편한 형태로 .json 데이터 조작하기
    aspect_lexicon = {aspect: set(words) for aspect, words in raw_aspect_lexicon.items()}
    sentiment_lexicon = {word: float(score) for word, score in raw_sentiment_lexicon.items()}

    # Aspect Lexicon은 '속성: 단어' 형태. ('맛': 맛있, 맛없, ...)
    # '단어 -> 속성' 관계를 빨리 찾기 위해 역순서 사전 만들기 ('맛있': 맛, '맛없': 맛, ...)
    find_aspect = {}
    for aspect, words in aspect_lexicon.items():
        for word in words:
            find_aspect[word] = aspect

    final_results = []
    for rev in reviews:
        tokens = rev["tokens"]
        words = [token.partition('/')[0] for token in tokens]
        aspect_sentiment = find_aspect_sentiment(words, aspect_lexicon, sentiment_lexicon, find_aspect)

        final_results.append({
            "rev_id": rev["rev_id"],
            "raw": rev["raw"],
            "tokens": tokens,
            "labels": aspect_sentiment,
        })

    save_json(final_results, OUTPUT)

if __name__ == "__main__":
    run_absa()
