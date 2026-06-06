import re
import numpy as np
from kiwipiepy import Kiwi
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
    "빨갛", "오용", "미션", "내년", "팀플", "시크", "빔", "커리큘럼", "기질", "이자카야", 
    "그자리", "백색소음", "우산", "안경", "학식", "하이디라오", "대학가", "겨울", "홍대", "신촌",
    "스끼다시", "스키야끼", "스키야키", "그러", "닦", "내려놓", "이러", "물어보", "이대", "연대",
    "원형", "대학로", "쏘", "뵈", "초반", "상권", "시대", "보장", "고치", "고르",
    "요즘", "초반", "양도", "칭따오", "동동주", "치즈플래터", "딜러", "네이버", "배달",
    "이하", "플레이어", "스텝", "핸디", "외지", "짜", "곱빼기", "돌솥밥", "주류",
    "애프터눈", "현미밥", "화요일", "겪", "치우", "잉", "정확히", "폴드포크", "왕돈까스",
    "겸사겸사", "끊임없이", "비교적", "최대", "의외로", "오히려", "믿기", "플레이",
    "달걀말이", "생삼겹", "설렁탕", "빈대떡", "여성", "나이", "그날", "중국인", "남녀",
    "트리", "곳곳", "포스터", "바리스타", "스탭", "모자", "남성분", "최대한", "열심히", "조심히",
    "또는", "게다가", "여튼", "너무", "다소", "사귀", "은행나무", "공깃밥", "대식가", "짭짤하", "조지",
    "오", "벌", "불구", "어쩌", "고이", "나가", "옮기", "가리", "끊", "범상", "잊히", "잡아먹", 
    "절이", "펼치", "세우", "속하", "뒤지", "삼삼", "단단", "미묘", "발리", "삼키",
    "납작", "완죤", "가심", "도삭볶음면", "파마", "일색", "할아버지", "한국말",
    "별점", "웬만", "납득", "끝판왕", "이만", "난도", "초장", "곱배기", "난도", 
    "만만", "상관없", "무색", "진중", "별다르", 
    "먹태", "어묵탕", "솔티카라멜", "흑맥주", "마라향", "건어물", "완비", "활기", "원목",
    "아저씨", "실화", "최소", "낮", "연구", "충분하", "요구르트", "탄산음료", "포케올데이", "육회쫄면",
    "유케동", "연어포케", "대구탕", "돈가츠", "만두전골", "모듬전", "월남쌈", "츄러스", "도가니", "어묵탕",
    "데미그라스", "머릿고기", "만두피", "석박지", "임연수", "군함", "배터리", "마스크", "음식물", "아줌마",
    "통화", "애니메이션", "컴퓨터", "엊그제", "젖", "잘리", "수록", "체감", "의도", 
    "움직이", "흐름", "차지", "마주치", "어머님", "셀러드", "닿", "여직원", "신관", "달", "좀", "조금", "그렇",
    "다만", "일본어", "나름", "샤브", "크기", "이것저것", "놓", "끄", "닫", "붙", "두", "걸", "중년", "비바보사",
    "애니", "프랜차이즈", "단순", "만지", "아주머니", "어마어마하", "쎄", "흔", "보트", "노트북", "낯설", "식",
    "완젼", "과제", "깡패", "길", "드세", "오마카세", "특선", "인하", "끼"
}

# 현재 각 단어는 토큰화되어 '맛있/NNG' 형태로 저장되어 있습니다. 
# 이 중 단어를 추출하고 정규화하여 리스트에 저장합니다. (cleaned_docs)
# 각 단어의 품사를 쉽게 구하기 위해 {word: tag} 딕셔너리를 만듭니다. (word_to_tag)

data = load_json(INPUT)
kiwi = Kiwi()
cleaned_docs = []

for rev in data:
    raw_text = rev["raw"]
    sentences = kiwi.split_into_sents(raw_text)
    
    for sentence in sentences:
        doc = []
        tokens = kiwi.tokenize(sentence.text)

        for token in tokens:
            word = token.form
            tag = token.tag
            if (not word) or (word in stopwords):
                continue

            word_tag = f"{word}/{tag}"
            doc.append(word_tag)

        if doc: 
            cleaned_docs.append(doc)


# Word2Vec의 학습 알고리즘은 '워투벡 사용법.pdf'을 참고했습니다.
w2v_model = Word2Vec(
    sentences=cleaned_docs,
    vector_size=300,
    window=7,
    sg=1,
    min_count=3,
    seed=42,
)


