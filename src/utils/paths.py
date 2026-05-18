from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
SRC_DIR = ROOT / "src"
MODELS = SRC_DIR / "sentiment" / "models"
RAW_DATA = DATA_DIR / "raw" / "naver_reviews.json"
INTERIM = DATA_DIR / "interim"
