import argparse
import csv
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from franchise_common import load_json, normalize_name, parse_int, rows_from_json, write_json


RestaurantRecord = Dict[str, Any]
BrandRecord = Dict[str, Any]
PERIOD_LUNCH = "점심"
PERIOD_DINNER = "저녁"
PERIOD_NONE = "점심/저녁 추천 없음"
KST = timezone(timedelta(hours=9))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="네이버 음식점 리뷰 JSON을 프랜차이즈/비프랜차이즈로 분리합니다."
    )
    parser.add_argument(
        "--reviews",
        type=Path,
        default=Path("data") / "naver_reviews.json",
        help="네이버 리뷰 JSON 경로",
    )
    parser.add_argument(
        "--brands",
        type=Path,
        required=True,
        help="프랜차이즈 브랜드 통계 JSON 경로",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="네이버 리뷰 JSON 파일 인코딩",
    )
    parser.add_argument(
        "--min-brand-chars",
        type=int,
        default=3,
        help="부분 매칭에 사용할 최소 브랜드명 길이",
    )
    parser.add_argument(
        "--min-franchise-outlets",
        type=int,
        default=5,
        help="프랜차이즈로 분류할 최소 전국 가맹점 수",
    )
    parser.add_argument(
        "--franchise-output",
        type=Path,
        default=Path("results") / "naver_reviews_franchise.json",
    )
    parser.add_argument(
        "--independent-output",
        type=Path,
        default=Path("results") / "naver_reviews_independent.json",
    )
    parser.add_argument(
        "--combined-output",
        type=Path,
        default=Path("results") / "naver_reviews_all.json",
        help="프랜차이즈와 비프랜차이즈를 합친 전체 JSON 저장 경로",
    )
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=Path("results") / "naver_restaurant_classification.csv",
    )
    return parser.parse_args()


def build_brand_index(
    brands: Iterable[BrandRecord],
    min_brand_chars: int,
    min_franchise_outlets: int = 0,
) -> List[Tuple[str, BrandRecord]]:
    index = []
    seen = set()
    for brand in brands:
        brand_name = brand.get("brandNm")
        normalized = normalize_name(brand_name)
        if len(normalized) < min_brand_chars:
            continue
        if parse_int(brand.get("frcsCnt")) < min_franchise_outlets:
            continue
        key = (normalized, str(brand.get("brandMnno") or brand.get("corpNm") or ""))
        if key in seen:
            continue
        seen.add(key)
        index.append((normalized, brand))
    index.sort(key=lambda item: len(item[0]), reverse=True)
    return index


def get_restaurant_name(record: RestaurantRecord) -> str:
    metadata = record.get("metadata") or {}
    return str(
        metadata.get("name")
        or record.get("name")
        or record.get("restaurant_name")
        or record.get("place_name")
        or ""
    )


def get_review_count(record: RestaurantRecord) -> int:
    reviews = record.get("reviews")
    if isinstance(reviews, list):
        return len(reviews)
    metadata = record.get("metadata") or {}
    value = metadata.get("collected_count")
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def value_contains_keyword(value: Any, keyword: str) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return any(value_contains_keyword(item, keyword) for item in value)
    return keyword in str(value)


def count_keyword_occurrences(value: Any, keyword: str) -> int:
    if value is None:
        return 0
    if isinstance(value, list):
        return sum(count_keyword_occurrences(item, keyword) for item in value)
    return str(value).count(keyword)


def get_visit_minutes_kst(value: Any) -> Optional[int]:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.hour * 60 + parsed.minute
    kst_datetime = parsed.astimezone(KST)
    return kst_datetime.hour * 60 + kst_datetime.minute


def get_visit_hour_kst(value: Any) -> Optional[int]:
    minutes = get_visit_minutes_kst(value)
    if minutes is None:
        return None
    return minutes // 60


def is_lunch_time_kst(minutes: Optional[int]) -> bool:
    return minutes is not None and 11 * 60 + 30 <= minutes <= 14 * 60


def is_dinner_time_kst(minutes: Optional[int]) -> bool:
    return minutes is not None and 17 * 60 + 30 <= minutes <= 20 * 60