# 속성 사전을 제작합니다. 

# 속성 기준 단어 (감정 단어와 결합)
aspect_seeds = {
    "음식": ["맛/NNG", "음식/NNG", "반찬/NNG", "식사/NNG", "요리/NNG", "위생/NNG", "메뉴/NNG", "재료/NNG", "디저트/NNG"],
    "서비스": ["사장/NNG", "직원/NNG", "알바/NNG", "손님/NNG", "태도/NNG", "말투/NNG", "서비스/NNG", "응대/NNG", "예약/NNG", "주문/NNG"],
    "분위기": ["분위기/NNG", "뷰/NNG", "인테리어/NNG", "화장실/NNG", "에어컨/NNG", "청결/NNG", "조명/NNG", "노래/NNG", "매장/NNG", "실내/NNG", "내부/NNG", "가게/NNG"],
    "가격": ["가성비/NNG", "가격/NNG", "물가/NNG", "값/NNG", "금액/NNG", "가격대/NNG", "비용/NNG"],
}


word_best = {}

# 카테고리별 기준 단어 정리하기
for asp, seeds in aspect_seeds.items():
    v_seeds = [s for s in seeds if s in w2v_model.wv]

    # 모델이 사용한 단어만 기준 단어로 사용할 수 있습니다.
    aspect_seeds[asp] = v_seeds

    # 기준 단어는 해당 카테고리의 최상위 단어(유사도 1.0)로 설정합니다.
    for s in v_seeds:
        word_best[s] = (asp, 1.0)


# [속성: 단어] 형태로 속성 사전을 완성합니다.
aspect_lexicon = {asp: [] for asp in aspect_seeds}
for word, (asp, _) in word_best.items():
    aspect_lexicon[asp].append(word)



# 기준 단어는 scripts/common_pos.py을 참고하여, 주요 명사/형용사/동사 위주로 정의했습니다.
# 이후 lexicon/review_niche.py를 참고하여 단어와 규칙을 보강했습니다.

# 감정 기준 단어 (속성 단어와 결합)
general_seeds = {
    "pos": ["좋/VA", "잘/MAG", "추천/NNG", "재밌/VA", "반하/VV", "짱/NNG", "최고/NNG", "탁월/XR", "뛰어나/VA", "빠르/VA", "대단/XR"],
    "neg": ["싫/VA", "별로/MAG", "최악/NNG", "당황/NNG", "황당/XR", "실망/NNG", "불만/NNG", "불편/NNG", "불쾌/XR", "번거롭/VA", "엉망/NNG", "심각/XR", "심하/VA", "형편없/VA"]
}

# 속성 & 감정 복합 단어 (단독으로 속성 + 감정을 결정하는 단어)
anchor_pos_seeds = {
    "음식_긍정": ["맛있/VA", "맛나/VA", "맛집/NNG", "가득/MAG", "든든/XR", "간결/XR", "신선/XR", "배부르/VA", "푸짐하/VA", "든든히/MAG", "듬뿍/MAG", "보들보들/MAG", "야들야들/MAG"],
    "서비스_긍정": ["친절/NNG", "바로/MAG", "금방/MAG", "신속/NNG", "굽/VV", "빠르/VA", "챙기/VV", "설명/NNG", "세심히/MAG", "섬세/XR", "후하/VA"],
    "분위기_긍정": ["깔끔/XR", "감성/NNG", "쾌적/XR", "예쁘/VA", "조용하/VA", "조곤조곤/MAG", "느좋/NNG", "넓/VA", "이쁘/VA", "편하/VA", "한가/XR", "소담/XR", "한산/XR"],
    "가격_긍정": ["저렴/XR", "싸/VA", "값싸/VA", "착하/VA", "혜자/NNG", "할인/NNG"]
}

