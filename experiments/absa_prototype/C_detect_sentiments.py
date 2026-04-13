from collections import Counter
from pathlib import Path
import json
import re

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
NO_SEN = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "02_aspects_added.json"
WITH_SEN = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "03_sentiments_added.json"

# Extremly basic sentiment lexicon
POS_WORDS = ["맛있", "좋", "훌륭", "최고", "추천", "만족",
    "깔끔", "친절", "신선", "훌륭", "완벽", "이쁘", "예쁘"]

NEG_WORDS = ["맛없", "나쁘", "최악", "비싸", "불친절", "별로",
     "느리", "짜", "싱겁", "실망", "아쉽", "더럽", "시끄럽", "불편"]

NEGATIONS = ["않", "별로", "못", "안"]

def detect_sentiment(text):
    # Count matches
    pos_score = sum(1 for w in POS_WORDS if w in text)
    neg_score = sum(1 for w in NEG_WORDS if w in text)
        
    # Check negation near words (very basic context)
    has_negation = any(n in text for n in NEGATIONS)
        
    if pos_score > neg_score:
        return "negative" if has_negation else "positive"
    if neg_score > pos_score:
        return "positive" if has_negation else "negative"
    if pos_score > 0 and neg_score > 0:
        return "mixed"
    return "neutral"

# 
def per_aspect_sentiments(row):
    sentence = row.get("sentence", "")
    aspects = row.get("sentence_aspects", [])
    results = {}

    for aspect in aspects:
        results[aspect] = detect_sentiment(sentence)
                            
    return results


# Make new .json
def main():
    with open(NO_SEN, "r", encoding="utf-8") as f:
        data = json.load(f)

    for row in data:
        row["aspect_sentiments"] = per_aspect_sentiments(row)
    

    with open(WITH_SEN, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
