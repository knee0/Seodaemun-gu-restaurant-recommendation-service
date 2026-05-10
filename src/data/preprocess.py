import json
import re

from kiwipiepy import Kiwi
from src.utils.paths import DATA_DIR, RAW_DATA

INPUT = RAW_DATA
OUTPUT = DATA_DIR / "interim" / "step1_preprocessed.json"
kiwi = Kiwi()


def normalize(text):
    text = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1+", r"\1\1", text)
    text = re.sub(r"([^\w\s])\1+", r"\1\1", text)

    text = re.sub(r"[^가-힣a-zA-Z0-9\s.,!?~]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def preprocess(data):
    dataset = []

    for rid, restaurant in data.items():
        for idx, review in enumerate(restaurant.get("reviews", [])):
            # Create unique Review ID
            rev_id = f"{rid}_{idx}"

            raw = review.get("content", "").strip()
            text = normalize(raw)
            if not text:
                continue

            # Split by sentence: BERT has length limits
            # Also ensures better aspect-sentiment mapping
            sentences = kiwi.split_into_sents(text)

            for sentence in sentences:
                tokens = kiwi.tokenize(sentence.text)

                # Format as Morpheme/Tag -> ['맛은'/NNG], ['좋'/VA], ...
                morpheme_tags = [f"{t.form}/{t.tag}" for t in tokens]

                dataset.append({
                        "rev_id": rev_id,
                        "raw": sentence.text,
                        "tokens": morpheme_tags,
                        "token_count": len(morpheme_tags),
                })
                                
    return dataset


# Write into new json
def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    token_data = preprocess(data)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
