from collections import defaultdict
from src.utils import PREP, SCORES, load_json, save_json

INPUT = SCORES / "bert_scores.json"
METADATA = PREP / "metadata.json"
FINAL = SCORES / "final_scores.json"

ASPECT_CONFIDENCE = {
    '음식': 12,      # High volume (85%): Needs a strong anchor
    '서비스': 5,     # Medium volume (25%): Balanced anchor
    '분위기': 5,     # Medium volume (23%): Balanced anchor
    '가격': 3        # Low volume (8%): Needs a very light touch to be dynamic
}

def aggregate_aspect_scores():
    bert_scores = load_json(INPUT)
    metadata = load_json(METADATA)

    id2weight = {}
    for res_id, res_info in metadata.items():
        for rev in res_info.get("rev_data", []):
            id2weight[rev["rev_id"]] = rev.get("weight", 1.0)

    ASPECTS = ['음식', '서비스', '분위기', '가격']

    # Global trackers for Bayesian Smoothing
    global_scores = {aspect: 0.0 for aspect in ASPECTS}
    global_counts = {aspect: 0 for aspect in ASPECTS}

    # Trackers for individual restaurants
    total_scores = {}
    total_counts = {}

    for res_id in metadata.keys():
        total_scores[res_id] = {aspect: 0.0 for aspect in ASPECTS}
        total_counts[res_id] = {aspect: 0 for aspect in ASPECTS}

    for review in bert_scores:
        rev_id = review.get("rev_id")

        res_id = rev_id.split("_")[0]
        weight = id2weight[rev_id]

        # 메타데이터에 없는 리뷰 ID가 있을 경우 기본값 1.0 (있으면 안 )
        weight = id2weight.get(rev_id, 1.0)
        labels = review.get("labels", [])

        for label in labels:
            aspect, sentiment = label.split("_")

            total_counts[res_id][aspect] += 1
            global_counts[aspect] += 1

            # 각 리뷰의 점수를 즉시 0 ~ 1 사이로 정규화하여 누적
            if sentiment == "긍정":
                norm_score = (weight + 1.44) / 2.88
            elif sentiment == "부정":
                norm_score = (-weight + 1.44) / 2.88

            total_scores[res_id][aspect] += norm_score
            global_scores[aspect] += norm_score


    global_avg = {}
    for aspect in ASPECTS:
        if global_counts[aspect] > 0:
            global_avg[aspect] = global_scores[aspect] / global_counts[aspect]
        else:
            global_avg[aspect] = 0.5 # 완벽한 중립


    final_output = {}
    for res_id, res_info in metadata.items():
        res_data = res_info.get("res_data", {})
        avg_scores = {}
        cur_scores = total_scores[res_id]
        cur_counts = total_counts[res_id]

        for aspect in ASPECTS:
            count = cur_counts[aspect]
            avg = global_avg[aspect]
            conf = ASPECT_CONFIDENCE[aspect]

            if count > 0:
                score_sum = cur_scores[aspect]
                avg_sum = conf * avg

                # Apply Bayesian Smoothing
                smoothed_score = (score_sum + avg_sum) / (count + conf)
                avg_scores[aspect] = round(smoothed_score * 5, 4)
            else:
                # 리뷰가 없는 속성은 글로벌 평균 값으로 부여.
                avg_scores[aspect] = round(avg * 5, 4)

        final_output[res_id] = {
            "res_data": res_data,
            "aspect_scores": avg_scores
        }

    save_json(final_output, FINAL)
    print("Done. Your restaurant scores are saved.")

if __name__ == "__main__":
    aggregate_aspect_scores()