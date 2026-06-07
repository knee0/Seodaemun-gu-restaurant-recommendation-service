from src.utils import SCORES, load_json, save_json

WEB = SCORES / "old_web.json"
NEW_SCORE = SCORES / "web_prep.json"
OUTPUT = SCORES / "web_format_scores.json"

def merge_restaurant_scores(web_json, new_scores_json, output_json):

    web_data = load_json(web_json)
    new_scores_data = load_json(new_scores_json)


    # Create a lookup map by 'name'
    scores_lookup = {}
    for item in new_scores_data:
        if 'name' in item and 'scores' in item:
            scores_lookup[item['name']] = item['scores']

    # Update the web data WITHOUT touching other metadata
    updated_count = 0
    missing_count = 0
    
    for item in web_data:
        name = item.get('name')
        if name in scores_lookup:
            # Overwrite ONLY the scores object
            item['scores'] = scores_lookup[name]
            updated_count += 1
        else:
            print(f"Warning: Could not find new scores for restaurant '{name}'")
            missing_count += 1

    save_json(web_data, output_json)

    print("\n--- Merge Complete ---")
    print(f"Successfully updated: {updated_count} restaurants.")
    if missing_count > 0:
        print(f"Skipped (Not found): {missing_count} restaurants.")

if __name__ == "__main__":
    merge_restaurant_scores(WEB, NEW_SCORE, OUTPUT)