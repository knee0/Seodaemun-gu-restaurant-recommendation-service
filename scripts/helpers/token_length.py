import json
import re
from kiwipiepy import Kiwi
from src.utils import RAW_DATA, load_json

INPUT = RAW_DATA

kiwi = Kiwi()

def normalize(text):
    text = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1+", r"\1\1", text)
    text = re.sub(r"[^가-힣0-9\s.,!?~]", "", text)
    text = re.sub(r"\s+([.,!?~])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text



def preprocess(data):
    longer_than_max = 0
    dataset = []

    for rid, restaurant in data.items():
        for idx, review in enumerate(restaurant.get("reviews", [])):
            raw = review.get("content", "").strip()
            text = normalize(raw)

            tokens = kiwi.tokenize(text)
            if len(tokens) > 128:
                longer_than_max += 1
      
    return longer_than_max


def main():
    data = load_json(INPUT)
    print(preprocess(data))

if __name__ == "__main__":
    main()
