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
    LEX_THRESH = 0.2

    for rev in lexicon_results:
        if rev.get("rev_id") in golden_set:
            continue
            
        labels = rev.get("labels", {})
        cleaned_labels = {label: (1.0 if score >= LEX_THRESH else 0.0) for label, score in labels.items()}

        total_score = sum(cleaned_labels.values())
        if total_score == 0:
            continue
        
        food_pos_score = cleaned_labels.get("음식_긍정", 0.0)
        rev["labels"] = cleaned_labels

        if food_pos_score > 0 and total_score == food_pos_score:
            single_food.append(rev)
        else:
            other_reviews.append(rev)

    keep_count = int(len(single_food) * 0.2)
    sampled_single_food = random.sample(single_food, keep_count)

    result = sampled_single_food + other_reviews
    random.shuffle(result)

    print(f"학습 데이터 수: {len(result)} (음식_긍정: {len(sampled_single_food)}, 기타: {len(other_reviews)})")
    save_json(result, TRAIN_DATA)


if __name__ == "__main__":
    main()