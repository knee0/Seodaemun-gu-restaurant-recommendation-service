import json
import re
import sys
from pathlib import Path
import numpy as np
from gensim import corpora
from gensim.models import Word2Vec
from gensim.models.phrases import Phraser

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import INTERIM, load_json, save_json

INPUT = INTERIM / "preprocessed.json"
OUTPUT_ASP = INTERIM / "aspect_lexicon.json"
OUTPUT_SEN = INTERIM / "sentiment_lexicon.json"

data = load_json(INPUT)

# scripts/common_pos.py로 확인한 주요 일반명사/고유명사를 바탕으로 만든 초기 Seed Lexicon.
# 맛 카테고리는 음식명과 메뉴명이 다양하게 등장하므로 다른 카테고리보다 기준 단어를 넓게 잡았음.
# 결과를 확인하면서 프로젝트 데이터에 맞게 계속 조정할 수 있음.
seed_lexicon = {
    "맛": [
        "맛있", "맛없", "훌륭", "메뉴", "요리", "신선", "맛집", "음식", "고기", "식사", "커피",
        "국물", "소스", "안주", "파스타", "치즈", "맥주", "반찬", "재료", "튀김", "치킨",
        "피자", "김치", "디저트", "와인", "초밥", "볶음밥", "떡볶이", "음료", "샐러드",
        "우동", "양념", "짬뽕", "만두", "김밥", "크림", "새우", "연어", "사이드", "브런치",
        "계란찜", "라떼", "닭발", "밀크티", "시그니처", "마라탕", "로제", "훠궈", "닭강정",
        "커리", "도우", "마라", "초코", "마파두부", "계란말이", "라자냐", "와플", "바질", 
        "티라미수", "가라아게", "소바", "닭볶음탕", "스콘", "칠리", "게장", "패티", "말차",
        "화과자", "쫄면", "떡갈비", "프라이", "바닐라", "딤섬", "대창", "백김치", "김치전",
        "타코", "팟타이", "비프", "휘낭시에", "신라면", "스키야키"
    ],
    "서비스": ["친절", "불친절", "사장", "직원", "서비스", "감사", "리필", "주문", "포장"],
    "분위기": [
        "분위기", "매장", "느낌", "인테리어", "편안", "깔끔", "예쁘", "가게", "데이트", "공간",
        "테이블", "모임", "대화", "장소", "이자카야", "포차"
    ],
    "가격": ["가성비", "가격", "저렴하", "싸", "비싸", "혜자", "부담", "아깝", "결제", "구성", "퀄리티"],
    # 자주 등장하는 명사를 보니 웨이팅/예약 같은 이용 흐름도 중요해서 시스템 카테고리로 분리.
    # 데이터 분포를 보면서 필요한 단어를 계속 보완해야 할듯...
    "시스템": ["예약", "웨이팅", "대기", "타임", "브레이크", "시간", "자리", "점심", "저녁", "런치"]
}

# 긍정/부정 기준 단어로 감정 방향의 기준점을 만들기.
# Word2Vec 공간에서 이 단어들과 가까운 단어를 찾아 감정 사전을 확장.
pos_seeds = ["맛있", "최고", "추천", "친절", "훌륭", "저렴하", "맛나", "좋아하", "편하", "괜찮"]
neg_seeds = ["맛없", "비싸", "불친절", "힘들", "나쁘", "느끼하", "실망", "아쉽", "최악"]

# 핵심 기준 단어는 Word2Vec 정규화 과정에서 값이 흐려지지 않도록 최종 Sentiment Lexicon에 고정값으로 보강.
SENTIMENT_OVERRIDES = {
    "맛있": 0.90,
    "맛없": -0.90,
    "훌륭": 0.85,
    "최고": 0.90,
    "추천": 0.75,
    "친절": 0.80,
    "불친절": -0.85,
    "비싸": -0.80,
    "저렴하": 0.75,
    "싸": 0.55,
    "아쉽": -0.60,
    "실망": -0.85,
    "최악": -0.95,
}

# 시스템 카테고리에 자주 섞여 들어왔지만 추천 점수에는 큰 의미가 없는 단어들.
stopwords = {
    "월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일",
    "주말", "평일", "오전", "오후", "낮시간", "저녁시간", "새벽"
}


allowed_tags = {"VV", "VA", "MAG", "NNG", "NNP"}

# "단어/품사" 형태의 토큰에서 단어 부분만 꺼내 Word2Vec 학습 문서를 만들기.
cleaned_docs = []
for rev in data:
    doc = []
    for t in rev["tokens"]:
        word = t.split("/")[0]
        cleaned_word = re.sub(r'\d+','', word)
        if len(cleaned_word) > 1 and word not in stopwords:
            doc.append(cleaned_word)
    if doc: cleaned_docs.append(doc)

# Word2Vec 모델을 정의한다. 한국어 Word2Vec 관련 선행 설정을 참고해 스킵그램 방식을 사용.
w2v_model = Word2Vec(
    sentences=cleaned_docs,
    vector_size=300,
    window=7,
    sg=1,
    min_count=2,
    workers=1,
    seed=42,
)

# 기준 단어는 실제 데이터에서 Word2Vec 어휘로 학습된 단어만 사용 가능.
valid_pos = [w for w in pos_seeds if w in w2v_model.wv]
valid_neg = [w for w in neg_seeds if w in w2v_model.wv]

if not valid_pos or not valid_neg:
    raise ValueError(
        f"Word2Vec vocab에 유효한 감정 seed가 부족합니다. "
        f"valid_pos={valid_pos}, valid_neg={valid_neg}"
    )

