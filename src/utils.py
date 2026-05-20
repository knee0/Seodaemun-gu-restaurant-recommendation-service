from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS = ROOT / "models"
RAW_DATA = DATA_DIR / "raw" / "naver_reviews.json"
INTERIM = DATA_DIR / "interim"

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, file_path, indent=4):
    # Create folder if doesn't exist yet
    # Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)