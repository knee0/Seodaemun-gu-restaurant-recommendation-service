import json
import torch
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from src.utils import DATA_DIR, load_json
from umap import UMAP
from hdbscan import HDBSCAN

INPUT = DATA_DIR / "interim" / "step1_preprocessed.json"
device = "cuda" if torch.cuda.is_available() else "cpu"
embedding_model = SentenceTransformer("jhgan/ko-sroberta-multitask", device=device)

data = load_json(INPUT)

stopwords = ["추천", "최고", "방문", "오늘", "리뷰", "생각", "사람", "진짜", "정말",
             "완전", "처음", "정도", "때문", "사용", "이용", "사진", "메뉴", "음식",
             "그렇", "나오", "시키", "들어가", "이렇", "모르", "드리", "오랜만",
             "이대", "식사", "느낌", "자리", "가게", "다음", "연희동"]

allowed_tags = ['NNG', 'NNP', 'VA']

raw_docs = []
cleaned_docs = []

for rev in data:
    tokens = [t.split("/")[0] for t in rev["tokens"] if any(tag in t for tag in allowed_tags)]
    cleaned = [w for w in tokens if len(w) > 1 and w not in stopwords]
    joined_cleaned = " ".join(cleaned).strip()

    raw_text = rev.get("raw", "").strip()
    if not isinstance(raw_text, str): continue

    if joined_cleaned and raw_text:
        raw_docs.append(raw_text)
        cleaned_docs.append(joined_cleaned)


embeddings = embedding_model.encode(raw_docs, batch_size = 64, show_progress_bar=True, convert_to_numpy=True)

seed_topic_list = [
    ["고기", "국물", "소스", "반찬", "재료", "파스타"],  # Taste
    ["친절", "사장", "직원", "서비스", "감사"],          # Service
    ["분위기", "매장", "느낌", "자리", "인테리어"],      # Vibe
    ["가성비", "가격", "저렴하", "비싸"],                # Price
    ["배부르", "푸짐하", "든든하", "종류"],               # Quantity
    ["웨이팅", "주차", "예약", "신촌"]                   # Noise
]


vectorizer = CountVectorizer(token_pattern=r'(?u)\b\w+\b', min_df=2)

representation_model = KeyBERTInspired()
umap_model = UMAP(n_neighbors=20, n_components=5, min_dist=0.05, metric='cosine', random_state=42)
hdbscan_model = HDBSCAN(min_cluster_size=20, min_samples=5, prediction_data=True, gen_min_span_tree=True)

topic_model = BERTopic(embedding_model=embedding_model,
                       vectorizer_model=vectorizer,
                       representation_model=representation_model,
                       umap_model=umap_model,
                       hdbscan_model=hdbscan_model,
                       seed_topic_list=seed_topic_list)

topics, probs = topic_model.fit_transform(cleaned_docs, embeddings=embeddings)
new_topics = topic_model.reduce_outliers(cleaned_docs, topics, strategy="embeddings", embeddings=embeddings)
topic_model.update_topics(cleaned_docs, topics=new_topics)

# Put this right before your print statement to stop truncation
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 50)

# Print just the top 15 main topic summaries
print("=== Top 15 Main Topic Summaries ===")
print(topic_model.get_topic_info()[["Topic", "Count", "Name"]].head(15))

for topic_id in range(5):
    print(f"\nTopic {topic_id} Keywords:")
    print(topic_model.get_topic(topic_id))
