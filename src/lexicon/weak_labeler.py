import numpy as np
from kiwipiepy import Kiwi
from src.utils import PREP, LEXICON, SCORES, load_json, save_json

INPUT = PREP / "preprocessed.json"
ASPECT_LEXICON = LEXICON / "aspect_lexicon.json"
SENTIMENT_LEXICON = LEXICON / "sentiment_lexicon.json"
SPECIFIC_MAP = LEXICON / "specific_sentiment_map.json"
OUTPUT = SCORES / "lexicon_scores.json"

def make_key(word, tag):
    return f"{word}/{tag}" if tag.startswith('N') else word

# 감정 단어 주위를 얼마나 살펴볼 것인지 정의합니다. (3: 주위의 세 단어)
DEFAULT_WINDOW_SIZE = 5

# 감정 단어가 있으면, 단어의 '감정 점수'를 가장 가까운 카테고리 단어의 '카테고리'에 부여합니다.
def find_aspect_sentiment(raw_text, aspect_lexicon, sentiment_lexicon, find_aspect,
    specific_sentiment_map, kiwi, window_size=DEFAULT_WINDOW_SIZE):

    kiwi_sents = kiwi.split_into_sents(raw_text)
    review_aspect_scores = {aspect: [] for aspect in aspect_lexicon.keys()}

    for sent in kiwi_sents:
        tokens = kiwi.tokenize(sent.text)

        valid_indices = [
            i for i, t in enumerate(tokens) 
            if not (t.tag.startswith('J') or t.tag.startswith('S'))
        ]

        boundary_indices = {
            i for i, t in enumerate(tokens)
            if (t.form in ['지만', '는데', '으나'])
        }

        # start, end 사이에 절이 달라지는지 검사합니다.
        def is_blocked(start, end):
            s, e = min(start, end), max(start, end)
            return any(s <= b <= e for b in boundary_indices)

        last_seen_aspect = None
        last_seen_aspect_idx = -1

        sentiment_positions = []
        for i in valid_indices:
            t = tokens[i]
            combined_word = make_key(t.form, t.tag)
            if combined_word in sentiment_lexicon or combined_word in specific_sentiment_map:
                sentiment_positions.append(i)

        valid_idx_to_pos = {idx: pos for pos, idx in enumerate(valid_indices)}

        for idx in sentiment_positions:
            token = tokens[idx]
            combined_word = make_key(token.form, token.tag)

            # 반전 표현이 나오면 감정을 뒤집습니다. (긍정 -> 부정)
            neg_left, neg_right = False, False
            for i in range(max(0, idx - 3), idx):
                if (tokens[i].form == "안" and tokens[i].tag == "MAG"):
                    neg_left = True
            # 뒤에 '않다', '없다' 검사
            for i in range(idx + 1, min(len(tokens), idx + 4)):
                if tokens[i].form in ["않", "없", "없이"] or (tokens[i].form == "안" and tokens[i].tag == "MAG"):
                    neg_right = True

            is_negated = neg_left or neg_right


            if combined_word in specific_sentiment_map:
                aspect, polarity = specific_sentiment_map[combined_word].split('_')
                
                # 감정 사전에 있으면 그 점수의 크기(magnitude)를 쓰고, 없으면 확실한 기본값(1.0) 부여
                base_score = sentiment_lexicon.get(combined_word, 1.0)
                score_magnitude = max(abs(base_score), 0.5) # 최소한의 감정 세기 보장
                
                assigned_score = score_magnitude if polarity == "긍정" else -score_magnitude
                if is_negated: assigned_score = -assigned_score

                review_aspect_scores[aspect].append(assigned_score)
                last_seen_aspect = aspect
                last_seen_aspect_idx = idx
                continue 


            score = sentiment_lexicon[combined_word]
            if is_negated: score = -score


            # 일반 감정 단어의 경우, 가장 가까운 속성 단어를 탐색합니다.
            current_pos = valid_idx_to_pos[idx]
            aspect_found = False

            for k in range(1, window_size + 1):
                for next_pos in [current_pos - k, current_pos + k]:
                    if 0 <= next_pos < len(valid_indices):
                        near_idx = valid_indices[next_pos]
                        near_token = tokens[near_idx]
                        near_combined = make_key(near_token.form, near_token.tag)
                        
                        if near_combined in find_aspect:
                            if not is_blocked(idx, near_idx):
                                aspect = find_aspect[near_combined]
                                review_aspect_scores[aspect].append(score)
                                last_seen_aspect = aspect
                                last_seen_aspect_idx = near_idx
                                aspect_found = True
                                break
                if aspect_found:
                    break


            # 문장 내에서 마지막으로 발견된 속성을 last_seen_aspect에 저장합니다. 
            # 이번 감성 단어 주변에 속성 단어가 없었다면, 이전 속성에 감정 점수를 부여합니다.
            if not aspect_found and last_seen_aspect:
                # 중간에 절 분리 단어가 있으면, 해당 속성으로 연결하지 않습니다.
                if not is_blocked(last_seen_aspect_idx, idx):
                    review_aspect_scores[last_seen_aspect].append(score)
                last_seen_aspect = None


    # 위의 과정을 거치면, 리뷰마다 속성별로 다양한 점수를 갖게 됩니다.
    # 예) 음식: [0.7, 0.5, 0.6], 서비스: [0.1, -0.4, -0.3]
    # 해당 점수의 평균값으로 리뷰의 속성별 감정 점수를 계산합니다.
    aspect_sentiment = {}
    for aspect in aspect_lexicon.keys():
        scores = review_aspect_scores[aspect]
        pos_scores = [s for s in scores if s > 0]
        neg_scores = [s for s in scores if s < 0]

        aspect_sentiment[f"{aspect}_긍정"] = round(np.mean(pos_scores), 4) if pos_scores else 0.0
        aspect_sentiment[f"{aspect}_부정"] = round(abs(np.mean(neg_scores)), 4) if neg_scores else 0.0

    return aspect_sentiment


def run_absa():
    reviews = load_json(INPUT)
    raw_aspect_lexicon = load_json(ASPECT_LEXICON)
    raw_sentiment_lexicon = load_json(SENTIMENT_LEXICON)
    specific_sentiment_map = load_json(SPECIFIC_MAP)

    # 사용하기 편한 형태로 .json 데이터 조작하기
    aspect_lexicon = {aspect: set(words) for aspect, words in raw_aspect_lexicon.items()}
    sentiment_lexicon = {word: float(score) for word, score in raw_sentiment_lexicon.items()}
    find_aspect = {word: aspect for aspect, words in aspect_lexicon.items() for word in words}
    kiwi = Kiwi()

    final_results = []
    for rev in reviews:
        raw_text = rev["raw"]

        aspect_sentiment = find_aspect_sentiment(
            raw_text=raw_text, aspect_lexicon=aspect_lexicon, sentiment_lexicon=sentiment_lexicon, 
            find_aspect=find_aspect, specific_sentiment_map=specific_sentiment_map, kiwi=kiwi
        )

        final_results.append({
            "rev_id": rev["rev_id"],
            "raw": rev["raw"],
            "tokens": rev["tokens"],
            "labels": aspect_sentiment,
        })

    save_json(final_results, OUTPUT)

if __name__ == "__main__":
    run_absa()
