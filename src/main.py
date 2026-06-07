# Pipeline script for /src

# Pre-conditions:
# 'naver_reviews.json' in /data/raw
# 'metadata.json' in data/prep
# 'golden_val.json', 'golden_test.json' in data/dataset

from src.utils import DATA_DIR, RAW_DATA, PREP, LEXICON, DATASET, SCORES, MODELS, load_json, save_json
from src.prep.preprocess import preprocess

