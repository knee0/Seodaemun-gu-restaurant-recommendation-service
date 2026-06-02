from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
RAW = DATA_DIR / "raw"
RAW_DATA = DATA_DIR / "raw" / "naver_reviews.json"
PREP = DATA_DIR / "prep"
LEXICON = DATA_DIR / "lexicon"
DATASET = DATA_DIR / "dataset"
SCORES = DATA_DIR / "scores"

MODELS = ROOT / "models"

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, file_path, indent=2):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
