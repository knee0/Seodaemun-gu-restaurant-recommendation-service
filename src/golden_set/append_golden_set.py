import random
from src.utils import DATASET, SCORES, load_json, save_json


def main():
    # 재현을 위해 seed 값을 고정합니다.
    random.seed(42)

    INPUT = SCORES / "lexicon_scores.json"
    GOLDEN_VAL = DATASET / "golden_val.json"
    GOLDEN_TEST = DATASET / "golden_test.json"
    TRAIN_DATA = DATASET / "train_data.json"
    GOLDEN_VAL_APPEND = DATASET / "golden_val_append_raw.json"
    GOLDEN_TEST_APPEND = DATASET / "golden_test_append_raw.json"

    lexicon_results = load_json(INPUT)
    golden_val = load_json(GOLDEN_VAL)
    golden_test = load_json(GOLDEN_TEST)

    golden_set = set()
    for rev in golden_val:
        golden_set.add(rev["rev_id"])
    for rev in golden_test:
        golden_set.add(rev["rev_id"])


    single_food = []
    other_reviews = []

    niche_targets = ["서비스_부정", "분위기_부정", "가격_부정", "편의성_부정"]
    niche_reviews = {target: [] for target in niche_targets}
    extracted_for_gold = []

    for rev in lexicon_results:
        if rev.get("rev_id") in golden_set:
            continue
            
        labels = rev.get("labels", [])

        for target in niche_targets:
            if target in labels:
                niche_reviews[target].append(rev)

        if not labels:
            continue
        
        if labels == ["음식_긍정"]:
            single_food.append(rev)
        else:
            other_reviews.append(rev)

    keep_count = int(len(single_food) * 0.2)
    sampled_single_food = random.sample(single_food, keep_count)

    result = sampled_single_food + other_reviews
    random.shuffle(result)

    print(f"학습 데이터 수: {len(result)} (음식_긍정: {len(sampled_single_food)}, 기타: {len(other_reviews)})")
    save_json(result, TRAIN_DATA)


    assigned_val_ids = set()
    assigned_test_ids = set()

    golden_val_append = []
    golden_test_append = []

    # Sort targets by scarcity so the rarest class gets first dibs on candidates
    sorted_targets = sorted(niche_targets, key=lambda t: len(niche_reviews[t]))

    for target in sorted_targets:
        all_candidates = niche_reviews[target]
    
        # Filter out reviews already assigned
        valid_candidates = [rev for rev in all_candidates 
            if rev["rev_id"] not in assigned_val_ids and rev["rev_id"] not in assigned_test_ids]
    
        print(f"[{target}] Total: {len(all_candidates)} -> Available (Unassigned): {len(valid_candidates)}")
    
        # 50 fresh, unique reviews for this category
        sample_size = min(len(valid_candidates), 100)
        sampled_cluster = random.sample(valid_candidates, sample_size)
    
        half = sample_size // 2
        val_slice = sampled_cluster[:half]
        test_slice = sampled_cluster[half:]
    
        # Track and append safely
        for rev in val_slice:
            assigned_val_ids.add(rev["rev_id"])
            golden_val_append.append(rev)
        
        for rev in test_slice:
            assigned_test_ids.add(rev["rev_id"])
            golden_test_append.append(rev)

        print(f"Added {len(val_slice)} to Val, {len(test_slice)} to Test.")

    assert assigned_val_ids.isdisjoint(assigned_test_ids), "Data leak detected"


    save_json(golden_val_append, GOLDEN_VAL_APPEND)
    save_json(golden_test_append, GOLDEN_TEST_APPEND)

if __name__ == "__main__":
    main()