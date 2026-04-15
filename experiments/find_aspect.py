from collections import Counter
from pathlib import Path
import json

# Define input/output Path
BASE_DIR = Path(__file__).resolve().parent # /experiments
PROJECT_ROOT = BASE_DIR.parent
SENTENCES = PROJECT_ROOT / "data" / "raw" / "naver_reviews.json"

# Find most common tags from dataset
# Use result to write ASPECT_RULES
all_tags = []

with open(SENTENCES, "r", encoding="utf-8") as f:
    data = json.load(f)

for restaurant in data.values():
    for review in restaurant["reviews"]:
        all_tags.extend(review.get("tags", []))

counter = Counter(all_tags)

for tag, count in counter.most_common(30):
    print(tag, count)
