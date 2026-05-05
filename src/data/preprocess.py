import json
from kiwipiepy import Kiwi
from utils.paths import RAW_DATA, DATA_DIR

# Define input/output Path
INPUT = RAW_DATA
OUTPUT = DATA_DIR / "interim" / "step1_preprocessed.json"

# This is just a skeleton from the prototype:
# add new features as you see fit.

# Use Kiwi to tokenize & get POS
kiwi = Kiwi()

def build_token_dataset(data):
    dataset = {}

    # Select vital POS for ABSA
    # 일반 명사 for Aspect, 형용사, 동사, 부사 for Sentiment
    ASPECT_TAGS = {'NNG', 'VA', 'VV', 'MAG'}
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

# Write into new json
def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    token_data = build_token_dataset(data)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, indent=4)
