from collections import Counter
from pathlib import Path
import json

all_tags = []

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
SENTENCES = PROJECT_ROOT / "data" / "processed" / "01_sentence_split.json"

with open(SENTENCES, "r", encoding="utf-8") as f:
    data = json.load(f)

for row in data:
    all_tags.extend(row["tags"])

counter = Counter(all_tags)

print(counter.most_common(50))