import json
from src.utils import PREP, load_json
from collections import Counter

INPUT = PREP / "preprocessed.json"

target1 = 'VA'
target2 = 'VV'
target3 = 'MAG'

def get_seed_clues(data):
    noun_counts = Counter()
    nnp_counts = Counter()
    adj_counts = Counter()

    for rev in data:
        for t in rev.get('tokens', []):       
            word, tag = t.split('/')
            if len(word) < 2: continue

            # Group by POS tag
            if tag in target1:
                noun_counts[word] += 1
            elif tag in target2:
                nnp_counts[word] += 1
            elif tag == target3:
                adj_counts[word] += 1

    return noun_counts.most_common(50), nnp_counts.most_common(50), adj_counts.most_common(50)


def main():
    data = load_json(INPUT)
    common_nouns, common_nnps, common_adjs = get_seed_clues(data)

    print(f"=== TOP 100 COMMON {target1} ===")
    for word, count in common_nouns:
       print(f"{word}: {count}", end=" | ")

    print(f"\n=== TOP 100 COMMON {target2} ===")
    for word, count in common_nnps:
        print(f"{word}: {count}", end=" | ")

    print(f"\n=== TOP 100 COMMON {target3} ===")
    for word, count in common_adjs:
       print(f"{word}: {count}", end=" | ")

if __name__ == "__main__":
    main()
