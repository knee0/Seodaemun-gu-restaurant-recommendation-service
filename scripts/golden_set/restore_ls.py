import json
from src.utils import DATASET, load_json, save_json

LABEL = DATASET / "golden_val.json"
ORIGINAL = DATASET / "golden_val_raw.json"
OUTPUT = DATASET / "golden_val_final.json"

def restore_tokens_to_gold(labeled_path, original_path, output_path):
    labeled_data = load_json(LABEL)
    original_data = load_json(ORIGINAL)

    token_lookup = {item["rev_id"]: item["tokens"] for item in original_data}

    for item in labeled_data:
        rev_id = item["rev_id"]
        if rev_id in token_lookup:
            # Reinsert tokens right before labels for clean structure
            item["tokens"] = token_lookup[rev_id]
        else:
            print(f"Warning: Could not find tokens for rev_id {rev_id}")
            item["tokens"] = []

    save_json(labeled_data, output_path)

restore_tokens_to_gold(LABEL, ORIGINAL, OUTPUT)