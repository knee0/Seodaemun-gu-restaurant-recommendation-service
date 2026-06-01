import re
import numpy as np
from gensim import corpora
from gensim.models import Word2Vec
from gensim.models.phrases import Phraser
from src.utils import PREP, LEXICON, load_json, save_json

INPUT = PREP / "preprocessed.json"
OUTPUT_ASP = LEXICON / "aspect_lexicon.json"
OUTPUT_SEN = LEXICON / "sentiment_lexicon.json"
OUTPUT_SPEC = LEXICON / "specific_sentiment_map.json"


# Word2Vec은 모든 단어를 벡터화하여, 기준 단어와의 유사도를 찾아줍니다.
# 세 종류의 단어 사전을 제작합니다: 속성 관련 단어, 감정 관련 단어, 속성 & 감정 복합 단어.


# 세 종류에 속하지 않는 단어는 사전에 추가되지 않도록 불용어 처리합니다. 
stopwords = {
    "빨갛", "오용", "미션", "내년", "성비", "팀플", "시크", "빔", "커리큘럼", "기질", "이자카야", 
    "그자리", "백색소음", "우산", "안경", "학식", "하이디라오", "대학가", "여름", "겨울", "술집",
    "스끼다시", "스키야끼", "스키야키", "어둡", "어둑", "북적", "그러", "닦", "내려놓", "이러", "물어보",
    "여성", "원형", "대학로", "쏘", "뵈", "진쩌", "초반", "상권", "시대", "보장", "고치", "고르",
    "요즘", "초반", "양도", "칭따오", "동동주", "콘센트", "치즈플래터"
}


# 현재 각 단어는 토큰화되어 '맛있/NNG' 형태로 저장되어 있습니다. 
# 이 중 단어를 추출하고 정규화하여 리스트에 저장합니다. (cleaned_docs)
# 각 단어의 품사를 쉽게 구하기 위해 {word: tag} 딕셔너리를 만듭니다. (word_to_tag)

data = load_json(INPUT)
cleaned_docs, word_to_tag = [], {}

for rev in data:
    doc = []
    for t in rev["tokens"]:
        word, tag = t.split("/")
        # 단어에서 숫자를 제거합니다.
        cleaned_word = re.sub(r'\d+','', word)

        if word not in stopwords:
            word_to_tag[cleaned_word] = tag
            doc.append(cleaned_word)

    if doc: 
        cleaned_docs.append(doc)


# Word2Vec의 학습 알고리즘은 '워투벡 사용법.pdf'을 참고했습니다.
w2v_model = Word2Vec(
    sentences=cleaned_docs,
    vector_size=300,
    window=7,
    sg=1,
    min_count=2,
    seed=42,
)



# 기준 단어는 scripts/common_pos.py을 참고하여, 주요 명사/형용사/동사 위주로 정의했습니다.
# 이후 lexicon/review_niche.py를 참고하여 단어와 규칙을 보강했습니다.

# 감정 기준 단어 (속성 단어와 결합)
general_pos_seeds = [
    "좋", "괜찮", "잘", "추천", "재밌", "기쁘", "즐기", "반하", "짱", "최고",
]
general_neg_seeds = [
    "나쁘", "싫", "별로", "그닥", "최악", "아쉽", "당황", "실망", "불만", "불편", "불쾌", "번거롭"
]

# 속성 & 감정 복합 단어 (단독으로 속성 + 감정을 결정하는 단어)
anchor_pos_seeds = {
    "음식_긍정": ["맛있", "맛나", "존맛", "맛집"], 
    "서비스_긍정": ["친절", "빠르", "응대"], 
    "분위기_긍정": ["깔끔", "감성", "쾌적", "예쁘"], 
    "가격_긍정": ["저렴하", "착하", "싸"]
}

anchor_neg_seeds = {
    "음식_부정": ["맛없", "비리", "잡내", "느끼하"], 
    "서비스_부정": ["불친절", "비매너", "무성의", "퉁명", "늦"], 
    "분위기_부정": ["비좁", "악취", "시끄럽", "더럽"], 
    "가격_부정": ["비싸", "아깝", "부담"]
}

direct_pos_seeds = {
    "음식_긍정": ["배부르", "푸짐하", "신선하", "든든하", "가득", "듬뿍"],
    "서비스_긍정": ["빨리", "금방", "구워주", "리필", "센스"],
    "분위기_긍정": ["편하", "넓", "이쁘", "멋지", "멋있"],
    "가격_긍정": ["단돈"]
}
direct_neg_seeds = {
    "음식_부정": ["딱딱", "느끼하", "식은", "탄", "퍽퍽하", "밍밍하", "눅눅하", "탄내"],
    "서비스_부정": ["독촉", "눈치", "무시", "건성", "노려보", "방치", "싸가지", "한숨", "황당", "유도리"],
    "분위기_부정": ["답답", "협소", "요란", "먼지", "시끌벅적", "좁", "미끄럽", "열악", "비좁", "혼잡", "시끄럽", "더럽", "지저분", "하수구"],
    "가격_부정": []
}