def get_period_recommendation(record: RestaurantRecord) -> Dict[str, Any]:
    lunch_keyword_matches = 0
    dinner_keyword_matches = 0
    lunch_time_matches = 0
    dinner_time_matches = 0
    reviews = record.get("reviews")

    if isinstance(reviews, list):
        for review in reviews:
            if not isinstance(review, dict):
                continue
            searchable_values = [review.get("content"), review.get("menu")]
            lunch_keyword_matches += sum(
                count_keyword_occurrences(value, PERIOD_LUNCH)
                for value in searchable_values
            )
            dinner_keyword_matches += sum(
                count_keyword_occurrences(value, PERIOD_DINNER)
                for value in searchable_values
            )

            visit_minutes_kst = get_visit_minutes_kst(review.get("visit_datetime"))
            has_lunch_time = is_lunch_time_kst(visit_minutes_kst)
            has_dinner_time = is_dinner_time_kst(visit_minutes_kst)
            if has_lunch_time:
                lunch_time_matches += 1
            if has_dinner_time:
                dinner_time_matches += 1

    time_match_gap = abs(lunch_time_matches - dinner_time_matches)
    label_selection_reason = "no_period_match"
    if time_match_gap >= 5 and lunch_time_matches > dinner_time_matches:
        label = PERIOD_LUNCH
        label_selection_reason = "time_gap_5_more_lunch"
    elif time_match_gap >= 5 and dinner_time_matches > lunch_time_matches:
        label = PERIOD_DINNER
        label_selection_reason = "time_gap_5_more_dinner"
    elif lunch_keyword_matches > dinner_keyword_matches:
        label = PERIOD_LUNCH
        label_selection_reason = "time_gap_below_5_keyword_lunch"
    elif dinner_keyword_matches > lunch_keyword_matches:
        label = PERIOD_DINNER
        label_selection_reason = "time_gap_below_5_keyword_dinner"
    elif lunch_keyword_matches or dinner_keyword_matches:
        label = PERIOD_NONE
        label_selection_reason = "time_gap_below_5_keyword_tie"
    else:
        label = PERIOD_NONE
        label_selection_reason = "time_gap_below_5_no_keyword"

    return {
        "label": label,
        "label_selection_reason": label_selection_reason,
        "is_lunch_recommended": label == PERIOD_LUNCH,
        "is_dinner_recommended": label == PERIOD_DINNER,
        "lunch_keyword_match_count": lunch_keyword_matches,
        "dinner_keyword_match_count": dinner_keyword_matches,
        "lunch_visit_time_match_count": lunch_time_matches,
        "dinner_visit_time_match_count": dinner_time_matches,
        "time_match_gap": time_match_gap,
    }


def match_brand(
    restaurant_name: str, brand_index: List[Tuple[str, BrandRecord]]
) -> Tuple[Optional[BrandRecord], str]:
    normalized_restaurant = normalize_name(restaurant_name)
    if not normalized_restaurant:
        return None, "missing_restaurant_name"

    for normalized_brand, brand in brand_index:
        if normalized_restaurant == normalized_brand:
            return brand, "exact"
        if normalized_restaurant.startswith(normalized_brand):
            return brand, "prefix"
        if normalized_brand in normalized_restaurant:
            return brand, "contains"

    return None, "no_match"


def iter_restaurants(data: Any) -> Iterable[Tuple[str, RestaurantRecord]]:
    if isinstance(data, dict):
        for restaurant_id, record in data.items():
            if isinstance(record, dict):
                yield str(restaurant_id), record
    elif isinstance(data, list):
        for index, record in enumerate(data):
            if isinstance(record, dict):
                restaurant_id = record.get("restaurant_id") or record.get("id") or index
                yield str(restaurant_id), record


def add_classification(
    record: RestaurantRecord,
    matched_brand: Optional[BrandRecord],
    match_type: str,
    min_franchise_outlets: int,
) -> RestaurantRecord:
    updated = copy.deepcopy(record)
    classification = {
        "is_franchise": matched_brand is not None,
        "label": "프랜차이즈" if matched_brand else "일반",
        "match_type": match_type,
        "min_franchise_outlets": min_franchise_outlets,
        "matched_brand_name": None,
        "matched_corp_name": None,
        "matched_brand_mnno": None,
        "matched_headquarter_mnno": None,
        "matched_industry_major": None,
        "matched_industry_middle": None,
        "franchise_outlet_count": 0,
    }
    if matched_brand:
        classification.update(
            {
                "matched_brand_name": matched_brand.get("brandNm"),
                "matched_corp_name": matched_brand.get("corpNm"),
                "matched_brand_mnno": matched_brand.get("brandMnno"),
                "matched_headquarter_mnno": matched_brand.get("jnghdqrtrsMnno"),
                "matched_industry_major": matched_brand.get("indutyLclasNm"),
                "matched_industry_middle": matched_brand.get("indutyMlsfcNm"),
                "franchise_outlet_count": parse_int(matched_brand.get("frcsCnt")),
            }
        )
    updated["franchise_classification"] = classification
    updated["period_recommendation"] = get_period_recommendation(updated)
    return updated


