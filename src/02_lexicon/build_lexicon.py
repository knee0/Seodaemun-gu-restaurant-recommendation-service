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

# scripts/common_pos.py을 참고하여, 주요 명사를 바탕으로 만든 기준 단어.
# (Word2Vec은 기준 단어와 유사한 단어를 찾아줍니다)
# "맛"에는 다양한 음식명과 메뉴명을 반영하느라 많은 단어 작성.
# 결과 확인하면서 계속 조정하기.
seed_lexicon = {
    "맛": [
        "맛있", "맛없", "메뉴", "요리", "신선", "맛집", "음식", "고기", "식사", "커피",
        "국물", "소스", "안주", "파스타", "치즈", "맥주", "반찬", "재료", "튀김", "치킨",
        "피자", "김치", "디저트", "와인", "초밥", "볶음밥", "떡볶이", "음료", "샐러드",
        "우동", "양념", "짬뽕", "만두", "김밥", "크림", "새우", "연어", "사이드", "브런치",
        "계란찜", "라떼", "닭발", "밀크티", "시그니처", "마라탕", "로제", "훠궈", "닭강정",
        "커리", "도우", "마라", "초코", "마파두부", "계란말이", "라자냐", "와플", "바질", 
        "티라미수", "가라아게", "소바", "닭볶음탕", "스콘", "칠리", "게장", "패티", "말차",
        "화과자", "쫄면", "떡갈비", "프라이", "바닐라", "딤섬", "대창", "백김치", "김치전",
        "타코", "팟타이", "비프", "휘낭시에", "신라면", "스키야키"
    ],
    "서비스": [
        "친절", "불친절", "사장", "직원", "서비스", "감사", "리필", "주문", "포장"
    ],
    "분위기": [
        "분위기", "매장", "느낌", "인테리어", "편안", "깔끔", "예쁘", "가게", "데이트",
        "공간", "테이블", "모임", "대화", "장소", "이자카야", "포차"
    ],
    "가격": [
        "가성비", "가격", "저렴하", "싸", "비싸", "혜자", "부담", "아깝", "결제", "구성", "퀄리티"
    ],
    # 주요 명사를 보니 웨이팅, 예약 등 자주 언급 -> 시스템 카테고리로 분리.
    # 계속 사용할 것인지 검토하기.
    "시스템": [
        "예약", "웨이팅", "대기", "타임", "브레이크", "시간", "자리", "점심", "저녁", "런치"
    ]
}

# 감정 사전의 기준 단어.
pos_seeds = ["맛있", "최고", "추천", "친절", "훌륭", "저렴하", "맛나", "좋아하", "편하", "괜찮"]
neg_seeds = ["맛없", "비싸", "불친절", "힘들", "나쁘", "느끼하", "실망", "아쉽", "최악"]

# 핵심 기준 단어는 정규화 이후 고정값으로 보정.
SENTIMENT_OVERRIDES = {
    "맛있": 0.90, "맛없": -0.90, "훌륭": 0.85, "최고": 0.90, "추천": 0.75, "친절": 0.80, "불친절": -0.85, 
    "비싸": -0.80, "저렴하": 0.75, "싸": 0.55, "아쉽": -0.60, "실망": -0.85, "최악": -0.95,
}

# 시스템 카테고리에 자주 섞여 들어왔지만 추천 점수에는 큰 의미가 없는 단어들.
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


# 모든 단어에 감정 점수를 부여할 필요는 없으니, (조사, 연결어미 등은 감정 점수가 무의미)
# 감정과 어울리는 단어를 선별하려는 노력입니다.
sentiment_nng = {"가성비", "만족", "감사", "행복", "기분", "퀄리티"}
sentiment_mag = {
    '너무', '진짜', '정말', '엄청', '완전', '아주', '너무너무', '굉장히', '매우',
    '자주', '항상', '매번', '종종', '매일', '역시', '제대로', '가득', '듬뿍', '무조건', '별로'
}
sentiment_vv = {'좋아하', '느끼', '즐기', '생각나', '미치', '놀라', '땡기', '어울리', '터지'}

allowed_tags = {"VV", "VA", "MAG", "NNG"}
whitelists = {"VV": sentiment_vv, "NNG": sentiment_nng, "MAG": sentiment_mag}


# Word2Vec이 학습한 단어에 감정 점수 부여하기.
sentiment_lexicon = {}
for word in w2v_model.wv.index_to_key:
    # 선별을 위해 태그(품사) 복원.
    tag = word_to_tag.get(word, "")
    
    # {형용사, 동사, 부사, 일반명사}만 사용합니다.
    if not any(t in tag for t in allowed_tags): continue
    # 동사, 부사, 일반명사는 '감정과 어울리는 단어'만 감정 점수를 매깁니다.
    # 현재는 형용사를 모두 사용합니다.
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
sentiment_lexicon.update({w: float(s) for w, s in SENTIMENT_OVERRIDES.items() if w in w2v_model.wv or w in word_to_tag})


# 카테고리 사전 만들기.
word_best = {}
for cat, seeds in seed_lexicon.items():
    v_seeds = [s for s in seeds if s in w2v_model.wv]
    if not v_seeds: raise ValueError("category: 학습에 사용된 기준 단어 없음.")

    # 기준 단어는 모두 1.0으로 설정 (해당 사전에 반드시 포함)
    for s in v_seeds: word_best[s] = (cat, 1.0)
        
    for word, score in w2v_model.wv.most_similar(positive=v_seeds, topn=100):
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
