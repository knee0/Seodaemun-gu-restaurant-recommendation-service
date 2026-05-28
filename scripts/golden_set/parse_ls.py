import json
from src.utils import DATASET, load_json, save_json

INPUT = DATASET / "golden_test_ls.json"
OUTPUT = DATASET / "golden_test.json"

ls_data = load_json(INPUT)

golden_set = []

for item in ls_data:
    task_data = item["data"]

    # Extract human-verified labels safely
    human_labels = []
    if item.get("annotations"):
        # Get the actual submission (usually the latest one)
        latest_annotation = item["annotations"][-1]
        for result in latest_annotation.get("result", []):
            if result.get("type") == "choices":
                human_labels.extend(result["value"]["choices"])

    # Reconstruct your clean, original ABSA schema
    clean_sample = {
        "rev_id": task_data["rev_id"],
        "raw": task_data["raw"],
        "tokens": task_data["tokens"],
        "labels": human_labels,
    }
    
    golden_set.append(clean_sample)

save_json(golden_set, OUTPUT)
