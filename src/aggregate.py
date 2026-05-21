import argparse
import json
import math
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import DATA_DIR, INTERIM, RAW_DATA


# BERT/사전 기반 점수가 섞여 들어올 수 있으므로 최종 집계에서 사용할 표준 카테고리명으로 맞춰주기.
CANONICAL_ASPECTS = ["맛", "서비스", "분위기", "가격", "시스템"]
DEFAULT_CUISINE = "기타"

# 이전 prototype의 영문 aspect명이나 유사 표현을 현재 프로젝트의 한글 aspect명으로 통일.
ASPECT_ALIASES = {
    "맛": "맛",
    "Taste": "맛",
    "taste": "맛",
    "서비스": "서비스",
    "Service": "서비스",
    "service": "서비스",
    "분위기": "분위기",
    "Mood": "분위기",
    "Atmosphere": "분위기",
    "mood": "분위기",
    "atmosphere": "분위기",
    "가격": "가격",
    "Price": "가격",
    "Value": "가격",
    "Amount": "가격",
    "price": "가격",
    "value": "가격",
    "amount": "가격",
    "양": "가격",
    "가성비": "가격",
    "시스템": "시스템",
    "System": "시스템",
    "system": "시스템",
    "편의": "시스템",
    "대기": "시스템",
}

# 업종별 가중치는 학습값이 아니라 느낌있게(?) 주기. 나중에 유저가 조정할 수 있게 수정해볼게요!
# 예: 카페는 분위기, 분식은 가격/회전, 주점은 분위기/서비스 비중을 조금 더 주기.
# 특정 aspect가 비어 있으면 실제 점수 계산 시 남은 aspect끼리 다시 정규화.

# TODO : 나중에 유저가 조절할 수 있게 바꾸기.
CUISINE_WEIGHTS = {
    DEFAULT_CUISINE: {"맛": 0.40, "서비스": 0.18, "분위기": 0.15, "가격": 0.15, "시스템": 0.12},
    "한식": {"맛": 0.42, "가격": 0.18, "서비스": 0.15, "시스템": 0.13, "분위기": 0.12},
    "중식": {"맛": 0.45, "시스템": 0.17, "가격": 0.15, "서비스": 0.13, "분위기": 0.10},
    "일식": {"맛": 0.44, "시스템": 0.17, "서비스": 0.16, "가격": 0.13, "분위기": 0.10},
    "양식": {"맛": 0.38, "분위기": 0.22, "서비스": 0.17, "가격": 0.13, "시스템": 0.10},
    "카페/디저트": {"맛": 0.34, "분위기": 0.26, "서비스": 0.15, "가격": 0.13, "시스템": 0.12},
    "분식/패스트푸드": {"맛": 0.35, "가격": 0.24, "시스템": 0.18, "서비스": 0.13, "분위기": 0.10},
    "분식/간편식": {"맛": 0.35, "가격": 0.24, "시스템": 0.18, "서비스": 0.13, "분위기": 0.10},
    "주점": {"맛": 0.32, "분위기": 0.24, "서비스": 0.18, "시스템": 0.14, "가격": 0.12},
    "술집/주점": {"맛": 0.32, "분위기": 0.24, "서비스": 0.18, "시스템": 0.14, "가격": 0.12},
    "아시안/세계요리": {"맛": 0.40, "분위기": 0.18, "서비스": 0.16, "가격": 0.13, "시스템": 0.13},
    "세계요리": {"맛": 0.40, "분위기": 0.18, "서비스": 0.16, "가격": 0.13, "시스템": 0.13},
}

# 웹페이지에서 탭/섹션으로 보여줄 랭킹 카테고리 목록.
# raw 데이터의 category를 최대한 그대로 살려 다이닝코드처럼 업종별 순위를 만들기 위해 사용.
RANKING_CATEGORIES = [
    "한식",
    "중식",
    "일식",
    "양식",
    "분식/간편식",
    "카페/디저트",
    "술집/주점",
    "아시안/세계요리",
    "세계요리",
]

# 모델/키워드 추정 과정에서 생긴 내부 업종명을 실제 노출 카테고리명으로 맞추기.
RANKING_CATEGORY_MAP = {
    "한식": "한식",
    "중식": "중식",
    "일식": "일식",
    "양식": "양식",
    "아시안/세계요리": "아시안/세계요리",
    "세계요리": "세계요리",
    "분식/패스트푸드": "분식/간편식",
    "분식/간편식": "분식/간편식",
    "카페/디저트": "카페/디저트",
    "주점": "술집/주점",
    "술집/주점": "술집/주점",
}

