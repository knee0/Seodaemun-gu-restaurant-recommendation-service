import json
from src.utils import DATASET, load_json, save_json

VAL_IN = DATASET / "golden_val_raw.json"
VAL_OUT = DATASET / "golden_val_raw_ls.json"
TEST_IN = DATASET / "golden_test_raw.json"
TEST_OUT = DATASET / "golden_test_raw_ls.json"


def format_for_ls(INPUT, OUTPUT):
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


def main():
    format_for_ls(VAL_IN, VAL_OUT)
    format_for_ls(TEST_IN, TEST_OUT)

if __name__ == "__main__":
    main()