import json
from collections import defaultdict

import numpy as np
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from src.score.aggregate import (
    aggregate_restaurant_scores,
    aggregate_review_aspect_scores,
    build_category_rankings,
    save_category_rankings,
    save_scores,
)
from src.utils.paths import DATA_DIR, MODELS, RAW_DATA, INTERIM

print(torch.cuda.is_available())

MODEL_PATH = MODELS / "koelectra_aspect_model"
ASPECTS = ["맛", "서비스", "분위기", "가격", "시스템"]
LABEL_MAP = {0: "Negative", 1: "Positive"}
BATCH_SIZE = 16

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
model = model.half()
model.to(device)
model.eval()

with open(RAW_DATA, "r", encoding="utf-8") as f:
    raw_data = json.load(f)
id_to_name = {r_id: r_data.get("metadata", {}).get("name", r_id) for r_id, r_data in raw_data.items()}

with open(INTERIM / "preprocessed.json", "r", encoding="utf-8") as f:
    pre_data = json.load(f)

restaurant_tracking = defaultdict(lambda: {
    "review_chunks": defaultdict(lambda: {
        "aspect_scores": {a: [] for a in ASPECTS},
        "sentences": [],
    })
})

for i in tqdm(range(0, len(pre_data), BATCH_SIZE)):
    batch_items = pre_data[i : i + BATCH_SIZE]
    
    flat_texts = []
    flat_aspects = []
    meta_info = []  # Tracking metadata to map predictions back correctly
    
    for item in batch_items:
        text = item.get("raw", "")
        if not text.strip(): 
            continue
            
        # Extract restaurant ID from your rev_id (e.g., "32876009_0" -> "32876009")
        rev_id = item["rev_id"]
        r_id = rev_id.split("_")[0]
        
        for aspect in ASPECTS:
            flat_texts.append(text)
            flat_aspects.append(aspect)
            meta_info.append((r_id, rev_id, text, aspect))
            
    if not flat_texts:
        continue

    # Tokenize the entire flat batch at once
    inputs = tokenizer(
        flat_texts, 
        text_pair=flat_aspects, 
        return_tensors="pt", 
        truncation=True, 
        padding=True, 
        max_length=128
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}


    with torch.no_grad():
        logits = model(**inputs).logits
        # Use softmax to get the probability of class 1 (Positive)
        probs = torch.softmax(logits, dim=1)
        pos_probs = probs[:, 1].cpu().numpy()

    num_aspects = len(ASPECTS)
    for idx in range(0, len(meta_info), num_aspects):
        chunk_meta = meta_info[idx : idx + num_aspects]
        chunk_probs = pos_probs[idx : idx + num_aspects]
        
        current_rid = chunk_meta[0][0]
        current_rev_id = chunk_meta[0][1]
        current_text = chunk_meta[0][2]
        
        rev_result = {}
        review_bucket = restaurant_tracking[current_rid]["review_chunks"][current_rev_id]
        for meta, prob in zip(chunk_meta, chunk_probs):
            aspect = meta[3]
            prob_val = round(float(prob), 3)
            
            rev_result[aspect] = prob_val
            review_bucket["aspect_scores"][aspect].append(prob)
            
        review_bucket["sentences"].append({
            "rev_id": current_rev_id,
            "review": current_text,
            "analysis": rev_result
        })


# 5. Calculate Final Scores & Weights
def get_raw_review(r_id, rev_id):
    try:
        review_idx = int(rev_id.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return {}

    reviews = raw_data.get(r_id, {}).get("reviews", [])
    if 0 <= review_idx < len(reviews):
        return reviews[review_idx]
    return {}


restaurant_results = {}
for r_id, info in restaurant_tracking.items():
    review_items = []
    for rev_id, review_info in info["review_chunks"].items():
        raw_review = get_raw_review(r_id, rev_id)
        review_text = raw_review.get("content", "") if isinstance(raw_review, dict) else str(raw_review)
        if not review_text:
            review_text = " ".join(sentence["review"] for sentence in review_info["sentences"])

        review_aspect_scores = {
            a: round(float(np.mean(scores)) if scores else 0, 3)
            for a, scores in review_info["aspect_scores"].items()
        }
        review_items.append({
            "rev_id": rev_id,
            "review": review_text,
            "aspect_scores": review_aspect_scores,
            "metadata": raw_review if isinstance(raw_review, dict) else {},
            "sentences": review_info["sentences"],
        })

    final_scores, weighted_reviews, review_weight_summary = aggregate_review_aspect_scores(review_items)
    sentence_count = sum(len(review["sentences"]) for review in review_items)

    restaurant_results[r_id] = {
        "name": id_to_name.get(r_id, r_id),
        "review_count": len(review_items),
        "sentence_count": sentence_count,
        "aspect_scores": final_scores,
        "review_weights_applied": True,
        "review_weight_summary": review_weight_summary,
        "reviews": weighted_reviews,
    }


sorted_results = aggregate_restaurant_scores(restaurant_results, raw_data)

with open(INTERIM/"absa_scores.json", "w", encoding="utf-8") as f:
    json.dump(sorted_results, f, ensure_ascii=False, indent=2)
save_scores(sorted_results, DATA_DIR / "final" / "restaurant_scores.json")
save_category_rankings(
    build_category_rankings(sorted_results),
    DATA_DIR / "final" / "category_rankings.json",
)

print("\n===== TOP 10 Restaurants =====\n")
for idx, (rid, info) in enumerate(list(sorted_results.items())[:10]):
    print(f"{idx+1}. {info['name']}")
    print(f"추천점수: {info['rec_score']}")
    print(f"카테고리 점수: {info['aspect_scores']}\n")