# raw metadata.category가 없거나 비어 있을 때 식당명/카테고리 텍스트에서 업종을 추정하기 위한 키워드.
CUISINE_KEYWORDS = {
    "카페/디저트": [
        "카페", "커피", "디저트", "베이커리", "빵", "케이크", "빙수", "베이글",
        "도넛", "아이스크림", "브런치카페",
    ],
    "주점": [
        "술집", "주점", "호프", "펍", "pub", "bar", "와인바", "맥주", "칵테일",
        "칵테일바", "이자카야",
    ],
    "분식/패스트푸드": [
        "분식", "간편식", "떡볶이", "김밥", "라면", "토스트", "샌드위치", "햄버거",
        "버거", "치킨", "패스트푸드",
    ],
    "한식": [
        "한식", "백반", "국밥", "찌개", "전골", "고기", "삼겹살", "보쌈",
        "족발", "감자탕", "닭갈비", "칼국수", "수제비", "냉면", "갈비",
        "곱창", "막창", "해장국",
    ],
    "중식": [
        "중식", "중국", "중화", "짜장", "자장", "짬뽕", "탕수육", "마라",
        "양꼬치", "딤섬", "도삭면", "훠궈", "소룡포",
    ],
    "일식": [
        "일식", "일본", "초밥", "스시", "라멘", "라멘집", "돈까스", "돈가스",
        "카레", "우동", "사시미", "횟집", "회전초밥", "덮밥", "규동", "오마카세",
    ],
    "양식": [
        "양식", "파스타", "피자", "스테이크", "리조또", "이탈리아", "프렌치",
        "프랑스", "멕시코", "타코", "퀘사디아", "샐러드", "브런치",
    ],
    "아시안/세계요리": [
        "아시안", "세계요리", "쌀국수", "베트남", "태국", "타이", "인도",
        "커리", "마라탕", "마라샹궈",
    ],
}

# 결과 JSON에 남겨 발표에서 "왜 이 업종은 이 가중치인가"를 설명할 때 사용.
WEIGHT_REASONS = {
    DEFAULT_CUISINE: "업종을 특정하기 어려워 맛을 중심으로 서비스, 분위기, 가격, 시스템을 균형 반영",
    "한식": "일상 식사 비중이 커 맛과 가성비를 높게 보고, 회전/대기 같은 시스템을 보조 반영",
    "중식": "메뉴 맛과 조리 일관성이 핵심이고, 배달/회전/대기 경험이 만족도에 크게 작용",
    "일식": "맛과 신선도, 제공 순서/대기/좌석 같은 운영 안정성이 선택 기준에 중요",
    "양식": "데이트와 모임 수요가 많아 맛 다음으로 분위기와 서비스 경험의 비중을 확대",
    "카페/디저트": "음료/디저트 품질과 함께 체류 분위기가 방문 목적에 직접 연결",
    "분식/패스트푸드": "가성비와 빠른 제공/회전이 만족도에 크게 영향을 주는 업종",
    "분식/간편식": "가성비와 빠른 제공/회전이 만족도에 크게 영향을 주는 업종",
    "주점": "음식뿐 아니라 분위기, 응대, 좌석/대기 같은 이용 경험이 재방문에 중요",
    "술집/주점": "음식뿐 아니라 분위기, 응대, 좌석/대기 같은 이용 경험이 재방문에 중요",
    "아시안/세계요리": "이색 메뉴의 맛과 함께 동행/모임 경험을 좌우하는 분위기와 서비스도 반영",
    "세계요리": "이색 메뉴의 맛과 함께 동행/모임 경험을 좌우하는 분위기와 서비스도 반영",
}

# 크롤러 버전이나 데이터 소스마다 키 이름이 조금씩 달라질 수 있어 후보 키를 여러 개 두기.
VISITOR_REVIEW_KEYS = [
    "visitor_review_count", "visitor_reviews", "visitorReviewCount", "visitorReview",
    "방문자 리뷰 수", "방문자리뷰", "방문자 리뷰",
]
BLOG_REVIEW_KEYS = [
    "blog_review_count", "blog_reviews", "blogReviewCount", "blogReview",
    "블로그 리뷰 수", "블로그리뷰", "블로그 리뷰",
]
RATING_KEYS = [
    "rating", "star_rating", "starRating", "naver_rating", "naverRating",
    "별점", "평점",
]
REVIEW_DATE_KEYS = [
    "date", "created_at", "createdAt", "created", "write_date", "writeDate",
    "written_at", "writtenAt", "visited_at", "visitedAt", "visit_datetime",
    "visitDatetime", "visit_date", "visitDate", "review_date", "reviewDate",
    "작성일", "방문일", "리뷰 작성일",
]
REVIEWER_REVIEW_COUNT_KEYS = [
    "review_count", "reviewCount",
    "author_review_count", "authorReviewCount", "reviewer_review_count",
    "reviewerReviewCount", "user_review_count", "userReviewCount",
    "writer_review_count", "writerReviewCount", "author.reviews",
    "author.review_count", "user.reviews", "user.review_count",
    "작성자 리뷰 수", "리뷰어 리뷰 수", "작성한 리뷰", "리뷰 수",
]
CATEGORY_KEYS = [
    "category", "category_name", "categoryName", "business_category",
    "업종", "카테고리", "분류",
]
NAME_KEYS = ["name", "restaurant_name", "place_name", "상호명", "가게명"]

