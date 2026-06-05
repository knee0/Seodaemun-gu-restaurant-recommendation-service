import re
import csv
from math import exp, log, log1p
from datetime import datetime, timezone
from src.utils import RAW, PREP, load_json, save_json

INPUT = RAW / "naver_reviews_deluxe.json"
OUTPUT = PREP / "metadata.json"
CSV_INPUT = RAW / "raw.csv"
URL_INPUT = RAW / "naver_thumbnail.json"


# 가중치 계산 관련 코드

# Recency: 오래된 리뷰의 영향력 감소.
RECENCY_PARAM = 1000
# 1000 기준, 1년 전: 0.88 / 2년 전: 0.59 / 3년 전: 0.3 / 최소: 0.1

# Activity: 작성한 리뷰가 많으면 영향력 증가.
# Loyalty: 식당 방문 횟수가 많으면 영향력 증가.
# 최대 영향력 1.2
# LIMIT은 상위 95% 값으로 설정 (scripts/metadata_dist 참조)
ACTIVITY_PARAM = 0.2
ACTIVITY_LIMIT = 1914
LOYALTY_PARAM = 0.05
LOYALTY_LIMIT = 5


def calculate_weight(visit_time, review_date_flag, review_count, visit_count):
    # 며칠 차이나는지 비교하기 위해 datetime 객체로 전환합니다.
    if review_date_flag:
        start_date = datetime.strptime(visit_time[:-2], "%y.%m.%d").replace(tzinfo=timezone.utc)
    else:
        start_date = datetime.strptime(visit_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

    # 수집된 리뷰 중 가장 최근 리뷰가 5월 5일 입니다.
    target_date = datetime(2026, 5, 5, tzinfo=timezone.utc)
    days_diff = (target_date - start_date).days
    power = -((days_diff / RECENCY_PARAM) ** 2)
    
    # 최소 영향력은 0.1로 설정합니다.
    recency = max(0.1, exp(power))

    # LIMIT 이상의 리뷰 작성 수는 LIMIT과 같도록 처리합니다. (최대 영향력 1.2로 제한)
    capped_rc = min(review_count, ACTIVITY_LIMIT)
    activity = 1 + ACTIVITY_PARAM * (log(capped_rc) / log(ACTIVITY_LIMIT))

    # LIMIT 이상의 식당 방문 수는 LIMIT과 같도록 처리합니다. (최대 영향력 1.2로 제한)
    capped_vc = min(visit_count, LOYALTY_LIMIT) - 1
    loyalty = 1 + LOYALTY_PARAM * capped_vc

    # 리뷰의 총 영향력(weight)을 리턴합니다.
    return recency * activity * loyalty



# 메타데이터 수집 및 정리 관련 코드
stopwords = ["카카오", "이벤트", "리뷰", "카드", "네이버"]

def clean_menu(text):
    for word in stopwords:
        if word in text:
            return

    text = re.sub(r"^\d+\s*\.?\s*", "", text)

    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"\([^)]*\)", "", text)

    text = re.sub(r"[^가-힣\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= 1: return

    return text

def load_address_mapping():
    address_map = {}

    with open(CSV_INPUT, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = row.get("사업장명")
            address = row.get("도로명전체주소")
            sub_address = row.get("소재지전체주소")
            if address:
                address_map[name.strip()] = address.strip()
            else:
                address_map[name.strip()] = sub_address.strip()

    return address_map

def load_url_mapping():
    info_map = {}
    info_list = load_json(URL_INPUT)
    
    for item in info_list:
        naver_id = item.get("naverID")
        if naver_id:
            info_map[naver_id] = item

    return info_map


def make_metadata(data, address_map, info_map):
    dataset = {}

    for rid, restaurant in data.items():
        # 케이크 주문제작 매장이 보여서 제외합니다.
        if rid == "1572782359":
            continue

        total_count += 1

        # 같은 식당 내 중복 제거.
        seen_raw = set()
        
        metadata = restaurant.get("metadata", {})
        franchise = restaurant.get("franchise_classification", {})
        time_period = restaurant.get("period_recommendation", {})
        
        all_menu = restaurant.get("all_menu", [])
        cleaned_menu = []
        for menu in all_menu:
            result = clean_menu(menu)
            if result is not None:
                cleaned_menu.append(result)

        res_name = metadata.get("name")

        url_info = info_map.get(rid, {})

        if res_name in address_map:
            matched_address = address_map[res_name]

        category_raw = metadata.get("category_raw")
        if category_raw == "아시안/세계요리":
            category_raw = "세계요리"
        elif category_raw == "카페/디저트":
            category_raw = "카페"
        elif category_raw == "술집/주점":
            category_raw = "주점"

        # 식당 이름, 카테고리(한식/일식 등), 프랜차이즈 여부, 점심/저녁 추천, 메뉴 목록
        res_data = {
            "name": res_name,
            "address": matched_address,
            "category": metadata.get("category"),
            "category_raw": category_raw,
            "franchise": franchise.get("is_franchise"),
            "time_period": time_period.get("label"),
            "all_menu": cleaned_menu,
            "naver_url": url_info.get("naver_url"),
            "thumbnail_url": url_info.get("thumbnail_url")
        }

        # 리뷰의 총 영향력.
        rev_datas = []
        for idx, review in enumerate(restaurant.get("reviews", [])):
            # preprocessed에서 만든 리뷰 ID와 같은 형식.
            rev_id = f"{rid}_{idx}"

            # visit_time 값이 없는 리뷰는 review_date 값으로 대체합니다.
            review_date_flag = False
            visit_time = review.get("visit_datetime")
            if not visit_time:
                visit_time = review.get("review_date")
                review_date_flag = True
            
            # review_count 값이 없으면 최솟값인 1로 처리합니다.
            review_count = review.get("review_count")
            if not review_count:
                review_count = 1

            # visit_count 값이 없으면 최솟값인 1로 처리합니다.
            visit_count = review.get("visit_count")
            if not visit_count:
                visit_count = 1

            weight = calculate_weight(visit_time, review_date_flag, review_count, visit_count)

            rev_datas.append({
                "rev_id": rev_id,
                "weight": weight
            })

        dataset[rid] = {
            "res_data": res_data,
            "rev_data": rev_datas
        }


    return dataset

def main():
    data = load_json(INPUT)
    address_map = load_address_mapping()
    info_map = load_url_mapping()
    metadata = make_metadata(data, address_map, info_map)
    save_json(metadata, OUTPUT)

if __name__ == "__main__":
    main()
