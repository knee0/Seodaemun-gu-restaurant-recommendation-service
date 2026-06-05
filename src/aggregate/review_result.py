from src.utils import SCORES, load_json, save_json

INPUT = SCORES / "final_scores.json"
data = load_json(INPUT)

ASPECTS = ["음식", "서비스", "분위기", "가격"]
final_rankings = {}

for aspect in ASPECTS:
    aspect_list = []
    
    for res_id, info in data.items():
        res_data = info.get("res_data", {})
        name = res_data.get("name", "")
        category = res_data.get("category", "")
        
        score = info.get("aspect_scores", {}).get(aspect, 0.0)
        
        aspect_list.append({
            "res_id": res_id,
            "name": name,
            "category": category,
            "score": score
        })
    
    # 점수를 기준으로 높은 순 정렬
    aspect_list.sort(key=lambda x: x["score"], reverse=True)
    
    # 정렬된 리스트에 순위 부여
    for rank, item in enumerate(aspect_list, start=1):
        item["rank"] = rank
        
    # 결과 딕셔너리에 저장
    final_rankings[aspect] = aspect_list


print("=== Kcelectra 모델 기반 속성별 맛집 랭킹 ===")

for aspect in ASPECTS:
    print(f"\n[{aspect}] 부문 순위")
    for item in final_rankings[aspect][:10]:
        print(f"{item['rank']}위: {item['name']} ({item['category']}) ➔ {item['score']:.4f}점")