# 최종 추천 점수는 감정 점수를 가장 크게 보고, 인기도/별점은 보조 신호로만 반영.
SENTIMENT_WEIGHT = 0.78
POPULARITY_WEIGHT = 0.12
RATING_WEIGHT = 0.10
MIN_REVIEWS_FOR_CONFIDENCE = 20

# 리뷰별 신뢰도 가중치 설정값.
# 최신 리뷰는 크게 반영하고, 작성자 리뷰 수는 로그 스케일로 작게만 보정.
RECENCY_HALF_LIFE_DAYS = 365
MIN_RECENCY_WEIGHT = 0.55
MAX_REVIEWER_ACTIVITY_BOOST = 0.25
REVIEWER_ACTIVITY_CAP = 100
MIN_REVIEW_WEIGHT = 0.45
MAX_REVIEW_WEIGHT = 1.45


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_scores(scores, output_path=None):
    output_path = Path(output_path or DATA_DIR / "final" / "restaurant_scores.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


def save_category_rankings(rankings, output_path=None):
    output_path = Path(output_path or DATA_DIR / "final" / "category_rankings.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)


def _normalize_key(key):
    # 공백/구분기호/대소문자 차이 때문에 같은 메타데이터 키를 놓치지 않도록 정규화.
    return re.sub(r"[\s_\-().]", "", str(key).lower())


def _metadata(raw_restaurant):
    # 식당 metadata가 루트와 metadata 하위에 나뉘어 있어도 한 dict처럼 읽을 수 있게 합치기.
    if not isinstance(raw_restaurant, dict):
        return {}

    result = {k: v for k, v in raw_restaurant.items() if k not in {"reviews", "metadata"}}
    nested = raw_restaurant.get("metadata", {})
    if isinstance(nested, dict):
        result.update(nested)
    return result


def _flatten_items(data, prefix=""):
    # author.review_count 같은 중첩 키도 _first_value에서 찾을 수 있도록 펼치고,
    if not isinstance(data, dict):
        return

    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        yield full_key, value
        if isinstance(value, dict):
            yield from _flatten_items(value, full_key)


def _first_value(data, keys):
    # 후보 키 목록 중 데이터에 실제 존재하는 첫 값을 찾아 반환.
    if not isinstance(data, dict):
        return None

    lookup = {_normalize_key(k): v for k, v in _flatten_items(data)}
    for key in keys:
        value = lookup.get(_normalize_key(key))
        if value is not None:
            return value

    for key in keys:
        target = _normalize_key(key)
        for data_key, value in lookup.items():
            if target and target in data_key:
                return value
    return None


def _parse_reference_date(value=None):
    # 테스트/재현성을 위해 기준일을 주입할 수 있고, 없으면 실행일을 기준으로 삼음.
    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _stringify(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(_stringify(v) for v in value)
    if isinstance(value, dict):
        return " ".join(_stringify(v) for v in value.values())
    return str(value)


def _extract_count(value):
    # "1,234", "1.2만", "3천" 같은 네이버식 숫자 표기를 정수로 바꾸기.
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).replace(",", "").strip()
    ten_thousand = re.search(r"(\d+(?:\.\d+)?)\s*만", text)
    if ten_thousand:
        return int(float(ten_thousand.group(1)) * 10000)

    thousand = re.search(r"(\d+(?:\.\d+)?)\s*천", text)
    if thousand:
        return int(float(thousand.group(1)) * 1000)

    match = re.search(r"\d+(?:\.\d+)?", text)
    return int(float(match.group(0))) if match else None


def _extract_rating(value):
    # 별점은 0~1 범위로 정규화해서 최종 점수 계산에 섞기 쉽게 만들기.
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        rating = float(value)
    else:
        numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", str(value).replace(",", ""))]
        valid_numbers = [n for n in numbers if 0 <= n <= 5]
        if not valid_numbers:
            return None
        rating = valid_numbers[-1]

    if 0 <= rating <= 5:
        return rating / 5
    if 0 <= rating <= 100:
        return rating / 100
    return None


def _extract_date(value, reference_date=None):
    # ISO 날짜, "3.18.수", "2주 전" 같은 리뷰 날짜 표기를 최대한 날짜 객체로 바꾸기.
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    today = _parse_reference_date(reference_date)
    text = str(value).strip()
    if not text:
        return None

    relative_patterns = [
        (r"(\d+)\s*일\s*전", 1),
        (r"(\d+)\s*주\s*전", 7),
        (r"(\d+)\s*개월\s*전", 30),
        (r"(\d+)\s*달\s*전", 30),
        (r"(\d+)\s*년\s*전", 365),
    ]
    if "오늘" in text or "방금" in text:
        return today
    if "어제" in text:
        return today - timedelta(days=1)

    for pattern, days in relative_patterns:
        match = re.search(pattern, text)
        if match:
            return today - timedelta(days=int(match.group(1)) * days)

    normalized = text.replace("년", "-").replace("월", "-").replace("일", "")
    normalized = normalized.replace(".", "-").replace("/", "-")
    match = re.search(r"(\d{2,4})-(\d{1,2})-(\d{1,2})", normalized)
    if not match:
        return None

    year = int(match.group(1))
    if year < 100:
        year += 2000
    month = int(match.group(2))
    day = int(match.group(3))

    try:
        return date(year, month, day)
    except ValueError:
        return None


def _recency_weight(review_date, reference_date=None):
    # 오래된 리뷰의 영향력을 급격히 0으로 만들지 않고 반감기 방식으로 완만하게 낮춤.
    if review_date is None:
        return 1.0

    today = _parse_reference_date(reference_date)
    age_days = max((today - review_date).days, 0)
    decay = math.exp(-age_days / RECENCY_HALF_LIFE_DAYS)
    return MIN_RECENCY_WEIGHT + (1 - MIN_RECENCY_WEIGHT) * decay


def _reviewer_activity_weight(review_count):
    # 리뷰를 많이 쓴 작성자는 약간 더 신뢰하되, 로그 스케일과 상한으로 과한 영향력을 막음.
    if review_count is None or review_count <= 0:
        return 1.0

    activity = min(math.log1p(review_count) / math.log1p(REVIEWER_ACTIVITY_CAP), 1.0)
    return 1.0 + MAX_REVIEWER_ACTIVITY_BOOST * activity


def _review_weight(metadata, reference_date=None):
    # 리뷰 1개의 최종 가중치 = 최근성 가중치 * 작성자 활동 가중치.
    metadata = metadata or {}
    review_date = _extract_date(_first_value(metadata, REVIEW_DATE_KEYS), reference_date)
    reviewer_review_count = _extract_count(_first_value(metadata, REVIEWER_REVIEW_COUNT_KEYS))

    recency = _recency_weight(review_date, reference_date)
    reviewer_activity = _reviewer_activity_weight(reviewer_review_count)
    weight = max(MIN_REVIEW_WEIGHT, min(MAX_REVIEW_WEIGHT, recency * reviewer_activity))

    return {
        "weight": weight,
        "review_date": review_date.isoformat() if review_date else None,
        "reviewer_review_count": reviewer_review_count,
        "components": {
            "recency": recency,
            "reviewer_activity": reviewer_activity,
        },
    }


def _normalize_score(value):
    # 사전 점수(-1~1)와 BERT 확률(0~1)이 모두 들어올 수 있어 최종 범위를 0~1로 통일.
    if value is None or isinstance(value, bool):
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None

    if score < 0:
        score = (score + 1) / 2
    return max(0.0, min(1.0, score))


def _canonical_aspect_scores(aspect_scores):
    # aspect 이름을 표준화하고, 같은 aspect로 매핑된 값이 여러 개면 평균을 냄.
    buckets = defaultdict(list)
    for aspect, value in (aspect_scores or {}).items():
        canonical = ASPECT_ALIASES.get(aspect)
        score = _normalize_score(value)
        if canonical in CANONICAL_ASPECTS and score is not None:
            buckets[canonical].append(score)

    return {aspect: mean(scores) for aspect, scores in buckets.items()}


def _weighted_average(values):
    # None 값은 제외하고 남은 점수만 가중 평균.
    valid = [(score, weight) for score, weight in values if score is not None and weight > 0]
    weight_sum = sum(weight for _, weight in valid)
    if not valid or weight_sum <= 0:
        return None
    return sum(score * weight for score, weight in valid) / weight_sum


def _aspect_total(aspect_scores, weights):
    # 업종별 aspect 가중치를 적용해 식당의 감정 기반 기본 점수를 만들기.
    canonical_scores = _canonical_aspect_scores(aspect_scores)
    values = [(canonical_scores.get(aspect), weights.get(aspect, 0.0)) for aspect in CANONICAL_ASPECTS]
    return _weighted_average(values) or 0.5


def aggregate_review_aspect_scores(review_items, reference_date=None):
    # 같은 식당의 리뷰들을 리뷰별 가중치로 묶어 식당 단위 aspect 점수로 집계.
    aspect_values = defaultdict(list)
    weighted_reviews = []
    weights = []

    for item in review_items or []:
        aspect_scores = item.get("aspect_scores") or item.get("analysis") or {}
        canonical_scores = _canonical_aspect_scores(aspect_scores)
        weight_info = _review_weight(item.get("metadata", {}), reference_date)
        review_weight = weight_info["weight"]

        # aspect별로 (점수, 리뷰 가중치)를 모아 나중에 가중 평균내기.
        for aspect, score in canonical_scores.items():
            aspect_values[aspect].append((score, review_weight))

        weights.append(review_weight)
        # 디버깅/시각화를 위해 각 리뷰에 실제 적용된 가중치와 구성 요소를 남기기.
        weighted_reviews.append({
            **item,
            "aspect_scores": {aspect: round(score, 3) for aspect, score in canonical_scores.items()},
            "review_weight": round(review_weight, 3),
            "weight_components": {
                "review_date": weight_info["review_date"],
                "reviewer_review_count": weight_info["reviewer_review_count"],
                "recency": round(weight_info["components"]["recency"], 3),
                "reviewer_activity": round(weight_info["components"]["reviewer_activity"], 3),
            },
        })

    aspect_scores = {
        aspect: round(_weighted_average(values), 3)
        for aspect, values in aspect_values.items()
        if values
    }
    weight_summary = {
        "min": round(min(weights), 3) if weights else None,
        "max": round(max(weights), 3) if weights else None,
        "avg": round(mean(weights), 3) if weights else None,
        "sum": round(sum(weights), 3) if weights else 0,
    }

    return aspect_scores, weighted_reviews, weight_summary


def _split_rev_id(rev_id):
    # "식당ID_리뷰인덱스" 형식의 rev_id에서 식당 ID와 원본 리뷰 번호를 분리.
    if not rev_id:
        return "", None

    text = str(rev_id)
    if "_" not in text:
        return text, None

    rid, idx_text = text.rsplit("_", 1)
    try:
        return rid, int(idx_text)
    except ValueError:
        return rid, None


def _get_raw_review(raw_data, rid, review_idx):
    # rev_id의 리뷰 번호를 이용해 raw 데이터의 리뷰 메타데이터를 다시 찾아오고,
    reviews = raw_data.get(rid, {}).get("reviews", []) if isinstance(raw_data, dict) else []
    if review_idx is not None and 0 <= review_idx < len(reviews):
        review = reviews[review_idx]
        return review if isinstance(review, dict) else {"content": str(review)}
    return {}


def build_restaurant_results_from_aspect_rows(aspect_rows, raw_data=None, reference_date=None):
    # aspect_scores.json처럼 문장/절 단위로 저장된 결과를 식당 단위 입력으로 변환.
    raw_data = raw_data or {}
    review_buckets = defaultdict(lambda: defaultdict(lambda: {
        "aspect_scores": defaultdict(list),
        "sentences": [],
        "review_idx": None,
    }))

    for row in aspect_rows or []:
        rev_id = row.get("rev_id")
        rid, review_idx = _split_rev_id(rev_id)
        if not rid:
            continue
        # raw 데이터가 제공된 경우, 버전이 맞지 않는 식당 ID는 최종 결과에서 제외.
        if raw_data and rid not in raw_data:
            continue

        raw_aspect_scores = row.get("aspect_score") or row.get("aspect_scores") or row.get("analysis") or {}
        canonical_scores = _canonical_aspect_scores(raw_aspect_scores)
        bucket = review_buckets[rid][str(rev_id)]
        bucket["review_idx"] = review_idx

        for aspect, score in canonical_scores.items():
            bucket["aspect_scores"][aspect].append(score)

        # BERT/사전 결과가 문장 단위이므로, 같은 rev_id 아래에 문장들을 모아 두기.
        bucket["sentences"].append({
            "rev_id": rev_id,
            "review": row.get("raw", ""),
            "analysis": raw_aspect_scores,
        })

    restaurant_results = {}
    for rid, reviews in review_buckets.items():
        review_items = []
        for rev_id, review_info in reviews.items():
            raw_review = _get_raw_review(raw_data, rid, review_info["review_idx"])
            review_text = raw_review.get("content", "")
            if not review_text:
                review_text = " ".join(sentence["review"] for sentence in review_info["sentences"]).strip()

            # 한 리뷰가 여러 문장으로 쪼개졌으면, 리뷰 내부에서는 단순 평균으로 리뷰 점수를 만들기.
            review_aspect_scores = {
                aspect: round(mean(scores), 3)
                for aspect, scores in review_info["aspect_scores"].items()
                if scores
            }
            review_items.append({
                "rev_id": rev_id,
                "review": review_text,
                "aspect_scores": review_aspect_scores,
                "metadata": raw_review,
                "sentences": review_info["sentences"],
            })

        aspect_scores, weighted_reviews, review_weight_summary = aggregate_review_aspect_scores(
            review_items,
            reference_date,
        )
        raw_restaurant = raw_data.get(rid, {}) if isinstance(raw_data, dict) else {}
        name = _metadata(raw_restaurant).get("name", rid)
        sentence_count = sum(len(review["sentences"]) for review in review_items)

        restaurant_results[rid] = {
            "name": name,
            "review_count": len(review_items),
            "sentence_count": sentence_count,
            "aspect_scores": aspect_scores,
            "review_weights_applied": True,
            "review_weight_summary": review_weight_summary,
            "reviews": weighted_reviews,
        }

    return restaurant_results


def detect_cuisine(category_text, name=""):
    # raw metadata.category가 있으면 우선 신뢰하고, 없을 때만 키워드로 추정.
    category = str(category_text).strip()
    if category in CUISINE_WEIGHTS:
        return category

    text = f"{category_text} {name}".replace(" ", "").lower()
    if not text.strip():
        return DEFAULT_CUISINE

    best_cuisine = DEFAULT_CUISINE
    best_hits = 0
    for cuisine, keywords in CUISINE_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword.replace(" ", "").lower() in text)
        if hits > best_hits:
            best_cuisine = cuisine
            best_hits = hits
    return best_cuisine


def _review_count(row, raw_restaurant):
    # raw 리뷰 수가 있으면 그것을 우선 사용하고, 없으면 집계 결과의 리뷰 수를 fallback으로 사용.
    if isinstance(raw_restaurant, dict) and isinstance(raw_restaurant.get("reviews"), list):
        return len(raw_restaurant["reviews"])

    if "review_count" in row:
        count = row.get("review_count")
        if isinstance(count, int):
            return count
        parsed_count = _extract_count(count)
        return parsed_count if parsed_count is not None else 0

    if isinstance(row.get("reviews"), list) and row["reviews"]:
        return len(row["reviews"])
    return None


def _log_norm(value, max_value):
    # 리뷰 수 같은 규모가 큰 값은 로그 정규화해서 대형 매장이 점수를 독식하지 않게 함.
    if value is None or value <= 0 or max_value <= 0:
        return None
    return math.log1p(value) / math.log1p(max_value)


def _popularity_score(item, max_visitor_count, max_blog_count):
    # 방문자 리뷰를 더 중요하게 보고, 블로그 리뷰는 보조 인기도 신호로 반영.
    visitor_score = _log_norm(item["visitor_review_count"], max_visitor_count)
    blog_score = _log_norm(item["blog_review_count"], max_blog_count)
    return _weighted_average([(visitor_score, 0.7), (blog_score, 0.3)])


def _round_or_none(value, digits=3):
    return None if value is None else round(float(value), digits)


def ranking_category_for(cuisine):
    # 내부 업종명을 실제 랭킹 파일의 카테고리명으로 변환.
    return RANKING_CATEGORY_MAP.get(cuisine)


def _ranking_entry(rid, row, rank):
    # 카테고리별 랭킹 파일에는 웹페이지 목록에 필요한 핵심 필드만 담음.
    return {
        "rank": rank,
        "restaurant_id": rid,
        "name": row.get("name", rid),
        "rec_score": row.get("rec_score"),
        "final_score": row.get("final_score"),
        "cuisine": row.get("cuisine"),
        "category": row.get("category"),
        "review_count": row.get("review_count", 0),
        "sentence_count": row.get("sentence_count", 0),
        "aspect_scores": row.get("aspect_scores", {}),
        "aspect_weights": row.get("aspect_weights", {}),
        "score_components": row.get("score_components", {}),
        "review_weight_summary": row.get("review_weight_summary", {}),
    }


def build_category_rankings(scores, top_n=None):
    # 전체 식당 점수에서 카테고리별 리스트를 다시 만들고, 카테고리 내부 순위를 부여.
    rankings = {category: [] for category in RANKING_CATEGORIES}

    sorted_items = sorted(
        scores.items(),
        key=lambda item: item[1].get("rec_score", 0),
        reverse=True,
    )
    for rid, row in sorted_items:
        category = row.get("ranking_category") or ranking_category_for(row.get("cuisine"))
        if category not in rankings:
            continue
        if top_n is not None and len(rankings[category]) >= top_n:
            continue

        rank = len(rankings[category]) + 1
        rankings[category].append(_ranking_entry(rid, row, rank))

    return rankings


def aggregate_restaurant_scores(restaurant_results, raw_data=None, reference_date=None):
    # 식당별 aspect 점수와 메타데이터를 합쳐 최종 추천 점수와 전체/카테고리 순위를 만들기.
    reference_date = _parse_reference_date(reference_date)
    raw_data = raw_data or {}
    prepared = {}
    base_scores = []

    for rid, row in restaurant_results.items():
        raw_restaurant = raw_data.get(rid, {})
        meta = _metadata(raw_restaurant)

        name = row.get("name") or _stringify(_first_value(meta, NAME_KEYS)) or rid
        category_text = _stringify(_first_value(meta, CATEGORY_KEYS))
        cuisine = detect_cuisine(category_text, name)
        weights = CUISINE_WEIGHTS.get(cuisine, CUISINE_WEIGHTS[DEFAULT_CUISINE])

        # 이미 리뷰별 가중치가 적용된 입력이면 그대로 쓰고, 아니면 이 단계에서 리뷰별 집계를 수행.
        aspect_scores = row.get("aspect_scores", {})
        weighted_reviews = row.get("reviews", [])
        review_weight_summary = row.get("review_weight_summary", {})
        if row.get("review_weights_applied") is not True and row.get("review_items"):
            aspect_scores, weighted_reviews, review_weight_summary = aggregate_review_aspect_scores(
                row["review_items"],
                reference_date,
            )

        aspect_total = _aspect_total(aspect_scores, weights)
        review_count = _review_count(row, raw_restaurant)
        visitor_review_count = _extract_count(_first_value(meta, VISITOR_REVIEW_KEYS))
        blog_review_count = _extract_count(_first_value(meta, BLOG_REVIEW_KEYS))

        # 네이버 방문자 리뷰 수가 없으면 분석에 사용된 리뷰 수를 약한 인기도 신호로 대체.
        popularity_review_count = visitor_review_count
        if popularity_review_count is None and review_count is not None and review_count > 0:
            popularity_review_count = review_count

        rating_score = _extract_rating(_first_value(meta, RATING_KEYS))

        base_scores.append(aspect_total)
        prepared[rid] = {
            "source": row,
            "name": name,
            "category": category_text,
            "cuisine": cuisine,
            "weights": weights,
            "weight_reason": WEIGHT_REASONS.get(cuisine, WEIGHT_REASONS[DEFAULT_CUISINE]),
            "aspect_scores": aspect_scores,
            "aspect_total": aspect_total,
            "review_count": review_count,
            "visitor_review_count": popularity_review_count,
            "blog_review_count": blog_review_count,
            "rating_score": rating_score,
            "weighted_reviews": weighted_reviews,
            "review_weight_summary": review_weight_summary,
        }

    prior = mean(base_scores) if base_scores else 0.5
    max_visitor_count = max((item["visitor_review_count"] or 0 for item in prepared.values()), default=0)
    max_blog_count = max((item["blog_review_count"] or 0 for item in prepared.values()), default=0)

    scored = {}
    for rid, item in prepared.items():
        row = item["source"]
        # 리뷰 수가 적은 식당은 전체 평균 쪽으로 조금 당겨 표본 부족에 따른 과대평가를 줄이기.
        if item["review_count"] is None:
            confidence = 1.0
        else:
            confidence = item["review_count"] / (item["review_count"] + MIN_REVIEWS_FOR_CONFIDENCE)
        sentiment_score = item["aspect_total"] * confidence + prior * (1 - confidence)
        popularity_score = _popularity_score(item, max_visitor_count, max_blog_count)

        # 최종 점수는 감정 기반 점수를 중심으로, 인기도와 별점을 보조적으로 더해줌.
        rec_score = _weighted_average([
            (sentiment_score, SENTIMENT_WEIGHT),
            (popularity_score, POPULARITY_WEIGHT),
            (item["rating_score"], RATING_WEIGHT),
        ]) or sentiment_score

        scored[rid] = {
            "name": item["name"],
            "category": item["category"],
            "cuisine": item["cuisine"],
            "review_count": item["review_count"] or 0,
            "sentence_count": row.get("sentence_count", len(row.get("reviews", []))),
            "rec_score": round(rec_score, 3),
            "final_score": round(rec_score * 100, 1),
            "aspect_scores": item["aspect_scores"],
            "aspect_weights": item["weights"],
            "weight_reason": item["weight_reason"],
            "score_components": {
                "aspect_total": round(item["aspect_total"], 3),
                "sentiment_score": round(sentiment_score, 3),
                "confidence": round(confidence, 3),
                "popularity_score": _round_or_none(popularity_score),
                "rating_score": _round_or_none(item["rating_score"]),
                "review_weight_sum": item["review_weight_summary"].get("sum"),
            },
            "review_weight_summary": item["review_weight_summary"],
            "metadata": {
                "visitor_review_count": item["visitor_review_count"],
                "blog_review_count": item["blog_review_count"],
            },
            "reviews": item["weighted_reviews"],
        }

    sorted_items = sorted(scored.items(), key=lambda item: item[1]["rec_score"], reverse=True)
    ranked = {}
    category_rank_counts = defaultdict(int)
    for rank, (rid, row) in enumerate(sorted_items, start=1):
        # 전체 순위와 별도로 카테고리 내부 순위도 결과에 저장.
        ranking_category = ranking_category_for(row.get("cuisine"))
        row["ranking_category"] = ranking_category
        if ranking_category:
            category_rank_counts[ranking_category] += 1
            row["category_rank"] = category_rank_counts[ranking_category]
        else:
            row["category_rank"] = None
        row["rank"] = rank
        ranked[rid] = row
    return ranked


def _resolve_input_path(input_arg):
    # 기본값은 BERT 추론 결과(absa_scores.json)를 먼저 보되,
    # 사전 기반 결과(aspect_scores.json)만 있는 경우도 바로 실행되도록 보완.
    input_path = Path(input_arg)
    if input_path.exists():
        return input_path

    default_absa_path = INTERIM / "absa_scores.json"
    fallback_aspect_path = INTERIM / "aspect_scores.json"
    if input_path == default_absa_path and fallback_aspect_path.exists():
        return fallback_aspect_path

    message = (
        f"입력 점수 파일을 찾을 수 없습니다: {input_path}\n"
        "프로젝트 data/interim 폴더에 absa_scores.json 또는 aspect_scores.json을 두거나,\n"
        "다음처럼 --input 옵션으로 점수 파일 경로를 직접 지정해 주세요.\n"
        '예: python aggregate.py --input "C:\\path\\to\\aspect_scores.json" '
        '--raw "C:\\path\\to\\naver_reviews.json"'
    )
    raise FileNotFoundError(message)


def main():
    # aspect_scores/absa_scores를 읽어 최종 점수 파일과 카테고리별 랭킹 파일 만들기.
    # 터미널 실행 예시:
    # python aggregate.py --input "aspect_scores.json이 있는 경로" --raw "naver_reviews.json이 있는 경로" --output "..\data\final\restaurant_scores.json" --category-output "..\data\final\category_rankings.json" --reference-date 2026-05-21
    # reference-date는 실행하는 날 기준 오늘 날짜를 YYYY-MM-DD 형식으로 넣으면 됩니다!
    parser = argparse.ArgumentParser(
        description="Aggregate restaurant ABSA scores into final recommendation scores.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "실행 예시:\n"
            '  python aggregate.py --input "aspect_scores.json이 있는 경로" '
            '--raw "naver_reviews.json이 있는 경로" '
            '--output "..\\data\\final\\restaurant_scores.json" '
            '--category-output "..\\data\\final\\category_rankings.json" '
            "--reference-date 2026-05-21\n\n"
            "reference-date는 실행하는 날 기준 오늘 날짜를 YYYY-MM-DD 형식으로 넣으면 됩니다!"
        ),
    )
    parser.add_argument("--input", default=str(INTERIM / "absa_scores.json"))
    parser.add_argument("--raw", default=str(RAW_DATA))
    parser.add_argument("--output", default=str(DATA_DIR / "final" / "restaurant_scores.json"))
    parser.add_argument("--category-output", default=str(DATA_DIR / "final" / "category_rankings.json"))
    parser.add_argument("--category-top-n", type=int, default=None)
    parser.add_argument("--reference-date", default=None)
    args = parser.parse_args()

    try:
        input_path = _resolve_input_path(args.input)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    raw_path = Path(args.raw)
    input_data = load_json(input_path)
    raw_data = load_json(raw_path) if raw_path.exists() else {}
    if not raw_data:
        print(f"[경고] 리뷰 메타데이터 파일을 찾지 못했습니다: {raw_path}")
        print("[경고] 리뷰 최신성/작성자 활동량/네이버 카테고리 기반 보정이 제한됩니다.")
    if isinstance(input_data, list):
        # 리스트 입력은 문장/절 단위 결과(aspect_scores.json)로 보고 식당 단위로 먼저 묶고,
        restaurant_results = build_restaurant_results_from_aspect_rows(
            input_data,
            raw_data,
            args.reference_date,
        )
    else:
        # dict 입력은 이미 식당 단위로 집계된 결과(absa_scores.json 등)로 간주.
        restaurant_results = input_data

    scores = aggregate_restaurant_scores(restaurant_results, raw_data, args.reference_date)
    save_scores(scores, args.output)

    # 웹페이지에서 탭별 목록을 바로 그릴 수 있도록 카테고리별 랭킹도 별도 파일로 저장.
    category_rankings = build_category_rankings(scores, args.category_top_n)
    save_category_rankings(category_rankings, args.category_output)

    print(f"Saved {len(scores)} restaurant scores to {args.output}")
    print(f"Saved category rankings to {args.category_output}")


if __name__ == "__main__":
    main()
