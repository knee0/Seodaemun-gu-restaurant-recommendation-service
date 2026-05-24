import json
from math import exp, log, log1p
from datetime import datetime, timezone
from src.utils import RAW_DATA, PREP, load_json, save_json

INPUT = RAW_DATA
OUTPUT = PREP / "metadata.json"

# 1년 전: 0.88, 2년 전: 0.59, 3년 전: 0.3, 최소: 0.1
RECENCY_PARAM = 1000
# LIMIT은 상위 95% 값. 최대 가중치 1.4
ACTIVITY_PARAM = 0.4
ACTIVITY_LIMIT = 1914
LOYALTY_PARAM = 0.1
LOYALTY_LIMIT = 5

def format_review_date(review_date):
    pieces = [p.strip() for p in review_date.split('.')]


def calculate_weight(visit_time, review_date_flag, review_count, visit_count):
    if review_date_flag:
        start_date = datetime.strptime(visit_time[:-2], "%y.%m.%d").replace(tzinfo=timezone.utc)
    else:
        start_date = datetime.strptime(visit_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

    target_date = datetime(2026, 5, 5, tzinfo=timezone.utc)
    days_diff = (target_date - start_date).days
    power = -((days_diff / RECENCY_PARAM) ** 2)
    
    recency = max(0.1, exp(power))

    capped_rc = min(review_count, ACTIVITY_LIMIT)
    activity = 1 + ACTIVITY_PARAM * (log(capped_rc) / log(ACTIVITY_LIMIT))

    capped_vc = min(visit_count, LOYALTY_LIMIT) - 1
    loyalty = 1 + LOYALTY_PARAM * capped_vc

    return recency * activity * loyalty

def make_metadata(data):
    dataset = {}

    # res_data에는 식당 이름과 카테고리(한식/일식 등),
    # rev_data에는 리뷰에 대한 정보(리뷰 ID, 방문 일자, 작성 리뷰 개수, 방문 횟수).
    # 전자는 웹페이지를 제작할 때, 후자는 식당 총점을 계산할 때 활용.
    for rid, restaurant in data.items():
        metadata = restaurant.get("metadata", {})

        res_data = {
            "name": metadata.get("name"),
            "category": metadata.get("category")
        }

        rev_datas = []
        for idx, review in enumerate(restaurant.get("reviews", [])):
            # preprocessed.py에서 만든 리뷰 ID와 같은 방식.
            rev_id = f"{rid}_{idx}"

            review_date_flag = False
            visit_time = review.get("visit_datetime")
            if not visit_time:
                visit_time = review.get("review_date")
                review_date_flag = True
            
            review_count = review.get("review_count")
            if not review_count:
                review_count = 1

            visit_count = review.get("visit_count")
            if not visit_count:
                visit_count = 1

            weight = calculate_weight(visit_time, review_date_flag, review_count, visit_count)

            rev_datas.append({
                "rev_id": rev_id,
                "visit_time": visit_time,
                "review_count": review_count,
                "visit_count": visit_count,
                "weight": weight
            })

        dataset[rid] = {
            "res_data": res_data,
            "rev_data": rev_datas
        }
                                
    return dataset

def main():
    data = load_json(INPUT)
    metadata = make_metadata(data)
    save_json(metadata, OUTPUT, 4)

if __name__ == "__main__":
    main()
