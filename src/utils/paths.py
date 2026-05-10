from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
RAW_DATA = DATA_DIR / "raw" / "naver_reviews.json"