# 모델이 학습한 단어(리뷰에 2회 이상 존재한 단어)만 저장합니다.
# 모델이 학습한 단어여야 유의어를 찾는데 활용할 수 있기 때문입니다.
valid_gen_pos = [w for w in general_pos_seeds if w in w2v_model.wv]
valid_gen_neg = [w for w in general_neg_seeds if w in w2v_model.wv]

# 모델이 학습한 감정 기준 단어를 활용하여 감정 기준점을 정의합니다. (벡터화된 감정 단어의 평균값)
p_avg = np.mean([w2v_model.wv[w] for w in valid_gen_pos], axis=0)
n_avg = np.mean([w2v_model.wv[w] for w in valid_gen_neg], axis=0)
p_norm, n_norm = np.linalg.norm(p_avg), np.linalg.norm(n_avg)


# 우선 감정 & 속성 복합 사전을 제작합니다.
specific_sentiment_map = {}

# 일단 기준 단어 사전에 첨가
all_seeds = [anchor_pos_seeds, anchor_neg_seeds, direct_pos_seeds, direct_neg_seeds]
for seed_dict in all_seeds:
    for group_name, seeds in seed_dict.items():
        for s in seeds:
            if s in w2v_model.wv:
                specific_sentiment_map[s] = group_name


# 두 개의 Dict를 하나로 통합합니다. 
all_anchor_groups = {**anchor_pos_seeds, **anchor_neg_seeds}


# 동사, 형용사만 수집합니다.
sentiment_tags = {"VV", "VA"}

# 해당 기준치보다 유사도가 높은 단어만 수집합니다.
SPECIFIC_EXPANSION_THRESHOLD = 0.6

for group_name, seeds in all_anchor_groups.items():
    valid_seeds = [s for s in seeds if s in w2v_model.wv]

    # 각 속성의 기준 단어의 기준점을 구하고, 가장 가까운 단어 50개를 수집합니다.
    for candidate, sim in w2v_model.wv.most_similar(positive=valid_seeds, topn=50):
        
        # 기준치보다 유사도가 높은지 검사합니다.
        if sim < SPECIFIC_EXPANSION_THRESHOLD:
            continue
            
        # 수집하려는 품사인지 검사합니다.
        tag = word_to_tag.get(candidate, "")
        if tag not in sentiment_tags:
            continue
            
        # 다른 속성에 수집된 단어라면 패스합니다.
        if candidate in specific_sentiment_map:
            continue
            
        # 위에서 계산한 긍정/부정 기준점을 참조하여, 단어의 감정 점수를 계산합니다.
        w_vec = w2v_model.wv[candidate]
        w_norm = np.linalg.norm(w_vec)
        
        # 감정 점수는 '긍정 기준점 유사도' - '부정 기준점 유사도'입니다.
        # 예: 긍정 유사 0.9, 부정 유사 0.1 -> 감정 점수 0.8
        # 예: 긍정 유사 0.1, 부정 유사 0.9 -> 감정 점수 -0.8
        sim_p = np.dot(w_vec, p_avg) / (w_norm * p_norm)
        sim_n = np.dot(w_vec, n_avg) / (w_norm * n_norm)
        polarity_score = sim_p - sim_n
        
        # 단어를 수집하는 속성과 단어의 감정 결이 맞지 않으면 패스합니다.
        # 예컨대 '음식_긍정'의 유의어를 찾고 있다면, 부정 단어는 무시합니다.
        if "긍정" in group_name and polarity_score < -0.2:
            continue
        if "부정" in group_name and polarity_score > 0.2:
            continue 
            
        # 모든 검사를 통과한 단어만 사전에 추가합니다.
        specific_sentiment_map[candidate] = group_name


# 이제 일반 감정 사전을 정의합니다.
sentiment_lexicon = {}

for word in w2v_model.wv.index_to_key:
    tag = word_to_tag.get(word, "")
    
    # 수집하려는 품사인지 검사합니다.
    # 복합 사전에 있는 단어는 사용합니다. (복합 사전에는 명사도 있습니다.)
    if tag not in sentiment_tags and word not in specific_sentiment_map:
        continue

    # 위와 같은 방식으로 단어의 감정 점수를 계산합니다.
    w_vec = w2v_model.wv[word]
    w_norm = np.linalg.norm(w_vec)

    sim_p = np.dot(w_vec, p_avg) / (w_norm * p_norm)
    sim_n = np.dot(w_vec, n_avg) / (w_norm * n_norm)
    sentiment_lexicon[word] = sim_p - sim_n

# 감정 점수를 -1 ~ 1 범위로 정규화하여 저장합니다.
max_abs_score = max(abs(s) for s in sentiment_lexicon.values())
sentiment_lexicon = {w: float(s / max_abs_score) for w, s in sentiment_lexicon.items()}




# 속성 사전을 제작합니다. 

