import json
from collections import defaultdict
from prototype.utils.paths import DATA_DIR, RAW_DATA

INPUT = DATA_DIR / "aspect_scores.json"
OUTPUT = DATA_DIR / "with_names.json"

# Current data only has restaurant ID
# Load names from raw for readable result
def load_restaurant_names(raw_data):
    mapping = {}

    for rid, info in raw_data.items():
        name = info.get("metadata", {}).get("name", "Unknown")
        mapping[rid] = name

    return mapping

# Attach restaurant name as attribute
def attach_names(data, name_map):
    for rid, info in data.items():
        info["name"] = name_map.get(rid, "Unknown")
    return data


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(RAW_DATA, "r", encoding="utf-8") as f:
        raw = json.load(f)

    name_map = load_restaurant_names(raw)
    data = attach_names(data, name_map)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
