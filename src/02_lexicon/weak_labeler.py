import sys
from collections import defaultdict
import numpy as np
from src.utils import PREP, LEXICON, SCORES, load_json, save_json

INPUT = PREP / "preprocessed.json"
ASPECT_LEXICON = LEXICON / "aspect_lexicon.json"
SENTIMENT_LEXICON = LEXICON / "sentiment_lexicon.json"
OUTPUT = SCORES / "lexicon_scores.json"

# 의도는 이해되지만, 사전 관련 코드는 build_lexicon에 적어주세요!
# FALLBACK_ASPECT_KEYWORDS = {}
# FALLBACK_SENTIMENT_SCORES = {}

# NEGATION_WORDS = {"안", "못", "않"}
DEFAULT_WINDOW_SIZE = 3

# 감정 단어의 점수를 가장 가까운 속성에 부여: 각 절마다 속성별 점수 매기기.
def find_aspect_sentiment(words, aspect_lexicon, sentiment_lexicon,
                           find_aspect, window_size=DEFAULT_WINDOW_SIZE):

    # defaultdist는 일반 dict와 같지만, 없는 key를 자동으로 생성해주어 편리합니다.
    aspect_positions = defaultdict(list)
    sentiment_positions = []

    # 문장(array)에서 속성 사전, 감정 사전에 포함된 단어 위치(index) 찾기.
    for idx, word in enumerate(words):
        if word in find_aspect:
            aspect_positions[find_aspect[word]].append(idx)
        if word in sentiment_lexicon:
            sentiment_positions.append(idx)

    aspect_scores = defaultdict(list)

    for idx in sentiment_positions:
        word = words[idx]
        score = sentiment_lexicon[word]

        # NEGATION을 관리한다면, 단어 뒤로 오는 부정문도 고려해야 겠네요.
        #prev_words = words[max(0, idx-2) : idx]
        #if any(word in NEGATION_WORDS for word in prev_words):
        #    score = -score

        # 감정 단어가 속성 사전에도 있으면, 해당 속성에 바로 연결.
        if word in find_aspect:
            aspect_scores[find_aspect[word]].append(score)
            continue

        # 속성 사전에 없는 감정 단어면, 가장 가까운 속성 단어에 연결.
        closest_aspects = []
        for k in range(1, window_size + 1):
            left_idx = idx - k
            right_idx = idx + k
            left_find = (left_idx >= 0) and words[left_idx] in find_aspect
            right_find = (right_idx < len(words)) and words[right_idx] in find_aspect

            if not (left_find or right_find):
                continue
            if left_find:
                aspect = find_aspect[words[left_idx]]
                aspect_scores[aspect].append(score)
            if right_find:
                aspect = find_aspect[words[right_idx]]
                aspect_scores[aspect].append(score)
        
            break

    aspect_sentiment = []
    for aspect in aspect_lexicon.keys():
        if not aspect_scores[aspect]: continue
        mean_score = round(np.mean(aspect_scores[aspect]), 4)

        if mean_score >= 0.5:
            aspect_sentiment.append(f"{aspect}_긍정")
        elif mean_score <= -0.5:
            aspect_sentiment.append(f"{aspect}_부정")

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
