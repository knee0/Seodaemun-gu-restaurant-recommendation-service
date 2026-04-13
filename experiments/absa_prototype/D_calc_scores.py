import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent

INPUT_PATH = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "03_sentiments_added.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "04_restaurant_scores.json"
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "naver_reviews.json"

# Sentiment to score
SENTIMENT_MAP = {
     "positive": 1,
     "neutral": 0,
     "negative": -1,
     "mixed": 0
}

# Load names for readable result
def load_restaurant_names(raw_data):
    mapping = {}

    for rid, info in raw_data.items():
        name = info.get("metadata", {}).get("name", "Unknown")
        mapping[rid] = name

    return mapping

# Attach name as attribute
def attach_names(data, name_map):
    for rid, info in data.items():
        info["name"] = name_map.get(rid, "Unknown")
    return data

# Add score of all review
def aggregate_scores(data):
    restaurant_scores = defaultdict(lambda: defaultdict(list))

    for row in data:
        rid = row["restaurant_id"]
        aspect_sentiments = row.get("aspect_sentiments", {})

        for aspect, sentiment in aspect_sentiments.items():
            score = SENTIMENT_MAP.get(sentiment, 0)
            restaurant_scores[rid][aspect].append(score)

    return restaurant_scores

# Find average score
def compute_average(scores_dict):
    result = {}

    for rid, aspects in scores_dict.items():
        result[rid] = {}

        all_scores = []
        for aspect, scores in aspects.items():
            if scores:
                avg = sum(scores) / len(scores)
                result[rid][aspect] = avg
                all_scores.extend(scores)

        # Final score
        if all_scores:
            result[rid]["overall_score"] = sum(all_scores) / len(all_scores)
        else:
            result[rid]["overall_score"] = 0

    return result


def assign_tier(score):
    if score >= 0.9:
        return "S"
    elif score >= 0.8:
        return "A"
    elif score >= 0.7:
        return "B"
    elif score >= 0.6:
        return "C"
    else:
        return "D"


def add_tiers(data):
    for rid, info in data.items():
        score = info.get("overall_score", 0)
        info["tier"] = assign_tier(score)
    return data


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(RAW_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    name_map = load_restaurant_names(raw)

    aggregated = aggregate_scores(data)
    averaged = compute_average(aggregated)
    final = add_tiers(averaged)

    final = attach_names(final, name_map)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
