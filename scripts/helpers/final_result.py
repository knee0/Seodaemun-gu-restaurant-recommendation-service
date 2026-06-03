from src.utils import SCORES, load_json

def print_top_10_by_aspect(dataset):
    aspects = ["음식", "서비스", "분위기", "가격"]

    for aspect in aspects:
        scored_restaurants = []
        
        for res_id, data in dataset.items():
            name = data.get("res_data", {}).get("name", "")
            score = data.get("aspect_scores", {}).get(aspect, 0.0)
            scored_restaurants.append((name, score))
        
        scored_restaurants.sort(key=lambda x: x[1], reverse=True)
        top_10 = scored_restaurants[:10]
        
        # Print the formatted output
        print(f"\n=== [{aspect}] 카테고리 상위 10개 식당 ===")
        for rank, (name, score) in enumerate(top_10, start=1):
            print(f"{rank:2d}. {name:<20} (점수: {score:.4f})")

if __name__ == "__main__":
    INPUT = SCORES / "final_scores.json"
    dataset = load_json(INPUT)
    print_top_10_by_aspect(dataset)