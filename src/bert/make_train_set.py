import random
from src.utils import DATASET, SCORES, load_json, save_json


def main():
    # 재현을 위해 seed 값을 고정합니다.
    random.seed(42)

    INPUT = SCORES / "lexicon_scores.json"
    GOLDEN_VAL = DATASET / "golden_val.json"
    GOLDEN_TEST = DATASET / "golden_test.json"
    TRAIN_DATA = DATASET / "train_data.json"

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

    for rev in lexicon_results:
        if rev.get("rev_id") in golden_set:
            continue
            
        labels = rev.get("labels", [])

        if not labels:
            continue
        
        if labels == ["음식_긍정"]:
            single_food.append(rev)
        else:
            other_reviews.append(rev)

    keep_count = int(len(single_food) * 0.15)
    sampled_single_food = random.sample(single_food, keep_count)

    result = sampled_single_food + other_reviews
    random.shuffle(result)

    print(f"학습 데이터 수: {len(result)} (음식_긍정: {len(sampled_single_food)}, 기타: {len(other_reviews)})")
    save_json(result, TRAIN_DATA)


if __name__ == "__main__":
    main()