import json
import re
import numpy as np
from gensim import corpora
from gensim.models import Word2Vec
from gensim.models.phrases import Phraser
from src.utils import PREP, LEXICON, load_json, save_json

INPUT = PREP / "preprocessed.json"
OUTPUT_ASP = LEXICON / "aspect_lexicon.json"
OUTPUT_SEN = LEXICON / "sentiment_lexicon.json"

data = load_json(INPUT)

# scripts/common_pos.py을 참고하여, 주요 명사/형용사/동사를 바탕으로 기준 단어를 정의합니다.
# Word2Vec은 모든 단어를 분석하여, 기준 단어와의 유사도를 찾아줍니다.


seed_lexicon = {
    "음식": [
        "맛", "음식", "메뉴", "맛집", "식사", "요리", "종류", "구성",
        "양", "배부르", "푸짐하", "알차", "든든하",
        "맛있", "맛나", "진하", "매콤하", "고소하", "달달하", "쫀득하", "담백하",
    ],
    "서비스": [
        "친절", "사장", "직원", "기분", "추가", "서비스", "리필", "감사", "만족", "응대", "친절하", "배려"
    ],
    "분위기": [
        "분위기", "느낌", "인테리어", "데이트", "편안", "매장", "힐링", "레트로", "예쁘", "이쁘", "멋지", "추억"
    ],
    "가격": [
        "가성비", "가격", "혜자", "저렴하", "비싸", "싸"
    ],
    "편의성": [
        "시간", "예약", "가능", "편하", "편리", "주차", "주차장", "화장실", "청결", "깨끗", 
        "웨이팅", "대기", "줄", "시간", "브레이크", "타임", "시설", "유아용", "아기의자", "반려동물"
    ]
}


# 감정 사전의 기준 단어입니다.
pos_seeds = [
    "맛있", "좋", "많", "맛나", "편하", "넓", "괜찮", "예쁘", "크", "배부르", "이쁘", 
    "저렴하", "착하", "알차", "재밌", "든든하", "멋지", "빠르", "푸짐하", "야무지", 
    "재미있", "실하", "기쁘", "멋있", "알맞", "좋아하", "즐기", "어울리", "생각나", 
    "땡기", "어우러지", "끝내주", "반하", "맛집", "친절", "감사", "깔끔", "혜자",
    "짱", "제대로", "가득", "듬뿍", "바삭", "야들야들"
]
neg_seeds = [
    "늦", "적", "작", "비싸", "힘들", "느끼하", "나쁘", "질기", "과하", "비리", "맛없", "싫", "지옥",
    "퍽퍽하", "정신없", "속상하", "질리", "물리", "싫어하", "상하", "별로", "그닥", "전혀", "아예", "최악"
]


# 의미 없는 단어들. 적극적으로 추가하진 않았습니다.
stopwords = {
    "빨갛", "야쿠르트", "오용", "미션", "내년", "진행자"
}


# 각 단어를 '맛있/NNG' 형태로 저장하여, word를 추출하여 리스트에 저장하고, 
# 각 word의 tag를 구하기 쉽도록 {word: tag} dict를 만듭니다.
cleaned_docs, word_to_tag = [], {}

for rev in data:
    doc = []
    for t in rev["tokens"]:
        word, tag = t.split("/")
        cleaned_word = re.sub(r'\d+','', word)

        if word not in stopwords:
            word_to_tag[word] = tag
            doc.append(cleaned_word)
    if doc:
        cleaned_docs.append(doc)


# Parameter는 '워투벡 사용법.pdf'을 참고했습니다. (Notion - 참고 문헌)
w2v_model = Word2Vec(
    sentences=cleaned_docs,
    vector_size=300,
    window=7,
    sg=1,
    min_count=2, # 1로 하면 온갖 오타와 신조어가 있을 것 같아 2로 설정했습니다.
    workers=1,
    seed=42,
)


# Word2Vec 모델이 학습하지 못한 단어는 기준 단어로 활용할 수 없습니다.
# 리뷰에 자주 등장하는 단어를 기준 단어로 활용한 만큼, 불필요한 과정이긴 합니다.
valid_pos = [w for w in pos_seeds if w in w2v_model.wv]
valid_neg = [w for w in neg_seeds if w in w2v_model.wv]
if not valid_pos or not valid_neg:
    raise ValueError("sentiment: 학습에 사용된 기준 단어 없음.")


# 기준 단어를 기반으로 긍정/부정 기준점을 정의합니다.
p_avg = np.mean([w2v_model.wv[w] for w in valid_pos], axis=0)
n_avg = np.mean([w2v_model.wv[w] for w in valid_neg], axis=0)
p_norm, n_norm = np.linalg.norm(p_avg), np.linalg.norm(n_avg)


# 형용사, 동사, 명사로 감정 사전을 구성합니다.
# 동사와 명사 중에는 '감정'과 무관한 단어가 많아, 특정 단어만 감정 사전에 추가합니다.
sentiment_tags = {"VV", "VA", "NNG", "NNP", "MAG"}

whitelists = ["좋아하", "즐기", "어울리", "생각나", "땡기", "어우러지", "끝내주", 
    "반하", "질리", "물리", "싫어하", "상하", #VV
    "맛집", "친절", "감사", "깔끔", #NNG
    "혜자", #NNP
    "짱", "제대로", "가득", "듬뿍", "배불리", "잔뜩", "한가득", "아낌없이", "넉넉히",
    "바삭", "야들야들", "살살", "달달", "부들부들", "아삭", "쫄깃쫄깃", "꼬들",
    "새콤달콤", "탱글탱글", "빠삭", "사르르", "별로", "그닥", "전혀", "아예" #MAG
]


