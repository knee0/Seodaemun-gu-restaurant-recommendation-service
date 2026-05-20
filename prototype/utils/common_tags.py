from collections import Counter
import json
from prototype.utils.paths import DATA_DIR

INPUT = DATA_DIR / "tokenized.json"

# Find most common tags from dataset
all_tags = []

with open(SENTENCES, "r", encoding="utf-8") as f:
    data = json.load(f)

for restaurant in data.values():
    for review in restaurant["reviews"]:
        all_tags.extend(review.get("tags", []))

counter = Counter(all_tags)

for tag, count in counter.most_common(30):
    print(tag, count)
