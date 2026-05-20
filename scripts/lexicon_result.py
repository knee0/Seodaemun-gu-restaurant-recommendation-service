import json
from src.utils import INTERIM, load_json
import random

INPUT = INTERIM / "aspect_scores.json"
results = load_json(INPUT)

total_reviews = len(results)
valid_count = 0
all_null_count = 0

# New counters for detailed statistics
aspect_counts = {}
aspect_score_sums = {}

# List to collect complex samples for the golden set
complex_samples = []

for rev in results:
    scores = rev["aspect_score"]
    
    # 1. Base Coverage Check
    if all(v is None for v in scores.values()):
        all_null_count += 1
        continue  # Skip to next review if it's a ghost review
        
    valid_count += 1

    # Track complex sentences with multiple categories identified and store their scores
    identified_aspects = {aspect: score for aspect, score in scores.items() if score is not None}
    if len(identified_aspects) > 1:
        complex_samples.append({
            "raw": rev["raw"],
            "aspects": identified_aspects,  # Stores a dictionary of aspect: score
            "count": len(identified_aspects)
        })
    
    # 2. Detailed Aspect Breakdown
    for aspect, score in scores.items():
        if score is not None:
            # Initialize keys if they don't exist yet
            if aspect not in aspect_counts:
                aspect_counts[aspect] = 0
                aspect_score_sums[aspect] = 0.0
                
            aspect_counts[aspect] += 1
            aspect_score_sums[aspect] += score

# === PRINTING THE REPORT ===

print("=== ABSA COVERAGE REPORT ===")
print(f"Total Reviews Analyzed: {total_reviews}")
print(f"Reviews with Aspect/Sentiment: {valid_count} ({valid_count/total_reviews*100:.1f}%)")
print(f"All-Null Ghost Reviews: {all_null_count} ({all_null_count/total_reviews*100:.1f}%)")
print("-" * 40)

print("=== DETAILED ASPECT STATISTICS ===")
if valid_count > 0:
    # Sort aspects by mention count (highest first)
    sorted_aspects = sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True)
    
    for aspect, count in sorted_aspects:
        # Calculate frequency relative to total valid reviews
        freq_pct = (count / valid_count) * 100
        # Calculate average sentiment score for this aspect
        avg_score = aspect_score_sums[aspect] / count
        
        print(f"[{aspect}] Mentions: {count} ({freq_pct:.1f}% of valid) | Avg Score: {avg_score:.4f}")
else:
    print("No valid aspect data found to generate detailed statistics.")

print("\n=== INVESTIGATING GHOST SAMPLES ===")

# Force filter exactly what is failing
ghost_samples = []
for rev in results:
    if all(v is None for v in rev["aspect_score"].values()):
        ghost_samples.append(rev)

if not ghost_samples:
    print("Check if aspect_scores.json was overwritten properly")
else:
    sample_size = min(20, len(ghost_samples))
    random_ghosts = random.sample(ghost_samples, sample_size)
    for idx, g in enumerate(random_ghosts):
        print(f"[{idx+1}] Raw Text: {g['raw']}")


print("\n=== INVESTIGATING COMPLEX SAMPLES (MULTIPLE ASPECTS) ===")
if valid_count > 0:
    complex_pct = (len(complex_samples) / valid_count) * 100
    print(f"Total Complex Reviews (with >1 Aspect): {len(complex_samples)} ({complex_pct:.1f}% of valid)")
else:
    print(f"Total Complex Reviews (with >1 Aspect): {len(complex_samples)}")

if not complex_samples:
    print("No reviews found with multiple aspects.")
else:
    # Sort complex samples by the number of identified aspects in descending order
    complex_samples.sort(key=lambda x: x["count"], reverse=True)
    
    # Display top 20 complex samples
    sample_size = min(20, len(complex_samples))
    for idx, c in enumerate(complex_samples[:sample_size]):
        # Format each aspect to display its name and the predicted score
        aspects_with_scores = [f"{aspect} ({score:+.1f})" for aspect, score in c["aspects"].items()]
        aspects_str = ", ".join(aspects_with_scores)
        
        print(f"[{idx+1}] [Aspect Count: {c['count']}] Aspects: {aspects_str}")
        print(f"    Raw Text: {c['raw']}")