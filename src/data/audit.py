import json
from src.utils.paths import DATA_DIR
from collections import Counter

INPUT = DATA_DIR / "interim" / "step1_preprocessed.json"

def audit_data(data):
    all_tokens = []
    for rid, sentences in data.items():
        for sent in sentences:
            all_tokens.extend(sent['tokens'])

    counts = Counter(all_tokens)

    # 1. Potential New Words: Long NNGs that occur frequently
    # If "맛없없/NNG" shows up 50 times, it's a new word.
    new_words = [(t, c) for t, c in counts.items()
        if "/NNG" in t and len(t.split('/')[0]) >= 4 and c > 10]
    
    # 2. Potential Typos: Rare tokens (Count == 1)
    # Most typos are unique.
    typos = [(t, c) for t, c in counts.items() if c == 1]
    
    return sorted(new_words, key=lambda x: x[1], reverse=True), typos

def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_words, typos = audit_data(data)

    print("Potential New Words:")
    for word, count in new_words[:20]:
        print(f"{word}: {count} times")

    print("Potential Typos:")
    for word, count in typos[:20]:
        print(f"{word}")

if __name__ == "__main__":
    main()

    
