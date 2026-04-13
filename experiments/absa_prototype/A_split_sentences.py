import json
from kiwipiepy import Kiwi
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
RAW = PROJECT_ROOT / "data" / "raw" / "naver_reviews.json"
SENTENCES = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "01_sentence_split.json"

kiwi = Kiwi()

# Working at sentence level is useful for ABSA
def split_sentences(text):
    if not text: return []
    return [s.text.strip() for s in kiwi.split_into_sents(text)]

# From raw.json, build sentence-level dataset
def build_sentence_dataset(data):
    dataset = []

    for restaurant_id, restaurant in data.items():
        reviews = restaurant.get("reviews", [])

        for review_idx, review in enumerate(reviews):
            content = review.get("content", "")
            sentences = split_sentences(content)

            for sentence_idx, sentence in enumerate(sentences):
                if not sentence: continue
                dataset.append({
                    "sentence_id": f"{restaurant_id}_{review_idx}_{sentence_idx}",
                    "review_id": f"{restaurant_id}_{review_idx}",
                    "restaurant_id": restaurant_id,
                    "review_index": review_idx,
                    "sentence_index": sentence_idx,
                    "sentence": sentence,
                    "tags": review.get("tags", []),
                    "menu": review.get("menu", None)
                })

    return dataset

def main():
    with open(RAW, "r", encoding="utf-8") as f:
        data = json.load(f)

    sentence_data = build_sentence_dataset(data)

    with open(SENTENCES, "w", encoding="utf-8") as f:
        json.dump(sentence_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
        
