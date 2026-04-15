import json
from kiwipiepy import Kiwi
from pathlib import Path

# Define input/output Path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "naver_reviews.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "A_tokenize.json"

# Prototype of ABSA(Aspect-Based Sentiment Analysis)

# Ex) 맛있고 가성비도 좋아요!
# Sentiment Analysis: "Positive"
# ABSA: "taste": "positive", "price": "positive"
# Detect sentiment for each aspect!

# Deeper understanding (Neutral -> Good food, bad service)
# Richer content (User specific rankings, recommendations)


# Use Kiwi to tokenize & get POS
# Upgrade to Dependency Parsing later
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
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    token_data = build_token_dataset(data)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
