from src.utils import SCORES, load_json, save_json

INPUT = SCORES / "final_scores.json"
OUTPUT = SCORES / "web_format_scores.json"

def web_format(data):
    formatted_list = []
    
    for index, (rid, contents) in enumerate(data.items(), start=1):
        res_data = contents.get("res_data", {})
        aspect_scores = contents.get("aspect_scores", {})
        
        food = round(aspect_scores.get("음식", 0.0), 1)
        price = round(aspect_scores.get("가격", 0.0), 1)
        mood = round(aspect_scores.get("분위기", 0.0), 1)
        service = round(aspect_scores.get("서비스", 0.0), 1)
        
        scores = {
            "food": food,
            "price": price,
            "mood": mood,
            "service": service
        }
        
        total_score = round(sum(scores.values()) / len(scores), 1) if scores else 0.0
        
        # 3. Deduplicate the menu items while preserving order
        raw_menu = res_data.get("all_menu", [])
        clean_menu = list(dict.fromkeys(raw_menu)) if raw_menu else []
        raw_url = res_data.get("naver_url")
        clean_url = raw_url.split("/review")[0] if raw_url else None
        
        # 4. Construct the beautiful flattened dictionary
        record = {
            "id": f"r{index:03d}",  # Formats into 'r001', 'r002', etc.
            "name": res_data.get("name"),
            "category": res_data.get("category"),
            "category_raw": res_data.get("category_raw"),
            "total_score": total_score,
            "scores": scores,
            "menus": clean_menu,  # Look at that, no more duplicate ramen!
            "address": res_data.get("address"),
            "naver_url": clean_url,
            "thumbnail_url": res_data.get("thumbnail_url")
        }
        
        formatted_list.append(record)
    return formatted_list

def main():
    raw_data = load_json(INPUT)
    final_data = web_format(raw_data)
    save_json(final_data, OUTPUT)
    print(f"Success! Converted {len(final_data)} records into the final array format.")


if __name__ == "__main__":
    main()