p_avg = np.mean([w2v_model.wv[w] for w in valid_pos], axis=0)
n_avg = np.mean([w2v_model.wv[w] for w in valid_neg], axis=0)

sentiment_lexicon = {}
sentiment_nng = {"가성비", "만족", "감사", "행복", "기분", "퀄리티"}
sentiment_mag = {'너무', '진짜', '정말', '엄청', '완전', '아주', '너무너무', '굉장히', '매우',
                 '자주', '항상', '매번', '종종', '매일', '역시', '제대로', '가득', '듬뿍', '무조건', '별로'}
sentiment_vv = {'좋아하', '느끼', '즐기', '생각나', '미치', '놀라', '땡기',  '어울리', '터지'}

# 단어별 품사 정보를 모아 Sentiment Lexicon에 넣을 후보를 거를 때 사용.
word_to_tag = {}
for rev in data:
    for t in rev["tokens"]:
        word, tag = t.split("/")
        word_to_tag[word] = tag


# Word2Vec 어휘의 각 단어에 감정 점수를 부여.
for word in w2v_model.wv.index_to_key:
    word_tag = word_to_tag.get(word, "")

    is_allowed_tag = any(tag in word_tag for tag in allowed_tags)
    if "VV" in word_tag and word not in sentiment_vv:
        continue
    if "NNG" in word_tag and word not in sentiment_nng:
        continue
    if "MAG" in word_tag and word not in sentiment_mag:
        continue
    if "NNP" in word_tag:
        continue
    if not is_allowed_tag:
        continue
    
    w_vec = w2v_model.wv[word]

    # 긍정 기준점/부정 기준점과의 코사인 유사도 차이를 감정 점수로 사용.
    sim_p = np.dot(w_vec, p_avg) / (np.linalg.norm(w_vec) * np.linalg.norm(p_avg))
    sim_n = np.dot(w_vec, n_avg) / (np.linalg.norm(w_vec) * np.linalg.norm(n_avg))
    sentiment_lexicon[word] = float(sim_p - sim_n)

scores = np.array(list(sentiment_lexicon.values()))
if len(scores) == 0:
    raise ValueError("Sentiment Lexicon 후보 단어가 없습니다. allowed_tags 또는 seed를 확인해 주세요.")

mean_s, std_s = np.mean(scores), np.std(scores)
if std_s == 0:
    std_s = 1.0

for word, score in sentiment_lexicon.items():
    z_score = (score - mean_s) / std_s
    sentiment_lexicon[word] = float(np.tanh(z_score))

for word, score in SENTIMENT_OVERRIDES.items():
    if word in w2v_model.wv or word in word_to_tag:
        sentiment_lexicon[word] = float(score)


neg_count, neu_count, pos_count = 0, 0, 0
total_words = len(sentiment_lexicon)
# 부정 단어가 상대적으로 적은지 확인하기 위해 점수 분포를 출력.
# 현재 기준에서는 강한 부정 구간을 좁게 잡아 분포를 확인.
for word, score in sentiment_lexicon.items():
    if -1.0 <= score < -0.75: neg_count += 1;
    elif -0.75 <= score <= 0.75: neu_count += 1;
    elif 0.75 <= score <= 1.0: pos_count += 1;

# Lexicon의 점수 분포를 출력.
print("\n=== LEXICON DISTRIBUTION ===")
print(f"Negative [-1.00 ~ -0.75] : {neg_count} words ({neg_count/total_words*100:.1f}%)")
print(f"Neutral  [-0.75 ~  0.75] : {neu_count} words ({neu_count/total_words*100:.1f}%)")
print(f"Positive [ 0.75 ~  1.00] : {pos_count} words ({pos_count/total_words*100:.1f}%)")
print(f"Total Vocabulary Size    : {total_words} words")

# 감정 점수를 기준으로 단어 정렬.
sorted_lexicon = sorted(sentiment_lexicon.items(), key=lambda item: item[1], reverse=True)

print("=== TOP 20 POSITIVE WORDS ===")
for word, score in sorted_lexicon[:20]:
    print(f"{word}: {score:.4f}", end=" ")

print("\n=== TOP 20 NEGATIVE WORDS ===")
for word, score in sorted_lexicon[-20:]:
    print(f"{word}: {score:.4f}", end=" ")

expanded_lexicon = {}
word_best_category = {}
word_best_score = {}
SIMILAR_THRESHOLD = 0.50

# 속성 기준 단어는 반드시 해당 카테고리에 포함되도록 가장 높은 유사도 점수를 주기.
for category, seeds in seed_lexicon.items():
    for seed in seeds:
        if seed in w2v_model.wv:
            word_best_score[seed] = 1.0
            word_best_category[seed] = category

for category, seeds in seed_lexicon.items():
    valid_seeds = [s for s in seeds if s in w2v_model.wv]
    if not valid_seeds: print(f"No valid seeds for {category}!")

    raw_similars = w2v_model.wv.most_similar(positive=valid_seeds, topn=100)

    for word, score in raw_similars:
        if score >= SIMILAR_THRESHOLD: # 음식 접미사 필터가 필요하면 여기에서 추가로 적용.
            if score > word_best_score.get(word, -1.0):
                word_best_score[word] = score
                word_best_category[word] = category
    
expanded_lexicon = {cat: [] for cat in seed_lexicon}
for word_tag, cat in word_best_category.items():
        expanded_lexicon[cat].append(word_tag)

# Expanded Lexicon 결과 확인.
for cat, words in expanded_lexicon.items():
    print(f"[{cat}]: {len(words)} words found.")
    print(f"{', '.join(words[:20])} ...\n")

save_json(expanded_lexicon, OUTPUT_ASP, 4)
save_json(sentiment_lexicon, OUTPUT_SEN, 4)
