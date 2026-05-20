import json
import re
from kiwipiepy import Kiwi
from src.utils import RAW_DATA, INTERIM, load_json, save_json

INPUT = RAW_DATA
OUTPUT = INTERIM / "preprocessed.json"

kiwi = Kiwi()

def normalize(text):
    # ㅋㅋㅋㅋ, ㅠㅠㅠ -> ㅋㅋ, ㅠㅠ
    text = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1+", r"\1\1", text)

    # ,,, | ... -> , | .
    text = re.sub(r"([^\w\s])\1+", r"\1", text)

    # Strip weird characters
    text = re.sub(r"[^가-힣a-zA-Z0-9\s.,!?~]", "", text)

    # Clean up whitespace around punctuation
    text = re.sub(r"\s+([.,!?~])", r"\1", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Scraped from most common EC.
# Want to split reviews into clauses with single aspect
# Open to suggestions!
CLAUSE_EC = {'는데', 'ㄴ데', '은데', '지만'}

# Take sentence, split at CLAUSE_EC
def clause_split(tokens):
    clauses = []
    current_clause = []

    for t in tokens:
        current_clause.append(t)
        if t.tag == 'EC' and t.form in CLAUSE_EC:
            clauses.append(current_clause)
            # Clear for next clause
            current_clause = []

    # If left, append last clause
    if current_clause:
        clauses.append(current_clause)

    return clauses


def preprocess(data):
    dataset = []

    for rid, restaurant in data.items():
        for idx, review in enumerate(restaurant.get("reviews", [])):
            # Create unique Review ID
            # Needed to connect with metadata, later in aggregate.py
            rev_id = f"{rid}_{idx}"

            raw = review.get("content", "").strip()
            text = normalize(raw)
            if not text: continue

            # Split by sentence: BERT has length limits
            # Also ensures better aspect-sentiment mapping
            sentences = kiwi.split_into_sents(text)
            for sentence in sentences:
                sentence_tokens = kiwi.tokenize(sentence.text)         
                split_clauses = clause_split(sentence_tokens)

                for c_idx, clause_tokens in enumerate(split_clauses):
                    # Since we split clauses, raw sentence is lost
                    # Use kiwi to reconstruct sentence from tokens
                    # Not used for training: just for human-readability
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
    data = load_json(INPUT)
    token_data = preprocess(data)
    save_json(token_data, OUTPUT, 4)

if __name__ == "__main__":
    main()
