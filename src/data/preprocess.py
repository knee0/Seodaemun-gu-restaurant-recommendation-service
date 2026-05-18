import json
import re

from kiwipiepy import Kiwi
from src.utils.paths import DATA_DIR, RAW_DATA

INPUT = RAW_DATA
OUTPUT = DATA_DIR / "interim" / "preprocessed.json"
kiwi = Kiwi()


def normalize(text):
    text = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1+", r"\1\1", text)
    text = re.sub(r"([^\w\s])\1+", r"\1\1", text)

    text = re.sub(r"[^가-힣a-zA-Z0-9\s.,!?~]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text

# Scraped from most common EC
CLAUSE_EC = {'는데', 'ㄴ데', '은데', '지만'}

def clause_split(tokens):
    clauses = []
    cur_clause = []

    for t in tokens:
        cur_clause.append(t)
        if t.tag == 'EC' and t.form in CLAUSE_EC:
            clauses.append(cur_clause)
            cur_clause = [] # Clear for next
    if cur_clause: # Last piece of sentence
        clauses.append(cur_clause)

    return clauses


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
                sentence_tokens = kiwi.tokenize(sentence.text)
                
                split_clauses = clause_split(sentence_tokens)

                for c_idx, clause_tokens in enumerate(split_clauses):
                    clause_text = kiwi.join((t.form, t.tag) for t in clause_tokens)
                    
                    dataset.append({
                        "rev_id": rev_id,
                        "raw": clause_text,
                        "tokens": [f"{t.form}/{t.tag}" for t in clause_tokens],
                        "token_count": len(clause_tokens),
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
