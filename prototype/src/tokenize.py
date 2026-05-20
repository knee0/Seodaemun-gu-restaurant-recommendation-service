import json
from kiwipiepy import Kiwi
from pathlib import Path
from prototype.utils.paths import RAW_DATA, DATA_DIR

INPUT = RAW_DATA
OUTPUT = DATA_DIR / "tokenized.json"

# Prototype of ABSA(Aspect-Based Sentiment Analysis)

# Use Kiwi to tokenize & get POS
kiwi = Kiwi()

def build_token_dataset(data):
    dataset = {}

    # Select vital POS for ABSA
    # 일반 명사(Aspect), 형용사, 동사, 부사(Sentiment)
    ASPECT_TAGS = {'NNG', 'VA', 'VV', 'MAG'}
    # Numbers easier to handle
    TAG_MAP = {'NNG': 1, 'VA': 2, 'VV': 3, 'MAG': 4}
 
    for rid, rest in data.items():
        pos_rev = []

        for rev in rest.get("reviews", []):
            tokens = kiwi.tokenize(rev.get("content", ""))
            # Take vital POS tokens only
            vital = " ".join([f"{t.form}/{TAG_MAP[t.tag]}" for t in tokens if t.tag in ASPECT_TAGS])
            if vital: pos_rev.append(vital)
        dataset[rid] = pos_rev
    return dataset

# Write into new.json
def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    token_data = build_token_dataset(data)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()