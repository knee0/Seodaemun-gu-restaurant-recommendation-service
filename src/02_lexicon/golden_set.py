import json
import random
from collections import defaultdict
from src.utils import DATASET, SCORES, load_json, save_json

def main():
    random.seed(42)

    INPUT = SCORES / "lexicon_scores.json"
    GOLDEN_VAL = DATASET / "golden_val.json"
    GOLDEN_TEST = DATASET / "golden_test.json"
    TRAIN_DATA = DATASET / "train_data.json"

    results = load_json(INPUT)

    ghost_pool = []
    complex_pool = []
    single_pool = defaultdict(list)
    
    for rev in results:
        labels = rev["labels"]
        
        if not labels:
            ghost_pool.append(rev)
            continue

        if len(labels) > 1:
            complex_pool.append(rev)
        elif len(labels) == 1:
            single_pool[labels[0]].append(rev)

    GHOST_TARGET = 250
    COMPLEX_TARGET = 250
    STRATIFIED_TARGET = 500
    
    golden_ghosts = random.sample(ghost_pool, GHOST_TARGET)
    print(f"Sampled {len(golden_ghosts)} Ghost reviews.")

    golden_complex = random.sample(complex_pool, COMPLEX_TARGET)
    print(f"Sampled {len(golden_complex)} Complex multi-aspect reviews.")

    # Multi-Label Stratified Single-Aspect Reviews
    total_single = 0
    for reviews in single_pool.values():
        total_single += len(reviews)
    aspect_ratios = {}
    
    # Calculate ratios of each aspect
    for aspect, reviews in single_pool.items():
        ratio = len(reviews) / total_single
        aspect_ratios[aspect] = max(20, int(ratio * STRATIFIED_TARGET))

    # Adjust largest aspect to hit exactly 500
    remainder = STRATIFIED_TARGET - sum(aspect_ratios.values())
    largest_aspect = max(aspect_ratios, key=aspect_ratios.get)
    aspect_ratios[largest_aspect] += remainder

    golden_stratified = []
    for aspect, count in aspect_ratios.items():
        sampled_for_aspect = random.sample(single_pool[aspect], count)
        golden_stratified.extend(sampled_for_aspect)
        print(f"[{aspect}]: {count} samples collected.")
    print(f"Sampled {len(golden_stratified)} Stratified Single-Aspect reviews.")

    # 5. Assemble, Shuffle, and Split Golden Set 50/50
    golden_set = golden_ghosts + golden_complex + golden_stratified
    random.shuffle(golden_set)

    val_set = golden_set[:500]
    test_set = golden_set[500:]

    # 6. Extract Clean Training Pool (Labeled Data ONLY, minus Golden Set instances)
    # Using python object IDs to guarantee exact object exclusions without string collision risks
    golden_ids = set(rev["rev_id"] for rev in golden_set)
    train_set = []
    for rev in results:
        if rev["labels"] and rev["rev_id"] not in golden_ids:
            train_set.append(rev)

    save_json(val_set, GOLDEN_VAL)
    save_json(test_set, GOLDEN_TEST)
    save_json(train_set, TRAIN_DATA)

    print("\n=== SPLIT GENERATION REPORT ===")
    print(f"Validation : {len(val_set)} samples saved.")
    print(f"Testing    : {len(test_set)} samples saved.")
    print(f"Training   : {len(train_set)} samples saved.")

if __name__ == "__main__":
    main()
