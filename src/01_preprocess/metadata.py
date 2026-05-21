import json
from src.utils import RAW_DATA, PREP, load_json, save_json

INPUT = RAW_DATA
OUTPUT = PREP / "metadata.json"

def make_metadata(data):
    dataset = {}

    # res_data에는 식당 이름과 카테고리(한식/일식 등),
    # rev_data에는 리뷰에 대한 정보(리뷰 ID, 방문 일자, 작성 리뷰 개수, 방문 횟수).
    # 전자는 웹페이지를 제작할 때, 후자는 식당 총점을 계산할 때 활용.
    for rid, restaurant in data.items():
        metadata = restaurant.get("metadata", {})

        res_data = {
            "name": metadata.get("name"),
            "category": metadata.get("category")
        }

        rev_datas = []
        for idx, review in enumerate(restaurant.get("reviews", [])):
            # preprocessed.py에서 만든 리뷰 ID와 같은 방식.
            rev_id = f"{rid}_{idx}"

            rev_datas.append({
                "rev_id": rev_id,
                "visit_time": review.get("visit_datetime"),
                "review_count": review.get("review_count"),
                "visit_count": review.get("visit_count")
            })

        dataset[rid] = {
            "res_data": res_data,
            "rev_data": rev_datas
        }
                                
    return dataset

def main():
    data = load_json(INPUT)
    metadata = make_metadata(data)
    save_json(metadata, OUTPUT, 4)

if __name__ == "__main__":
    main()
