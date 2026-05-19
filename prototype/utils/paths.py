from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRO = ROOT / "prototype"

DATA_DIR = PRO / "data"
RAW_DATA = ROOT / "data" / "raw" / "naver_reviews.json"
