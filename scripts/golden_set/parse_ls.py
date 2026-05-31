import re
from src.utils import DATASET, load_json, save_json

INPUT = DATASET / "golden_test_append_ls.json"
OUTPUT = DATASET / "golden_test_append.json"


# preprocess.py에 있는 영어 리뷰 판별 함수입니다.
def is_english(text, threshold = 0.7):
    clean_text = re.sub(r"\s+", "", text)
    if not clean_text:
        return False

    english_chars = re.findall(r"[a-zA-Z]", text)
    ratio = len(english_chars) / len(text)
    return ratio > threshold


# Label Studio에서 제공하는 json을 이용하기 편한 형태로 변환합니다.
def parse_ls(INPUT, OUTPUT):
    ls_data = load_json(INPUT)
    golden_set = []
    noise = 0

    for item in ls_data:
        task_data = item["data"]

        # 케이크 레터링 매장의 리뷰는 제외합니다.
        if task_data["rev_id"].split("_")[0] == "1572782359":
            continue

        # 영어 리뷰는 제외합니다.
        if is_english(task_data["raw"]):
            continue

        # 직접 라벨링한 값을 가져옵니다..
        human_labels = []
        if item.get("annotations"):
            
            # 최종적으로 라벨링한 결과를 활용합니다.
            latest_annotation = item["annotations"][-1]
            for result in latest_annotation.get("result", []):
                if result.get("type") == "choices":
                    human_labels.extend(result["value"]["choices"])

        # 기존의 json 형태로 전환합니다.
        clean_sample = {
            "rev_id": task_data["rev_id"],
            "raw": task_data["raw"],
            "tokens": task_data["tokens"],
            "labels": human_labels,
        }
    
        golden_set.append(clean_sample)

    save_json(golden_set, OUTPUT)

parse_ls(INPUT, OUTPUT)
