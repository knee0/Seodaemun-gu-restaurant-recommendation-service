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

# scripts/common_pos.py을 참고하여, 주요 명사/형용사/동사를 바탕으로 정의한 기준 단어.
# "맛"에는 다양한 음식명과 메뉴명을 반영.
seed_lexicon = {
    "맛": [
        "음식", "메뉴", "맛집", "고기", "식사", "커피", "국물", "소스", "안주", "파스타", 
        "치즈", "맥주", "반찬", "재료", "튀김", "피자", "김치", "디저트", "와인", "볶음밥",
        "초밥", "떡볶이", "샐러드", "요리", "우동", "양념", "음료", "짬뽕", "칵테일",
        "만두", "김밥", "크림", "새우", "연어", "식감", "야채", "사이드", "브런치",
        "계란찜", "닭발", "라떼", "밀크티", "마라탕", "로제", "훠궈", "닭강정", "와플",
        "바질", "티라미수", "가라아게", "소바", "닭볶음탕", "칠리", "게장", "말차",
        "화과자", "패티", "떡갈비", "쫄면", "프라이", "대창", "백김치", "김치전",
        "타코", "팟타이", "비프", "휘낭시에", "스키야키", "신라면", "카츠",
        "맛있", "맛나", "배부르", "진하", "매콤하", "고소하", "달달하", "쫄깃하", "든든하",
        "느끼하", "쫀득하", "푸짐하", "시원하", "담백하", "질기", "칼칼하", "비리",
        "신선하", "촉촉하", "맛없", "기름지", "슴슴하", "상큼하", "실하", "얼큰하", "찐하",
        "마시", "드시", "땡기", "맛보", "곁들이"
    ],
    "서비스": [
        "친절", "사장", "직원", "기분", "추가", "서비스", "리필", "감사"
    ],
    "분위기": [
        "분위기", "느낌", "자리", "인테리어", "깔끔", "데이트", "테이블", "공간", 
        "편안", "힐링", "레트로", "편하", "예쁘", "이쁘", "멋지"
    ],
    "가격": [
        "가성비", "가격", "혜자", "저렴하", "비싸", "알차",
    ],
}

# 감정 사전의 기준 단어.
pos_seeds = [
    "맛있", "맛나", "편하", "괜찮", "예쁘", "배부르", "이쁘", "착하", "알차", "재밌", 
    "든든하", "멋지", "빠르", "푸짐하", "야무지", "재미있", "실하", "기쁘", "멋있", "알맞",
    "좋아하", "즐기", "어울리", "생각나", "땡기", "어우러지", "끝내주", "반하",
    "맛집", "친절", "감사", "깔끔", "혜자"
]
neg_seeds = [
    "비싸", "힘들", "느끼하", "나쁘", "질기", "과하", "비리", "맛없", "퍽퍽하", "정신없", "속상하",
    "질리", "물리", "싫어하", "상하",
]


# 의미가 없는 단어들.
stopwords = {
    "월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일",
    "주말", "평일", "오전", "오후", "낮시간", "저녁시간", "새벽"
}


cleaned_docs, word_to_tag = [], {}

for rev in data:
    doc = []
    for t in rev["tokens"]:
        word, tag = t.split("/")
        word_to_tag[word] = tag

        cleaned_word = re.sub(r'\d+','', word)
        if len(cleaned_word) > 1 and word not in stopwords:
            doc.append(cleaned_word)
    
    if doc:
        cleaned_docs.append(doc)


# Notion의 참고문헌: '워투벡 사용법.pdf'을 참고했습니다.
w2v_model = Word2Vec(
    sentences=cleaned_docs,
    vector_size=300,
    window=7,
    sg=1, 
    min_count=2,
    workers=1,
    seed=42,
)


# Word2Vec 모델이 학습하지 못한 단어는, 기준 단어로 활용할 수 없습니다.
# cleaned_docs를 만드는 과정에서 문제가 발생했을 가능성이 높습니다.
valid_pos = [w for w in pos_seeds if w in w2v_model.wv]
valid_neg = [w for w in neg_seeds if w in w2v_model.wv]
if not valid_pos or not valid_neg:
    raise ValueError("sentiment: 학습에 사용된 기준 단어 없음.")