def write_summary_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "restaurant_id",
        "restaurant_name",
        "classification",
        "period_recommendation",
        "period_label_selection_reason",
        "is_lunch_recommended",
        "is_dinner_recommended",
        "lunch_keyword_match_count",
        "dinner_keyword_match_count",
        "lunch_visit_time_match_count",
        "dinner_visit_time_match_count",
        "time_match_gap",
        "is_franchise",
        "match_type",
        "matched_brand_name",
        "matched_corp_name",
        "matched_brand_mnno",
        "franchise_outlet_count",
        "min_franchise_outlets",
        "review_count",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    reviews_data = load_json(args.reviews, encoding=args.encoding)
    brand_rows = rows_from_json(load_json(args.brands))
    if args.min_franchise_outlets > 0 and not any("frcsCnt" in row for row in brand_rows):
        raise SystemExit(
            "--min-franchise-outlets 기준을 쓰려면 frcsCnt가 있는 브랜드 통계 JSON이 필요합니다. "
            "먼저 fetch_franchise_brand_stats.py를 실행해 주세요."
        )

    brand_index = build_brand_index(
        brand_rows,
        args.min_brand_chars,
        min_franchise_outlets=args.min_franchise_outlets,
    )

    franchise_records: Dict[str, RestaurantRecord] = {}
    independent_records: Dict[str, RestaurantRecord] = {}
    combined_records: Dict[str, RestaurantRecord] = {}
    summary_rows: List[Dict[str, Any]] = []

    for restaurant_id, record in iter_restaurants(reviews_data):
        restaurant_name = get_restaurant_name(record)
        matched_brand, match_type = match_brand(restaurant_name, brand_index)
        classified = add_classification(
            record,
            matched_brand,
            match_type,
            args.min_franchise_outlets,
        )

        if matched_brand:
            franchise_records[restaurant_id] = classified
        else:
            independent_records[restaurant_id] = classified
        combined_records[restaurant_id] = classified

        classification = classified["franchise_classification"]
        period_recommendation = classified["period_recommendation"]
        summary_rows.append(
            {
                "restaurant_id": restaurant_id,
                "restaurant_name": restaurant_name,
                "classification": classification["label"],
                "period_recommendation": period_recommendation["label"],
                "period_label_selection_reason": period_recommendation[
                    "label_selection_reason"
                ],
                "is_lunch_recommended": period_recommendation["is_lunch_recommended"],
                "is_dinner_recommended": period_recommendation["is_dinner_recommended"],
                "lunch_keyword_match_count": period_recommendation[
                    "lunch_keyword_match_count"
                ],
                "dinner_keyword_match_count": period_recommendation[
                    "dinner_keyword_match_count"
                ],
                "lunch_visit_time_match_count": period_recommendation[
                    "lunch_visit_time_match_count"
                ],
                "dinner_visit_time_match_count": period_recommendation[
                    "dinner_visit_time_match_count"
                ],
                "time_match_gap": period_recommendation["time_match_gap"],
                "is_franchise": classification["is_franchise"],
                "match_type": match_type,
                "matched_brand_name": classification["matched_brand_name"],
                "matched_corp_name": classification["matched_corp_name"],
                "matched_brand_mnno": classification["matched_brand_mnno"],
                "franchise_outlet_count": classification["franchise_outlet_count"],
                "min_franchise_outlets": classification["min_franchise_outlets"],
                "review_count": get_review_count(record),
            }
        )

    write_json(args.franchise_output, franchise_records)
    write_json(args.independent_output, independent_records)
    write_json(args.combined_output, combined_records)
    write_summary_csv(args.summary_csv, summary_rows)

    print("프랜차이즈 음식점: %s건 -> %s" % (len(franchise_records), args.franchise_output))
    print("비프랜차이즈 음식점: %s건 -> %s" % (len(independent_records), args.independent_output))
    print("통합 음식점: %s건 -> %s" % (len(combined_records), args.combined_output))
    print("분류 요약 CSV -> %s" % args.summary_csv)


if __name__ == "__main__":
    main()
