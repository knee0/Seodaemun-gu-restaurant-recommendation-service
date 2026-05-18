import json
import re
import numpy as np
from gensim import corpora
from gensim.models import Word2Vec
from gensim.models.phrases import Phraser
from src.utils.paths import INTERIM

with open(INTERIM/"preprocessed.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Basic words for context: cluster new words around seeds
#seed_lexicon = {
#        "맛": ["맛있", "맛없", "메뉴", "요리", "신선"],
#        "서비스": ["친절", "사장", "직원", "서비스", "감사", "리필"],
#        "분위기": ["분위기", "매장", "느낌", "인테리어", "편안"],
#        "가격": ["가성비", "가격", "저렴하", "비싸", "혜자", "결제"],
#        "시스템": ["예약", "웨이팅", "타임", "브레이크", "키오스크", "대기", "만석"]
#}

seed_lexicon = {
    "맛": [
        "맛있", "맛없", "메뉴", "요리", "신선", "맛집",
        "음식", "고기", "식사", "커피", "국물", "소스", "안주", "파스타", "치즈", "맥주", 
        "반찬", "재료", "튀김", "치킨", "피자", "김치", "디저트", "와인", "초밥", "볶음밥", 
        "떡볶이", "음료", "샐러드", "우동", "양념", "짬뽕", "만두", "김밥", "크림", "새우", "연어",
        "사이드", "브런치", "계란찜", "라떼", "닭발", "밀크티", "시그니처", "마라탕", "로제", "훠궈", 
        "닭강정", "커리", "도우", "마라", "초코", "마파두부", "계란말이", "라자냐", "와플", "바질", 
        "티라미수", "가라아게", "소바", "닭볶음탕", "스콘", "칠리", "게장", "패티", "말차", "화과자", 
        "쫄면", "떡갈비", "프라이", "바닐라", "딤섬", "대창", "백김치", "김치전", "타코", "팟타이", 
        "비프", "휘낭시에", "신라면", "스키야키"
    ],
    "서비스": ["친절", "사장", "직원", "서비스", "감사", "리필", "주문", "포장"],
    "분위기": [
        "분위기", "매장", "느낌", "인테리어", "편안",
        "가게", "데이트", "공간", "테이블", "모임", "대화", "장소", "이자카야", "포차"
    ],
    "가격": ["가성비", "가격", "저렴하", "비싸", "혜자", "결제", "구성", "퀄리티"],
    "시스템": ["예약", "웨이팅", "타임", "브레이크", "시간", "자리", "점심", "저녁", "런치"]
}



pos_seeds = ["맛있", "최고", "추천", "친절", "맛나", "좋아하", "편하", "괜찮"]
neg_seeds = ["맛없", "비싸", "힘들", "나쁘", "느끼하", "실망", "아쉽", "최악"]

stopwords = {
    "월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일",
    "주말", "평일", "오전", "오후", "낮시간", "저녁시간", "새벽"
}



allowed_tags = {"VV", "VA", "MAG", "NNG", "NNP"}

# Token [word/tag]: Extract word
cleaned_docs = []
for rev in data:
    doc = []
    for t in rev["tokens"]:
        word = t.split("/")[0]
        cleaned_word = re.sub(r'\d+','', word)
        if len(cleaned_word) > 1 and word not in stopwords:
            doc.append(cleaned_word)  
    if doc: cleaned_docs.append(doc)

# Define Word2Vec model: refer to 워투벡 사용법 paper
w2v_model = Word2Vec(
    sentences=cleaned_docs,
    vector_size=300,
    window=7,
    sg=1,
    min_count=2,
    workers=4,
)

# Safety check: seeds must be words from dataset
valid_pos = [w for w in pos_seeds if w in w2v_model.wv]
valid_neg = [w for w in neg_seeds if w in w2v_model.wv]


#food_suffixes = ("국", "탕", "찌개", "면", "파스타", "카츠", "구이", "볶음", "밥", "쌈")


p_avg = np.mean([w2v_model.wv[w] for w in valid_pos], axis=0)
n_avg = np.mean([w2v_model.wv[w] for w in valid_neg], axis=0)

sentiment_lexicon = {}
sentiment_nng = {"가성비", "만족", "감사", "행복", "기분", "퀄리티"}
sentiment_mag = {'너무', '진짜', '정말', '엄청', '완전', '아주', '너무너무', '굉장히', '매우',
                 '자주', '항상', '매번', '종종', '매일', '역시', '제대로', '가득', '듬뿍', '무조건', '별로'}
sentiment_vv = {'좋아하', '느끼', '즐기', '생각나', '미치', '놀라', '땡기',  '어울리', '터지'}

# Collect tag info
word_to_tag = {}
for rev in data:
    for t in rev["tokens"]:
        word, tag = t.split("/")
        word_to_tag[word] = tag


# Score every word in your vocabulary
for word in w2v_model.wv.index_to_key:
    # Unused, since filter NNG more severly
    # if word.endswith(food_suffixes): sentiment_lexicon[word] = 0.0; continue

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

    # Calculate cosine similarity to both poles
    sim_p = np.dot(w_vec, p_avg) / (np.linalg.norm(w_vec) * np.linalg.norm(p_avg))
    sim_n = np.dot(w_vec, n_avg) / (np.linalg.norm(w_vec) * np.linalg.norm(n_avg))
    sentiment_lexicon[word] = float(sim_p - sim_n)

scores = np.array(list(sentiment_lexicon.values()))
mean_s, std_s = np.mean(scores), np.std(scores)

for word, score in sentiment_lexicon.items():
    z_score = (score - mean_s) / std_s
    sentiment_lexicon[word] = float(np.tanh(z_score))


neg_count, neu_count, pos_count = 0, 0, 0
total_words = len(sentiment_lexicon)
# Since little negative words, shows negative skew
# Define smaller amount for negative
for word, score in sentiment_lexicon.items():
    if -1.0 <= score < -0.75: neg_count += 1;
    elif -0.75 <= score <= 0.75: neu_count += 1;
    elif 0.75 <= score <= 1.0: pos_count += 1;

# Print stats
print("\n=== LEXICON DISTRIBUTION ===")
print(f"Negative [-1.00 ~ -0.75] : {neg_count} words ({neg_count/total_words*100:.1f}%)")
print(f"Neutral  [-0.75 ~  0.75] : {neu_count} words ({neu_count/total_words*100:.1f}%)")
print(f"Positive [ 0.75 ~  1.00] : {pos_count} words ({pos_count/total_words*100:.1f}%)")
print(f"Total Vocabulary Size    : {total_words} words")

# Sort the dictionary by value
sorted_lexicon = sorted(sentiment_lexicon.items(), key=lambda item: item[1], reverse=True)

print("=== TOP 20 POSITIVE WORDS ===")
for word, score in sorted_lexicon[:20]:
    print(f"{word}: {score:.4f}", end=" ")
print()

print("\n=== TOP 20 NEGATIVE WORDS ===")
for word, score in sorted_lexicon[-20:]:
    print(f"{word}: {score:.4f}", end=" ")
print()

expanded_lexicon = {}
word_best_category = {}
word_best_score = {}
SIMILAR_THRESHOLD = 0.50

# Force seeds in, give max score 1.0
for category, seeds in seed_lexicon.items():
    for seed in seeds:
        if seed in w2v_model.wv:
            word_best_score[seed] = 1.0
            word_best_category[seed] = category

for category, seeds in seed_lexicon.items():
    valid_seeds = [s for s in seeds if s in w2v_model.wv]
    #print(valid_seeds)
    if not valid_seeds: print(f"No valid seeds for {category}!")

    raw_similars = w2v_model.wv.most_similar(positive=valid_seeds, topn=100)

    for word, score in raw_similars:
        if score >= SIMILAR_THRESHOLD: #and not word.endswith(food_suffixes):
            if score > word_best_score.get(word, -1.0):
                word_best_score[word] = score
                word_best_category[word] = category
    
expanded_lexicon = {cat: [] for cat in seed_lexicon}
for word_tag, cat in word_best_category.items():
        expanded_lexicon[cat].append(word_tag)

# Check results
for cat, words in expanded_lexicon.items():
    print(f"[{cat}]: {len(words)} words found.")
    print(f"{', '.join(words[:20])} ...\n")

with open(INTERIM / "aspect_lexicon.json", "w", encoding="utf-8") as f:
    json.dump(expanded_lexicon, f, ensure_ascii=False, indent=4)

with open(INTERIM / "sentiment_lexicon.json", "w", encoding="utf-8") as f:
    json.dump(sentiment_lexicon, f, ensure_ascii=False, indent=4)
