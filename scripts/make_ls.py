import json
from src.utils import DATASET, load_json, save_json

INPUT = DATASET / "golden_val_raw.json"
OUTPUT = DATASET / "golden_val_raw_ls.json"

raw_data = load_json(INPUT)

transformed = []

for item in raw_data:
    ls_item = {
        "data": {
            "rev_id": item["rev_id"],
            "raw": item["raw"],
            "tokens": item["tokens"],
        },
        "predictions": [
            {
                "result": [
                    {
                        "from_name": "absa_labels",
                        "to_name": "text",
                        "type": "choices",
                        "value": {"choices": item["labels"]},
                    }
                ]
            }
        ],
    }
    transformed.append(ls_item)

save_json(transformed, OUTPUT)