import json
import random
from collections import defaultdict
from src.utils import SCORES, load_json

INPUT = SCORES / "lexicon_scores.json"
results = load_json(INPUT)

total_reviews = len(results)
valid_count = 0
ghost_count = 0

aspect_counts = defaultdict(int)
complex_samples = []
ghost_samples = []

for rev in results:
    labels = rev["labels"]

    if not labels:
        ghost_count += 1
        ghost_samples.append(rev["raw"])
        continue

    valid_count += 1
    found_aspects = []
    
    for aspect in labels:
        found_aspects.append(aspect)
        aspect_counts[aspect] += 1

    if len(found_aspects) > 1:
        complex_samples.append({
            "raw": rev["raw"],
            "aspects": found_aspects,
            "count": len(found_aspects)
        })


# === PRINTING THE REPORT ===

print("=== ABSA COVERAGE REPORT ===")
print(f"Total Reviews Analyzed: {total_reviews}")
print(f"Reviews with Aspect/Sentiment: {valid_count} ({valid_count/total_reviews*100:.1f}%)")
print(f"All-Null Ghost Reviews: {ghost_count} ({ghost_count/total_reviews*100:.1f}%)")
print("-" * 40)

print("=== DETAILED ASPECT STATISTICS ===")
if valid_count > 0:
    # Sort aspects by mention count (highest first)
    sorted_aspects = sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True)
    for aspect, count in sorted_aspects:
        # Calculate frequency relative to total valid reviews
        freq_pct = (count / valid_count) * 100
        print(f"{aspect} Mentions: {count} ({freq_pct:.1f}% of valid)")

print("\n=== INVESTIGATING GHOST SAMPLES ===")
sample_size = min(20, len(ghost_samples))
random_ghosts = random.sample(ghost_samples, sample_size)
for idx, g in enumerate(random_ghosts):
    print(f"[{idx+1}] Raw Text: {g}")


print("\n=== INVESTIGATING COMPLEX SAMPLES (MULTIPLE ASPECTS) ===")
complex_pct = (len(complex_samples) / valid_count) * 100
print(f"Total Complex Reviews (with >1 Aspect): {len(complex_samples)} ({complex_pct:.1f}% of valid)")

complex_samples.sort(key=lambda x: x["count"], reverse=True)
sample_size = min(20, len(complex_samples))
for idx, c in enumerate(complex_samples[:sample_size]):
    print(f"[{idx+1}] Aspect Count: [{c['count']}] Aspects: [{c['aspects']}]")
    print(f"Raw Text: {c['raw']}")
