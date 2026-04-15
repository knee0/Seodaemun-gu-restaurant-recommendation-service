from collections import Counter
from pathlib import Path
import json
import re
import math

# Define input/output path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
INPUT_PATH =  PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "A_tokenized.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "B_aspect_scores.json"

# Mapping made from common Naver tag & common words
# Helper code: experiments/find_aspect.py, experiments/common_words.py
ASPECT_MAP = {
    "Taste": ["맛", "음식", "고기", "메뉴", "반찬"],
    "Service": ["친절", "사장", "직원", "알바", "직접"],
    "Mood": ["분위기", "매장", "인테리어"],
    "Amount": ["양", "푸짐", "배부르", "많"],
    "Price": ["가격", "가성비", "저렴하"],
}

# Using sets would improve performance,
# but dict is easier to read and maintain.
SENTIMENT_MAP = {
    "pos": ["맛있", "맛나", "좋", "편하", "예쁘", "괜찮", "신선", "훌륭"],
    "neg": ["없", "별로", "최악", "피해", "불편"],
}

# Adverb: hint of intense sentiment
ADVERB_LIST = ["너무", "진짜", "정말", "넘", "엄청", "완전"]

# Each aspect gets sentiment score: make final score with weights
# Default weights: every aspect equal
WEIGHTS = {
    "Taste": 0.2,
    "Service": 0.2,
    "Mood": 0.2,
    "Amount": 0.2,
    "Price": 0.2
}


def score_per_aspect(data):
    results = {}

    for rid, reviews in data.items():
        # Initialize scores for each aspect
        scores = {a: 0.0 for a in ASPECT_MAP}
    
        # Number of aspects hit, used to normalize scores(average)
        hits = {a: 0 for a in ASPECT_MAP}

        for review in reviews:
            # Current data: [맛/1, 좋/2 ... ]
            tokens = [t.split('/') for t in review.split()] 

            for i, (word, tag) in enumerate(tokens):
                # Return aspect if word in ASPECT_MAP
                aspect = next((a for a, ws in ASPECT_MAP.items() if word in ws), None)
                if not aspect: continue

                # If aspect word found, detect sentiment
                hits[aspect] += 1
                # Initialize sentiment values
                sen, emp = 0, 1.0
                # Find sentiment word within window: 3 tokens nearby.
                window = tokens[max(0, i-3) : i+4]
    
                # _ is 'tag', not used here
                for w, _ in window:
                    # If adverb found, emplify sentiment
                    if w in ADVERB_LIST: emp *= 1.5
                    # If positive word found, increase sentiment
                    if w in SENTIMENT_MAP["pos"]: sen += 1
                    # If negative word found, decrease sentiment
                    elif w in SENTIMENT_MAP["neg"]: sen -= 1

                # Get final sentiment score for aspect
                scores[aspect] += (sen * emp)

        norm_scores = {}
        for a in scores:
            # Average sentiment per aspect
            avg = scores[a] / hits[a] if hits[a] > 0 else 0

            # Normalize to [-1, 1]
            norm_scores[a] = math.tanh(avg)

        # Calculate weighted total
        valid = [a for a in norm_scores if hits[a] > 0]
        if valid:
            w_sum = sum(WEIGHTS[a] for a in valid)
            final = sum(norm_scores[a] * WEIGHTS[a] for a in valid) / w_sum
        else: final = 0

        # Add attribute "Total"
        norm_scores["Total"] = final

        # Write scores for each restaurant ID
        results[rid] = norm_scores

    return results


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    aspect_scores = score_per_aspect(data)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(aspect_scores, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
