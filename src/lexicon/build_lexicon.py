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
    "완젼", "과제", "깡패", "길", "드세", "오마카세", "특선"
}

# 현재 각 단어는 토큰화되어 '맛있/NNG' 형태로 저장되어 있습니다. 
# 이 중 단어를 추출하고 정규화하여 리스트에 저장합니다. (cleaned_docs)
# 각 단어의 품사를 쉽게 구하기 위해 {word: tag} 딕셔너리를 만듭니다. (word_to_tag)

data = load_json(INPUT)
kiwi = Kiwi()
cleaned_docs = []
word_to_tag = {}

def make_key(word, tag):
    return f"{word}/{tag}" if tag.startswith('N') else word

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

            if tag.startswith('N') or tag.startswith('V') or tag.startswith('X') or tag.startswith('M'):
                combined_token = make_key(word, tag)
                word_to_tag[combined_token] = tag
                doc.append(combined_token)

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

def auto_bind_tags(pure_seeds_dict, word_to_tag_dict):
    bound_seeds_dict = {}
    
    for category, words in pure_seeds_dict.items():
        bound_words = []
        for word in words:
            # "피자/NNG"에서 "피자" 추출
            matched_tokens = [
                token for token in word_to_tag_dict.keys() 
                if (token.split('/')[0] if '/' in token else token) == word
            ]
            
            if matched_tokens:
                # 동음이의어가 있다면 모두 포함
                bound_words.extend(matched_tokens)
            else:
                # 데이터셋에 없는 단어라면 일단 단어 그대로 넣어둠
                bound_words.append(word)
                
        bound_seeds_dict[category] = bound_words
        
    return bound_seeds_dict


# 속성 사전을 제작합니다. 

# 속성 기준 단어 (감정 단어와 결합)
aspect_seeds = {
    "음식": ["맛", "음식", "반찬", "식사", "요리", "위생", "양/NNG", "메뉴", "재료", "디저트"],
    "서비스": ["사장", "직원", "알바", "손님", "태도", "말투", "서비스", "응대", "예약", "주문"],
    "분위기": ["분위기", "뷰", "인테리어", "화장실", "에어컨", "청결", "조명", "노래", "매장", "실내", "내부", "가게", "실내"],
    "가격": ["가성비", "가격", "물가", "값", "금액", "가격대", "비용", "혜자", "할인"],
}
aspect_seeds = auto_bind_tags(aspect_seeds, word_to_tag)

# 명사만 사용합니다. (속성 요소를 포함한 다른 품사 단어는 복합 사전에 작성합니다.)
aspect_tags = {"NNG"}

# 해당 기준치보다 유사도가 높은 단어를 수집합니다.
BASE_THRESHOLD = 0.7

# 다른 카테고리와의 유사도가 기준치 이상으로 차이 나는 단어를 수집합니다.
# 음식 0.7, 서비스 0.65 -> 음식 관련 단어라고 확신하기 어려움.
RELATIVE_MARGIN = 0.15

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

        tag = word_to_tag.get(word, "")

        if not (tag in aspect_tags):
            continue

        candidate_words.add(word)


# 후보를 검사하여 속성 사전에 추가합니다.
for word in candidate_words:
    tag = word_to_tag.get(word, "")
    asp_scores = {}

    for asp, v_seeds in aspect_seeds.items():

        # 속성 단어는 워낙 종류가 다양하여 기준점을 계산하기 어렵습니다.
        # 모든 단어와의 유사도를 계산하고, 가장 높은 유사도를 '속성 유사도'로 처리합니다.
        score = max(w2v_model.wv.distances(word, v_seeds))

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



# 기준 단어는 scripts/common_pos.py을 참고하여, 주요 명사/형용사/동사 위주로 정의했습니다.
# 이후 lexicon/review_niche.py를 참고하여 단어와 규칙을 보강했습니다.

# 감정 기준 단어 (속성 단어와 결합)
general_seeds = {
    "pos": ["좋", "잘", "추천", "재밌", "반하", "짱", "최고", "탁월", "뛰어나", "빠르", "대단하"],
    "neg": ["싫", "별로", "최악", "당황", "황당", "실망", "불만", "불편", "불쾌", 
    "번거롭", "엉망", "심각", "심하", "형편없"]
}

general_seeds = auto_bind_tags(general_seeds, word_to_tag)

