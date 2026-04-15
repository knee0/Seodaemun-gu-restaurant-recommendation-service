from collections import Counter
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
TOKENS = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "A_tokenize.json"

with open(TOKENS, "r", encoding="utf-8") as f:
    data = json.load(f)

all_nouns = []
all_verbs = []
all_adjs = []
all_advs = []

for rid in data:
    for review in data[rid]:
        # Review looks like: "맛/1 가성비/1 별로/4"
        pairs = review.split()
        for p in pairs:
            word, tag = p.split('/')
            if tag == '1': all_nouns.append(word)
            elif tag == '2': all_verbs.append(word)
            elif tag == '3': all_adjs.append(word)
            elif tag == '4': all_advs.append(word)
                                        

print("Most common Nouns:")
print(Counter(all_nouns).most_common(20))

print("Most common verbs:")
print(Counter(all_verbs).most_common(20))

print("Most common Adjectives:")
print(Counter(all_adjs).most_common(20))

print("Most common adverbs:")
print(Counter(all_advs).most_common(20))
