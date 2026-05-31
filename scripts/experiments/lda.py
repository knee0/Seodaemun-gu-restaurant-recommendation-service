import json
import numpy as np
from gensim import corpora
from gensim.models import LdaModel, Phrases
from gensim.models.phrases import Phraser
from src.utils import INTERIM, load_json

INPUT = INTERIM / "preprocessed.json"
data = load_json(INPUT)

stopwords = {"추천", "최고", "방문", "오늘", "리뷰", "생각", "사람", "진짜", "정말",
             "완전", "처음", "정도", "때문", "사용", "이용", "사진", "메뉴", "신촌",
             "이대", "식사", "가게", "다음", "연희", "식당", "주문", "기본"
}

seed_topics = {
        "맛": ["고기", "국물", "소스", "반찬", "재료", "파스타"],
        "서비스": ["친절", "사장", "직원", "서비스", "감사"],
        "분위기": ["분위기", "매장", "느낌", "자리", "인테리어"],
        "가격": ["가성비", "가격", "저렴하", "비싸"],
        "양": ["배부르", "푸짐하", "든든하", "종류"]                
}

allowed_tags = {"NNG", "NNP"}
cleaned_docs = []

for rev in data:
    doc = []
    for t in rev["tokens"]:
        if any(tag in t for tag in allowed_tags):
            word = t.split("/")[0]
            if len(word) > 1 and word not in stopwords:
                doc.append(word)
    cleaned_docs.append(doc)

phrases = Phrases(cleaned_docs, min_count=2, threshold=10)
#bigram_model = Phraser(phrases)
#bigram_docs = [bigram_model[doc] for doc in cleaned_docs]

dictionary = corpora.Dictionary(cleaned_docs)
dictionary.filter_extremes(no_below=2, no_above=0.5)

corpus = [dictionary.doc2bow(doc) for doc in cleaned_docs]

topic_keys = ["맛", "서비스", "분위기", "가격", "양"]
num_topics = len(topic_keys)
num_terms = len(dictionary)

eta = np.ones((num_topics, num_terms)) * 0.01

for topic_idx, topic_name in enumerate(topic_keys):
    seeds = seed_topics[topic_name]
    for word in seeds:
        if word in dictionary.token2id:
            word_id = dictionary.token2id[word]
            eta[topic_idx, word_id] = 100.0

lda_model = LdaModel(
    corpus=corpus,
    id2word=dictionary,
    num_topics=num_topics,
    eta=eta,
    passes=20,
    iterations=400,
    random_state=42,
)

topics = lda_model.show_topics(num_words=20, formatted=False)
for topic_id, words in topics:
    guide_name = topic_keys[topic_id]
    print(f"\nTopic {topic_id} [{guide_name} Target]:")
    word_list = [word for word, prob in words]
    print(word_list)
