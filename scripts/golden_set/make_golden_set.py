import json
import random
from collections import defaultdict
from src.utils import DATASET, SCORES, load_json, save_json


# BERT Validation, 모델 성능 평가에는 Golden set(사람이 라벨링한 정답 데이터)이 필요합니다.
# Golden set에 사용할 리뷰(직접 라벨링할 리뷰)를 선정하기 위한 코드입니다.


def main():
    # 재현을 위해 seed 값을 고정합니다.
    random.seed(42)

    INPUT = SCORES / "lexicon_scores.json"
    GOLDEN_VAL = DATASET / "golden_val.json"
    GOLDEN_TEST = DATASET / "golden_test.json"
    TRAIN_DATA = DATASET / "train_data.json"

    results = load_json(INPUT)


    # BERT Validation을 위한 세트, 성능 평가를 위한 세트를 추출합니다.
    # 각 세트마다 리뷰 500개, 총 1000개의 리뷰를 사용합니다.
    val_set = []
    test_set = []


    # 도움이 되는 참고문헌을 찾지 못하여 Gemini를 참고하여 기준을 정했습니다.
    # 단일 카테고리(맛, 서비스) 리뷰 50%, 다수 카테고리 리뷰 25%,
    # 카테고리(맛, 서비스)를 찾지 못한 리뷰 25%입니다.
    ghost_pool = []
    complex_pool = []
    single_pool = defaultdict(list)
    
    for rev in results:
        labels = rev["labels"]
        
        # 카테고리가 없으면 ghost로 분류합니다.
        if not labels:
            ghost_pool.append(rev)
            continue

        # 카테고리가 여러 개 발견되면 complex로 분류합니다.
        if len(labels) > 1:
            complex_pool.append(rev)

        # 카테고리가 1개 발견되면 single로 분류합니다.
        elif len(labels) == 1:
            single_pool[labels[0]].append(rev)


    # 각 세트(500개)의 25%, 25%, 50% 값입니다.
    GHOST_TARGET = 125
    COMPLEX_TARGET = 125
    STRATIFIED_TARGET = 250
    
    val_ghosts = random.sample(ghost_pool, GHOST_TARGET)
    test_ghosts = random.sample(ghost_pool, GHOST_TARGET)

    val_complex = random.sample(complex_pool, COMPLEX_TARGET)
    test_complex = random.sample(complex_pool, COMPLEX_TARGET)


    # Stratified는 모집단의 비율에 맞춰 표본을 수집하는 방식입니다.
    # 예컨대 총 리뷰 중 '맛' 리뷰가 70%, '서비스' 리뷰가 30%라면, 
    # 표본을 수집할 때도 '맛' 리뷰를 70%, '서비스' 리뷰를 30% 수집합니다.
    total_single = 0
    for reviews in single_pool.values():
        total_single += len(reviews)
    
    aspect_sample_number = {}
    
    # 단일 카테고리 리뷰 중 각 카테고리의 비율을 계산합니다.
    for aspect, reviews in single_pool.items():
        ratio = len(reviews) / total_single

        # 비율을 참고하여 카테고리마다 수집할 리뷰 개수를 구합니다.
        # 너무 비율이 작은 경우 리뷰가 수집이 안 되어, 최소 개수를 10으로 고정합니다.
        aspect_sample_number[aspect] = max(5, int(ratio * STRATIFIED_TARGET))



    # 가장 많은 카테고리의 리뷰 수집 수를 줄여, 리뷰 수집 수를 TARGET으로 맞춥니다.
    remainder = STRATIFIED_TARGET - sum(aspect_sample_number.values())
    largest_aspect = max(aspect_sample_number, key=aspect_sample_number.get)
    aspect_sample_number[largest_aspect] += remainder

    val_stratified = []
    test_stratified = []
    for aspect, count in aspect_sample_number.items():
        # 단일 카테고리 리뷰에서 계산한 개수만큼 표본을 추출합니다.
        aspect_sample_val = random.sample(single_pool[aspect], count)
        val_stratified.extend(aspect_sample_val)

        aspect_sample_test = random.sample(single_pool[aspect], count)
        test_stratified.extend(aspect_sample_test)


    # 수집한 리뷰를 합쳐 Golden set을 구성합니다.
    golden_val = val_ghosts + val_complex + val_stratified
    golden_test = test_ghosts + test_complex + test_stratified

    # 라벨링할 때 거슬리지 않도록, 수집한 표본을 뒤섞습니다.
    random.shuffle(golden_val)
    random.shuffle(golden_test)


    # 사전을 통해 감정 점수를 얻은 데이터만 BERT 학습에 활용합니다.
    # Golden set에 포함된 리뷰는 학습에서 제외합니다.
    golden_set = golden_val + golden_test
    golden_ids = set(rev["rev_id"] for rev in golden_set)

    train_set = []
    for rev in results:
        # "labels"는 "맛_긍정", "서비스_부정" 등의 라벨로,
        # 해당 값이 존재하면 감정 점수를 얻은 리뷰입니다.
        if rev["labels"] and rev["rev_id"] not in golden_ids:
            train_set.append(rev)

    save_json(golden_val, GOLDEN_VAL)
    save_json(golden_test, GOLDEN_TEST)
    save_json(train_set, TRAIN_DATA)

    print("\n=== Golden Set Report ===")
    print(f"Validation : {len(golden_val)} samples saved.")
    print(f"Testing    : {len(golden_test)} samples saved.")
    print(f"Training   : {len(train_set)} samples saved.")

if __name__ == "__main__":
    main()