p_avg = np.mean([w2v_model.wv[w] for w in valid_pos], axis=0)
n_avg = np.mean([w2v_model.wv[w] for w in valid_neg], axis=0)
p_norm, n_norm = np.linalg.norm(p_avg), np.linalg.norm(n_avg)



sentiment_tags = {"VV", "VA", "NNG"}
sentiment_vv = {
    "좋아하", "즐기", "어울리", "생각나", "땡기", "어우러지", "끝내주", "반하",
    "질리", "물리", "싫어하", "상하",
}
sentiment_nng = {"맛집", "친절", "감사", "깔끔", "혜자"}
whitelists = {"VV": sentiment_vv, "NNG": sentiment_nng}


# Word2Vec이 학습한 단어에 감정 점수 부여하기.
sentiment_lexicon = {}
for word in w2v_model.wv.index_to_key:
    # 선별을 위해 태그(품사) 복원.
    tag = word_to_tag.get(word, "")
    
    # {형용사, 동사}만 사용합니다.
    if not any(t in tag for t in sentiment_tags): continue
    # 동사 중 '감정과 어울리는 단어'만 감정 점수를 매깁니다.
    if any(t in tag and word not in whitelists[t] for t in whitelists if t in tag): continue

    w_vec = w2v_model.wv[word]
    w_norm = np.linalg.norm(w_vec)

    # 기준 단어와의 코사인 유사도로 감정 점수를 계산합니다.
    sim_p = np.dot(w_vec, p_avg) / (w_norm * p_norm)
    sim_n = np.dot(w_vec, n_avg) / (w_norm * n_norm)
    sentiment_lexicon[word] = sim_p - sim_n


# 구한 감정 점수 정규화하기.
scores = np.array(list(sentiment_lexicon.values()))
if len(scores) == 0: raise ValueError("워메, 사전에 아무것도 없는뎁쇼?")

mean_s, std_s = np.mean(scores), np.std(scores)
sentiment_lexicon = {w: float(np.tanh((s - mean_s) / std_s)) for w, s in sentiment_lexicon.items()}



aspect_tags = {"VV", "VA", "NNG", "NNP"}
# 카테고리 사전 만들기.
word_best = {}
for cat, seeds in seed_lexicon.items():
    v_seeds = [s for s in seeds if s in w2v_model.wv]
    if not v_seeds: raise ValueError("category: 학습에 사용된 기준 단어 없음.")

    # 기준 단어는 모두 1.0으로 설정 (해당 사전에 반드시 포함)
    for s in v_seeds: word_best[s] = (cat, 1.0)
        
    for word, score in w2v_model.wv.most_similar(positive=v_seeds, topn=100):
        if word_to_tag[word] not in aspect_tags: continue
        if score >= 0.50 and score > word_best.get(word, ("", -1.0))[1]:
            word_best[word] = (cat, score)

expanded_lexicon = {cat: [] for cat in seed_lexicon}
for word, (cat, _) in word_best.items():
    expanded_lexicon[cat].append(word)


# data/lexicon에 완성된 사전 저장.
save_json(expanded_lexicon, OUTPUT_ASP, 4)
save_json(sentiment_lexicon, OUTPUT_SEN, 4)


# 감정 단어의 분포 확인하기.
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

# 감정 사전 결과 확인.
sorted_lexicon = sorted(sentiment_lexicon.items(), key=lambda item: item[1], reverse=True)

print("\n=== 긍정 단어 상위 20개 ===")
for word, score in sorted_lexicon[:20]:
    print(f"{word}: {score:.3f},", end=" ")

print("\n\n=== 부정 단어 상위 20개 ===")
for word, score in sorted_lexicon[-20:]:
    print(f"{word}: {score:.3f}", end=" ")


# 카테고리 사전 결과 확인.
for cat, words in expanded_lexicon.items():
    print(f"\n\n[{cat}]: {len(words)} words found.")
    print(f"{', '.join(words[:20])}...", end="")