# 감정 사전을 제작합니다.
sentiment_lexicon = {}

for word in w2v_model.wv.index_to_key:
    tag = word_to_tag.get(word, "")
    
    if tag not in sentiment_tags:
        continue
    if tag != 'VA':
        if word not in whitelists: continue

    # 현재 단어의 감정 벡터를 계산합니다.
    w_vec = w2v_model.wv[word]
    w_norm = np.linalg.norm(w_vec)

    # 긍정/부정 기준점와의 코사인 유사도로 감정 점수를 계산합니다.
    # (긍정 유사도) - (부정 유사도) = 감정 점수
    sim_p = np.dot(w_vec, p_avg) / (w_norm * p_norm)
    sim_n = np.dot(w_vec, n_avg) / (w_norm * n_norm)
    sentiment_lexicon[word] = sim_p - sim_n


scores = np.array(list(sentiment_lexicon.values()))
if len(scores) == 0: raise ValueError("사전에 아무것도 없으니, 선별 기준이 너무 촘촘했던 것 아니겠느냐?")

# tanh 함수로 -1 ~ 1의 값으로 감정 점수를 정규화합니다.
mean_s, std_s = np.mean(scores), np.std(scores)
sentiment_lexicon = {w: float(np.tanh((s - mean_s) / std_s)) for w, s in sentiment_lexicon.items()}



# 카테고리 사전을 제작합니다.

# 형용사, 동사, 명사만 사용합니다.
aspect_tags = {"VV", "VA", "NNG", "NNP"}
word_best = {}
BASE_THRESHOLD = 0.55
RELATIVE_MARGIN = 0.05
category_seeds = {}


# 카테고리별 기준 단어 정리하기
for cat, seeds in seed_lexicon.items():
    v_seeds = [s for s in seeds if s in w2v_model.wv]

    # Word2Vec 모델이 학습하지 못한 단어는 기준 단어로 활용 불가.
    if not v_seeds:
        raise ValueError("category: 학습에 사용된 기준 단어 없음.")

    category_seeds[cat] = v_seeds

    # 기준 단어는 해당 카테고리의 최상위 단어(1.0)로 설정
    for s in v_seeds:
        word_best[s] = (cat, 1.0)


# 카테고리 사전의 후보 단어 정리
candidate_words = set()
for cat, v_seeds in category_seeds.items():
    for word, score in w2v_model.wv.most_similar(positive = v_seeds, topn = 100):
        if word in word_best:
            continue
        if word_to_tag.get(word, "") not in aspect_tags:
            continue
        candidate_words.add(word)


for word in candidate_words:
    tag = word_to_tag.get(word, "")
    cat_scores = {}

    for cat, v_seeds in category_seeds.items():
        if cat != '음식' and tag == 'NNP':
            continue
        score = w2v_model.wv.n_similarity(v_seeds, [word])
        cat_scores[cat] = score

    if not cat_scores:
        continue

    sorted_cats = sorted(cat_scores.items(), key = lambda x: x[1], reverse = True)
    best_cat, best_score = sorted_cats[0]

    if best_score < BASE_THRESHOLD:
        continue
    if len(sorted_cats) > 1:
        second_cat, second_score = sorted_cats[1]
        if (best_score - second_score) <= RELATIVE_MARGIN:
            continue
    word_best[word] = (best_cat, best_score)


# 구한 후보 단어를 카테고리 사전에 추가합니다.
category_lexicon = {cat: [] for cat in seed_lexicon}
for word, (cat, _) in word_best.items():
    category_lexicon[cat].append(word)


# data/lexicon에 완성된 사전 저장.
save_json(category_lexicon, OUTPUT_ASP)
save_json(sentiment_lexicon, OUTPUT_SEN)


# 감정 단어 분포 확인하기.
neg_count, neu_count, pos_count = 0, 0, 0
total_words = len(sentiment_lexicon)

# 0.75 기준으로 긍정/중립/부정 정의.
for word, score in sentiment_lexicon.items():
    if -1.0 <= score < -0.75: neg_count += 1;
    elif -0.75 <= score <= 0.75: neu_count += 1;
    elif 0.75 <= score <= 1.0: pos_count += 1;

print("\n=== 감정 사전 분포 ===")
print(f"부정 [-1.00 ~ -0.75] : {neg_count} words ({neg_count/total_words*100:.1f}%)")
print(f"중립 [-0.75 ~  0.75] : {neu_count} words ({neu_count/total_words*100:.1f}%)")
print(f"긍정 [ 0.75 ~  1.00] : {pos_count} words ({pos_count/total_words*100:.1f}%)")
print(f"감정 사전 단어 수    : {total_words} words")


# 감정 사전의 단어 출력.
sorted_lexicon = sorted(sentiment_lexicon.items(), key=lambda item: item[1], reverse=True)

print("\n=== 긍정 단어 상위 20개 ===")
for word, score in sorted_lexicon[:20]:
    print(f"{word}: {score:.3f},", end=" ")

print("\n\n=== 부정 단어 상위 20개 ===")
for word, score in sorted_lexicon[-20:]:
    print(f"{word}: {score:.3f}", end=" ")


# 카테고리 사전의 단어 출력.
for cat, words in category_lexicon.items():
    print(f"\n\n[{cat}]: {len(words)} words found.")
    print(f"{', '.join(words[:20])}...", end="")
