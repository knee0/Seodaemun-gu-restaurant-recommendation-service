from collections import defaultdict
from src.utils import PREP, SCORES, load_json, save_json

INPUT = SCORES / "bert_scores.json"
METADATA = PREP / "metadata.json"
FINAL = SCORES / "restaurant_scores.json"

CONFIDENCE = 20

def aggregate_aspect_scores():
    bert_scores = load_json(INPUT)
    metadata = load_json(METADATA)

    id2weight = {}
    for res_id, res_info in metadata.items():
        for rev in res_info.get("rev_data", []):
            id2weight[rev["rev_id"]] = rev.get("weight", 1.0)

    # Global trackers for Bayesian Smoothing
    global_scores = {'맛': 0.0, '서비스': 0.0, '분위기': 0.0, '가격': 0.0}
    global_counts = {'맛': 0, '서비스': 0, '분위기': 0, '가격': 0}

    # Trackers for individual restaurants
    total_scores = {}
    total_counts = {}

    for res_id in metadata.keys():
        total_scores[res_id] = {'맛': 0.0, '서비스': 0.0, '분위기': 0.0, '가격': 0.0}
        total_counts[res_id] = {'맛': 0, '서비스': 0, '분위기': 0, '가격': 0}

    for review in bert_scores:
        rev_id = review.get("rev_id")

        res_id = rev_id.split("_")[0]
        weight = id2weight[rev_id]

        labels = review.get("labels", [])

        for label in labels:
            aspect, sentiment = label.split("_")
            total_counts[res_id][aspect] += 1
            global_counts[aspect] += 1

            if sentiment == "긍정":
                total_scores[res_id][aspect] += weight
                global_scores[aspect] += weight
            elif sentiment == "부정":
                total_scores[res_id][aspect] -= weight
                global_scores[aspect] -= weight


    global_avg = {}
    for aspect in global_scores.keys():
        global_avg[aspect] = global_scores[aspect] / global_counts[aspect]


    final_output = {}
    for res_id, res_info in metadata.items():
        res_data = res_info.get("res_data", {})

        avg_scores = {}
        cur_scores = total_scores[res_id]
        cur_counts = total_counts[res_id]

        for aspect, count in cur_counts.items():
            if count > 0:
                score_sum = cur_scores[aspect]
                avg = global_avg[aspect]
                avg_sum = CONFIDENCE * avg

                # Apply Bayesian Smoothing
                smoothed_score = (score_sum + avg_sum) / (count + CONFIDENCE)
                avg_scores[aspect] = round(smoothed_score, 4)
            else:
                avg_scores[aspect] = 0.0

        final_output[res_id] = {
            "res_data": res_data,
            "aspect_scores": avg_scores
        }

    save_json(final_output, FINAL)
    print("Done. Your restaurant scores are saved.")

if __name__ == "__main__":
    aggregate_aspect_scores()