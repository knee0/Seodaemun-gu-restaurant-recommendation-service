import json
from src.utils.paths import DATA_DIR
from collections import Counter

INPUT = DATA_DIR / "interim" / "preprocessed.json"

def get_seed_clues(data):
    noun_counts = Counter()
    nnp_counts = Counter()
    adj_counts = Counter()

    # Follow your nested structure: {rev_id: [sentence1, sentence2, ...]}
    for rev in data:
        for t in rev.get('tokens', []):
            if '/' not in t: continue

            word, tag = t.split('/')

            # Ignore single letters (e.g., '것', '이', '수') to reduce noise
            if len(word) < 2: continue
                
            # Group by POS tag
            if tag in ('NNG'):
                noun_counts[word] += 1
            elif tag in ('NNP'):
                nnp_counts[word] += 1
            elif tag == 'NNG':
                adj_counts[word] += 1

    return noun_counts.most_common(100), nnp_counts.most_common(100), adj_counts.most_common(100)


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    common_nouns, common_nnps, common_adjs = get_seed_clues(data)

    print("=== TOP 100 COMMON ===")
    for word, count in common_nouns:
       print(f"{word}: {count}", end=" | ")

    print()
    print("=== TOP 100 COMMON ===")
    for word, count in common_nnps:
        print(f"{word}: {count}", end=" | ")

    print()
#    print("\n=== TOP 100 COMMON ===")
#    for word, count in common_adjs:
#       print(f"{word}: {count}", end=" | ")

if __name__ == "__main__":
    main()