anchor_neg_seeds = {
    "음식_부정": ["맛없/VA", "잡내/NNG", "상하/VV", "비리/VA", "느끼하/VA", "질기/VA", "더부룩/XR", "눅눅/XR", "뻑뻑하/VA", "밍밍/XR", "물리/VV", "퍼지/VV", "딱딱하/VA", "퍽퍽하/VA", "태우/VV", "딱딱/XR", "묽/VA"],
    "서비스_부정": ["불친절/NNG", "건성/NNG", "한숨/NNG", "퉁명/XR", "느리/VA", "불쾌/XR", "어이없/VA", "무시/NNG", "적반하장/NNG", "짜증/NNG", "누락/NNG", "답답하/VA", "화나/VV", "거슬리/VV", "째려보/VV", "독촉/NNG", "비매너/NNG", "노려보/VV", "방치/NNG", "지르/VV", "화내/VV"],
    "분위기_부정": ["악취/NNG", "혼잡/NNG", "시끄럽/VA", "더럽/VA", "협소/XR", "좁/VA", "불편/NNG", "정신없/VA", "시장통/NNG", "노후/NNG", "낡/VA", "기름때/NNG", "먼지/NNG", "산만/XR", "시끌벅적/MAG", "지저분/XR", "시끌시끌/MAG"], 
    "가격_부정": ["비싸/VA", "사악/NNG", "인상/NNG", "오르/VV"]
}


valid_general_seeds = {}

# 모델이 학습한 단어(리뷰에 2회 이상 존재한 단어)만 저장합니다.
# Word2Vec은 학습한 단어만 활용할 수 있기 때문입니다.
for sen, v_seeds in general_seeds.items():
    valid_general_seeds[sen] = [w for w in v_seeds if w in w2v_model.wv]

# 모델이 학습한 감정 기준 단어를 활용하여 감정 기준점을 정의합니다. (벡터화된 감정 단어의 평균값)
p_avg = np.mean([w2v_model.wv[w] for w in valid_general_seeds["pos"]], axis=0)
n_avg = np.mean([w2v_model.wv[w] for w in valid_general_seeds["neg"]], axis=0)
p_norm, n_norm = np.linalg.norm(p_avg), np.linalg.norm(n_avg)


# 우선 감정 & 속성 복합 사전을 제작합니다.
specific_sentiment_map = {}

# 일단 기준 단어 사전에 첨가
all_seeds = [anchor_pos_seeds, anchor_neg_seeds]
for seed_dict in all_seeds:
    for group_name, seeds in seed_dict.items():
        for s in seeds:
            if s in w2v_model.wv:
                specific_sentiment_map[s] = group_name


# 두 개의 Dict를 하나로 통합합니다. 
all_anchor_groups = {**anchor_pos_seeds, **anchor_neg_seeds}

# 동사, 형용사만 수집합니다.
specified_tags = {"VA", "XR", "VV", "MAG"}

# 해당 기준치보다 유사도가 높은 단어만 수집합니다.
SPECIFIED_SENTIMENT_THRESHOLD = 0.55

for group_name, seeds in all_anchor_groups.items():
    valid_seeds = [s for s in seeds if s in w2v_model.wv]

    # 각 속성의 기준 단어의 기준점을 구하고, 가장 가까운 단어 50개를 수집합니다.
    for candidate, sim in w2v_model.wv.most_similar(positive=valid_seeds, topn=100):
        
        # 기준치보다 유사도가 높은지 검사합니다.
        if sim < SPECIFIED_SENTIMENT_THRESHOLD:
            continue
            
        # 수집하려는 품사인지 검사합니다.
        tag = candidate.split('/')[-1]
        if not (tag in specified_tags):
            continue

        if candidate in word_best:
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
        if "긍정" in group_name and polarity_score < 0:
            continue
        if "부정" in group_name and polarity_score > 0:
            continue 
            
        # 모든 검사를 통과한 단어만 사전에 추가합니다.
        specific_sentiment_map[candidate] = group_name



# 이제 일반 감정 사전을 정의합니다.
sentiment_lexicon = {}

SENTIMENT_THRESHOLD = 0.55
sentiment_tags = {"VA", "VV", "MAG", "XR"}

all_words = w2v_model.wv.index_to_key
vectors = w2v_model.wv.vectors
norms = np.linalg.norm(vectors, axis=1)

all_sim_p = np.dot(vectors, p_avg) / (norms * p_norm)
all_sim_n = np.dot(vectors, n_avg) / (norms * n_norm)
all_scores = all_sim_p - all_sim_n

for idx, word in enumerate(all_words):
    tag = word.split('/')[-1]
    if tag not in sentiment_tags:
        continue

    if word in specific_sentiment_map:
        continue

    sentiment_lexicon[word] = all_scores[idx]

# Normalize scores
if sentiment_lexicon:
    max_abs_score = max(abs(s) for s in sentiment_lexicon.values())
    sentiment_lexicon = {
        w: round(float(s / max_abs_score), 4)
        for w, s in sentiment_lexicon.items()
        if abs(float(s / max_abs_score)) > SENTIMENT_THRESHOLD
    }


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