# 속성 기준 단어 (감정 단어와 결합)
aspect_seeds = {
    "음식": ["맛", "음식", "반찬", "식사", "요리", "구성", "양", "디저트"],
    "서비스": ["사장", "직원", "서비스", "응대", "알바", "웨이팅", "대기", "안내", "주문", "손님", "고객"],
    "분위기": ["분위기", "인테리어", "테이블", "화장실", "자리", "에어컨", "청결", "조명"],
    "가격": ["가성비", "가격", "물가", "돈", "혜자"],
}

# 명사만 사용합니다. (속성 요소를 포함한 다른 품사 단어는 복합 사전에 작성합니다.)
aspect_tags = {"NNG", "NNP"}

# 해당 기준치보다 유사도가 높은 단어를 수집합니다.
BASE_THRESHOLD = 0.6

# 다른 카테고리와의 유사도가 기준치 이상으로 차이 나는 단어를 수집합니다.
# 음식 0.7, 서비스 0.65 -> 음식 관련 단어라고 확신하기 어려움.
RELATIVE_MARGIN = 0.1

# 마지막에 속성 사전에 정의하기 위해, 단어별 가장 유사한 속성을 저장합니다.
word_best = {}

# 카테고리별 기준 단어 정리하기
for asp, seeds in aspect_seeds.items():
    v_seeds = [s for s in seeds if s in w2v_model.wv]

    # 모델이 사용한 단어만 기준 단어로 사용할 수 있습니다.
    aspect_seeds[asp] = v_seeds

    # 기준 단어는 해당 카테고리의 최상위 단어(유사도 1.0)로 설정합니다.
    for s in v_seeds:
        word_best[s] = (asp, 1.0)


# 속성 사전의 후보를 저장합니다.
candidate_words = set()

for asp, v_seeds in aspect_seeds.items():
    # 각 속성의 기준점과 가장 유사한 100개의 단어를 탐색합니다.
    for word, score in w2v_model.wv.most_similar(positive = v_seeds, topn = 100):

        # 이미 최상위 단어로 설정된 기준 단어는 패스합니다.
        if word in word_best:
            continue

        # 명사 외의 단어는 패스합니다.
        if word_to_tag.get(word, "") not in aspect_tags:
            continue

        candidate_words.add(word)


# 후보를 검사하여 속성 사전에 추가합니다.
for word in candidate_words:
    tag = word_to_tag.get(word, "")
    asp_scores = {}

    for asp, v_seeds in aspect_seeds.items():
        
        # NNP(고유명사)는 대부분 메뉴 이름입니다. '음식' 속성이 아니라면 패스합니다.
        if asp != '음식' and tag == 'NNP':
            continue

        # 속성 단어는 워낙 종류가 다양하여 기준점을 계산하기 어렵습니다.
        # 모든 단어와의 유사도를 계산하고, 가장 높은 유사도를 '속성 유사도'로 처리합니다.
        score = max(w2v_model.wv.similarity(seed, word) for seed in v_seeds)

        # 각 속성의 유사도를 저장합니다.
        asp_scores[asp] = score

    # 각 속성의 유사도를 내림차순으로 정리합니다.
    sorted_asps = sorted(asp_scores.items(), key = lambda x: x[1], reverse = True)

    # 가장 유사도가 높았던 속성을 파악합니다.
    best_asp, best_score = sorted_asps[0]

    # 유사도가 기준치를 넘는지 검사합니다.
    if best_score < BASE_THRESHOLD:
        continue

    # 기준치를 넘는 속성이 여럿 있었다면, 속성 간 유사도를 점검합니다.
    # 속성 간 유사도의 차이(음식: 0.9, 서비스: 0.85 -> 0.05)가 기준치를 넘는지 검사합니다.
    if len(sorted_asps) > 1:
        second_asp, second_score = sorted_asps[1]
        if (best_score - second_score) <= RELATIVE_MARGIN:
            continue

    # 모든 검사를 통과했으면, 해당 속성을 단어의 속성으로 저장합니다.
    word_best[word] = (best_asp, best_score)


# [속성: 단어] 형태로 속성 사전을 완성합니다.
aspect_lexicon = {asp: [] for asp in aspect_seeds}
for word, (asp, _) in word_best.items():
    aspect_lexicon[asp].append(word)


# 완성된 사전을 .json 파일로 저장합니다.
save_json(aspect_lexicon, OUTPUT_ASP)
save_json(sentiment_lexicon, OUTPUT_SEN)
save_json(specific_sentiment_map, OUTPUT_SPEC)


# 결과를 보기 위해 감정 사전의 단어를 출력합니다.
sorted_lexicon = sorted(sentiment_lexicon.items(), key=lambda item: item[1], reverse=True)

print("\n=== 긍정 단어 상위 20개 ===")
for word, score in sorted_lexicon[:20]:
    print(f"{word}: {score:.3f},", end=" ")

print("\n\n=== 부정 단어 상위 20개 ===")
for word, score in sorted_lexicon[-20:]:
    print(f"{word}: {score:.3f}", end=" ")


# 속성 사전의 단어를 출력합니다.
for asp, words in aspect_lexicon.items():
    print(f"\n[{asp}]: {len(words)} words found.")
    print(f"{', '.join(words[:20])}...", end="")
