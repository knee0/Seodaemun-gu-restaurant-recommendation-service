import json
import pandas as pd
from tqdm import tqdm
from src.utils.paths import MODELS, RAW_DATA, INTERIM
import numpy as np
from datasets import Dataset, ClassLabel
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from collections import defaultdict
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, DataCollatorWithPadding

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
    "aspect_scores": {a: [] for a in ASPECTS},
    "reviews": []
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
        r_id = item["rev_id"].split("_")[0]
        
        for aspect in ASPECTS:
            flat_texts.append(text)
            flat_aspects.append(aspect)
            meta_info.append((r_id, text, aspect))
            
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
        current_text = chunk_meta[0][1]
        
        rev_result = {}
        for meta, prob in zip(chunk_meta, chunk_probs):
            aspect = meta[2]
            prob_val = round(float(prob), 3)
            
            rev_result[aspect] = prob_val
            restaurant_tracking[current_rid]["aspect_scores"][aspect].append(prob)
            
        restaurant_tracking[current_rid]["reviews"].append({
            "review": current_text,
            "analysis": rev_result
        })


# 5. Calculate Final Scores & Weights
restaurant_results = {}
for r_id, info in restaurant_tracking.items():
    final_scores = {
        a: round(float(np.mean(scores)) if scores else 0, 3) 
        for a, scores in info["aspect_scores"].items()
    }

    rec_score = round(
        final_scores["맛"] * 0.4 +
        final_scores["서비스"] * 0.2 +
        final_scores["분위기"] * 0.15 +
        final_scores["시스템"] * 0.15 +
        final_scores["가격"] * 0.1,
        3
    )

    restaurant_results[r_id] = {
        "name": id_to_name.get(r_id, r_id),
        "review_count": len(info["reviews"]),
        "aspect_scores": final_scores,
        "rec_score": rec_score,
        "reviews": info["reviews"]
    }


sorted_results = dict(sorted(restaurant_results.items(), key=lambda x: x[1]["rec_score"], reverse=True))

with open(INTERIM/"absa_scores.json", "w", encoding="utf-8") as f:
    json.dump(sorted_results, f, ensure_ascii=False, indent=2)

print("\n===== TOP 10 Restaurants =====\n")
for idx, (rid, info) in enumerate(list(sorted_results.items())[:10]):
    print(f"{idx+1}. {info['name']}")
    print(f"추천점수: {info['rec_score']}")
    print(f"카테고리 점수: {info['aspect_scores']}\n")
