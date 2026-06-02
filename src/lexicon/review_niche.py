import random
from src.utils import DATASET, SCORES, load_json, save_json


def main():
    # 재현을 위해 seed 값을 고정합니다.
    INPUT = SCORES / "lexicon_scores.json"
    GOLDEN_VAL = DATASET / "golden_val.json"
    GOLDEN_TEST = DATASET / "golden_test.json"

    lexicon_results = load_json(INPUT)
    golden_val = load_json(GOLDEN_VAL)
    golden_test = load_json(GOLDEN_TEST)

    golden_set = {rev["rev_id"] for rev in golden_val} | {rev["rev_id"] for rev in golden_test}

    niche_targets = ["분위기_부정"]
    niche_reviews = {target: [] for target in niche_targets}

    for rev in lexicon_results:
        if rev.get("rev_id") in golden_set:
            continue
            
        labels = rev.get("labels", [])

        for target in niche_targets:
            if labels.get(target, 0) > 0.2:
                niche_reviews[target].append(rev)

    for target in niche_targets:
        print(f"{target} Samples (Total Found: {len(niche_reviews[target])})")
        
        candidates = niche_reviews[target]
        if not candidates:
            print("해당 조건의 리뷰가 없습니다.")
            continue
            
        # 눈으로 읽기 적당하게 10개만 무작위 추출
        sample_size = min(len(candidates), 10)
        sampled_reviews = random.sample(candidates, sample_size)
        
        for idx, rev in enumerate(sampled_reviews, 1):
            score = rev.get("labels", {}).get(target, 0)
            raw_text = rev.get("raw", "원문 없음")
            
            print(f"\n[{idx}] 렉시콘 점수: {score:.4f}")
            print(f"리뷰 원문: {raw_text}")

if __name__ == "__main__":
    main()