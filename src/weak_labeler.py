import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import INTERIM, load_json, save_json


INPUT_PREPROCESSED = INTERIM / "preprocessed.json"
INPUT_ASPECT_LEXICON = INTERIM / "aspect_lexicon.json"
INPUT_SENTIMENT_LEXICON = INTERIM / "sentiment_lexicon.json"
OUTPUT = INTERIM / "aspect_scores.json"

# 사전에 누락되면 점수가 크게 흔들리는 핵심 단어는 보완 목록으로 한 번 더 보강.
# Word2Vec 기준 단어가 데이터에 적게 등장해 속성 사전에서 빠지는 경우를 막기 위한 안전장치...
FALLBACK_ASPECT_KEYWORDS = {
    "맛": {"맛있", "맛없", "훌륭", "신선", "고소", "느끼", "달달", "매콤"},
    "서비스": {"친절", "불친절", "직원", "사장", "응대", "서비스"},
    "분위기": {"분위기", "인테리어", "공간", "편안", "깔끔", "예쁘"},
    "가격": {"가격", "가성비", "비싸", "저렴하", "싸", "혜자", "부담", "아깝"},
    "시스템": {"웨이팅", "예약", "대기", "자리", "주문", "포장", "브레이크"},
}

FALLBACK_SENTIMENT_SCORES = {
    "맛있": 0.90,
    "맛없": -0.90,
    "훌륭": 0.85,
    "최고": 0.90,
    "추천": 0.75,
    "좋": 0.65,
    "괜찮": 0.45,
    "친절": 0.80,
    "불친절": -0.85,
    "깔끔": 0.55,
    "예쁘": 0.55,
    "비싸": -0.80,
    "저렴하": 0.75,
    "싸": 0.55,
    "아쉽": -0.60,
    "실망": -0.85,
    "최악": -0.95,
}

NEGATION_WORDS = {"안", "못", "않", "별로"}
DEFAULT_WINDOW_SIZE = 3


def _split_token(token):
    if "/" not in token:
        return token, ""
    return token.rsplit("/", 1)


def _merge_aspect_lexicon(aspect_lexicon):
    merged = {aspect: set(words) for aspect, words in aspect_lexicon.items()}
    for aspect, words in FALLBACK_ASPECT_KEYWORDS.items():
        merged.setdefault(aspect, set()).update(words)
    return merged


def _merge_sentiment_lexicon(sentiment_lexicon):
    merged = {word: float(score) for word, score in sentiment_lexicon.items()}
    for word, score in FALLBACK_SENTIMENT_SCORES.items():
        merged.setdefault(word, float(score))
    return merged


def _build_word_to_aspects(aspect_lexicon):
    word_to_aspects = defaultdict(set)
    for aspect, words in aspect_lexicon.items():
        for word in words:
            word_to_aspects[word].add(aspect)
    return word_to_aspects


def _apply_negation(words, index, score):
    # "안 비싸다", "별로 친절하지 않다"처럼 앞쪽 부정 표현이 있으면 감정 방향을 뒤집음.
    previous_words = words[max(0, index - 2):index]
    if any(word in NEGATION_WORDS for word in previous_words):
        return -score
    return score


def score_aspect_sentiment(tokens, aspect_lexicon, sentiment_lexicon, window_size=DEFAULT_WINDOW_SIZE):
    """
    절 하나의 토큰 목록을 속성별 감정 점수로 변환.

    기존 방식은 절 안의 감정 점수를 평균낸 뒤 탐지된 모든 속성에 같은 점수를 넣었음.
    그러면 "가격은 비싸지만 맛은 훌륭" 같은 문장에서 가격과 맛이 같은 점수를 받게 됨.
    여기서는 감정 단어를 가장 가까운 속성에만 연결해서 속성별 감정이 섞이지 않게 함.
    """
    aspect_lexicon = _merge_aspect_lexicon(aspect_lexicon)
    sentiment_lexicon = _merge_sentiment_lexicon(sentiment_lexicon)
    word_to_aspects = _build_word_to_aspects(aspect_lexicon)

    words = [_split_token(token)[0] for token in tokens]
    aspect_positions = defaultdict(list)
    sentiment_positions = []

    for idx, word in enumerate(words):
        for aspect in word_to_aspects.get(word, set()):
            aspect_positions[aspect].append(idx)
        if word in sentiment_lexicon:
            sentiment_positions.append(idx)

    aspect_score_lists = defaultdict(list)
    assigned_pairs = set()

    def add_score(aspect, token_index, score):
        pair = (aspect, token_index)
        if pair not in assigned_pairs:
            aspect_score_lists[aspect].append(score)
            assigned_pairs.add(pair)

    for idx in sentiment_positions:
        word = words[idx]
        score = _apply_negation(words, idx, float(sentiment_lexicon[word]))

        # "비싸", "친절", "맛있"처럼 단어 자체가 속성과 감정을 함께 담으면 그 속성에 바로 연결.
        own_aspects = word_to_aspects.get(word, set())
        for aspect in own_aspects:
            add_score(aspect, idx, score)

        # 명시적인 속성 단어가 가까이 있으면 가장 가까운 속성에 감정을 연결.
        nearby_aspects = []
        for aspect, positions in aspect_positions.items():
            min_distance = min(abs(idx - pos) for pos in positions)
            if min_distance <= window_size:
                nearby_aspects.append((min_distance, aspect))

        if not nearby_aspects:
            continue

        nearest_distance = min(distance for distance, _ in nearby_aspects)
        for distance, aspect in nearby_aspects:
            if distance == nearest_distance:
                add_score(aspect, idx, score)

    aspect_scores = {}
    for aspect in aspect_lexicon.keys():
        scores = aspect_score_lists.get(aspect, [])
        aspect_scores[aspect] = round(float(np.mean(scores)), 4) if scores else None

    return aspect_scores


def run_absa():
    aspect_lexicon = load_json(INPUT_ASPECT_LEXICON)
    sentiment_lexicon = load_json(INPUT_SENTIMENT_LEXICON)
    reviews = load_json(INPUT_PREPROCESSED)

    output_results = []

    for rev in reviews:
        tokens = rev["tokens"]
        aspect_score = score_aspect_sentiment(tokens, aspect_lexicon, sentiment_lexicon)

        output_results.append({
            "rev_id": rev["rev_id"],
            "raw": rev["raw"],
            "tokens": tokens,
            "aspect_score": aspect_score,
        })

    save_json(output_results, OUTPUT, 4)
    print(f"Saved {len(output_results)} weak labels to {OUTPUT}")


if __name__ == "__main__":
    run_absa()