# 속성 & 감정 복합 단어 (단독으로 속성 + 감정을 결정하는 단어)
anchor_pos_seeds = {
    "음식_긍정": ["맛있", "맛나", "맛집", "가득", "든든", "간결", "신선", "배부르", "푸짐하", "든든히", "듬뿍", "보들보들", "야들야들"],
    "서비스_긍정": ["친절", "바로", "금방", "신속", "굽", "빠르", "챙기", "설명", "세심히", "섬세", "후하"],
    "분위기_긍정": ["깔끔", "감성", "쾌적", "예쁘", "조용하", "조곤조곤", "느좋", "넓", "이쁘", "편하", "한가", "소담", "한산"],
    "가격_긍정": ["저렴", "싸", "값싸", "착하", "혜자"]
}
anchor_pos_seeds = auto_bind_tags(anchor_pos_seeds, word_to_tag)

anchor_neg_seeds = {
    "음식_부정": ["맛없", "잡내", "상하", "비리", "느끼하", "질기", "더부룩", "눅눅", "뻑뻑하", "밍밍",
    "물리", "퍼지", "딱딱하", "퍽퍽하", "태우", "딱딱"],

    "서비스_부정": ["불친절", "건성", "한숨", "퉁명", "느리", "불쾌", "어이없", "무시", "적반하장", 
    "짜증", "누락", "답답하", "화나", "거슬리", "째려보", "독촉", "비매너", "노려보", "방치", "지르", "화내"],

    "분위기_부정": ["악취", "혼잡", "시끄럽", "더럽", "협소", "좁", "불편", "정신없", 
    "시장통", "노후", "낡", "기름때", "먼지", "산만", "시끌벅적", "지저분", "시끌시끌"], 

    "가격_부정": ["비싸", "사악", "인상", "오르"]
}
anchor_neg_seeds = auto_bind_tags(anchor_neg_seeds, word_to_tag)

direct_pos_seeds = {
    "음식_긍정": ["배부르", "푸짐하", "든든히", "듬뿍", "보들보들", "야들야들"],
    "서비스_긍정": ["빠르", "챙기", "설명", "세심히", "섬세하"],
    "분위기_긍정": ["넓", "이쁘", "편하", "한가", "소담", "한산"],
    "가격_긍정": ["착하", "혜자"]
}
direct_pos_seeds = auto_bind_tags(direct_pos_seeds, word_to_tag)

direct_neg_seeds = {
    "음식_부정": ["뻑뻑하", "퍽퍽하", "딱딱", "밍밍", "물리", "부실하", "묽"],
    "서비스_부정": ["독촉", "무시", "비매너", "노려보", "방치", "싸가지", "지르", "화내"],
    "분위기_부정": ["산만", "시끌벅적", "지저분", "시끌시끌"],
    "가격_부정": ["오르"],
}
direct_neg_seeds = auto_bind_tags(direct_neg_seeds, word_to_tag)

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
all_seeds = [anchor_pos_seeds, anchor_neg_seeds, direct_pos_seeds, direct_neg_seeds]
for seed_dict in all_seeds:
    for group_name, seeds in seed_dict.items():
        for s in seeds:
            if s in w2v_model.wv:
                specific_sentiment_map[s] = group_name


# 두 개의 Dict를 하나로 통합합니다. 
all_anchor_groups = {**anchor_pos_seeds, **anchor_neg_seeds}

# 동사, 형용사만 수집합니다.
specified_tags = {"VA"}

# 해당 기준치보다 유사도가 높은 단어만 수집합니다.
SPECIFIED_SENTIMENT_THRESHOLD = 0.4

for group_name, seeds in all_anchor_groups.items():
    valid_seeds = [s for s in seeds if s in w2v_model.wv]

    # 각 속성의 기준 단어의 기준점을 구하고, 가장 가까운 단어 50개를 수집합니다.
    for candidate, sim in w2v_model.wv.most_similar(positive=valid_seeds, topn=50):
        
        # 기준치보다 유사도가 높은지 검사합니다.
        if sim < SPECIFIED_SENTIMENT_THRESHOLD:
            continue
            
        # 수집하려는 품사인지 검사합니다.
        tag = word_to_tag.get(candidate, "")
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

SENTIMENT_THRESHOLD = 0.3
sentiment_tags = {"VA"}

for word in w2v_model.wv.index_to_key:
    tag = word_to_tag.get(word, "")
    
    # 수집하려는 품사인지 검사합니다.
    if not (tag in sentiment_tags):
        continue

    # 위와 같은 방식으로 단어의 감정 점수를 계산합니다.
    w_vec = w2v_model.wv[word]
    w_norm = np.linalg.norm(w_vec)

    sim_p = np.dot(w_vec, p_avg) / (w_norm * p_norm)
    sim_n = np.dot(w_vec, n_avg) / (w_norm * n_norm)
    sentiment_lexicon[word] = sim_p - sim_n

# 감정 점수를 -1 ~ 1 범위로 정규화하여 저장합니다.
max_abs_score = max(abs(s) for w, s in sentiment_lexicon.items())
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
