from src.utils import DATASET, load_json, save_json

def append_to_gold():
    original_val_path = DATASET / "golden_test.json"
    append_val_path = DATASET / "golden_test_append.json"
    
    # Load both files
    original_val = load_json(original_val_path)
    append_val = load_json(append_val_path)
    
    print(f"Before merging:")
    print(f"- Original golden_val size: {len(original_val)} reviews")
    print(f"- New niche reviews to add: {len(append_val)} reviews")
    

    # Ensure zero overlapping IDs
    existing_ids = {rev["rev_id"] for rev in original_val}
    duplicates = [rev["rev_id"] for rev in append_val if rev["rev_id"] in existing_ids]
    
    if duplicates:
        print(f"Found {len(duplicates)} duplicates: skipping...")
        append_val = [rev for rev in append_val if rev["rev_id"] not in existing_ids]
    
    # Append the lists cleanly
    original_val.extend(append_val)
    
    # Save it over original file
    save_json(original_val, original_val_path)
    
    print(f"\nUpdated golden_val.json successfully.")
    print(f"New total size of golden_val: {len(original_val)} reviews")

if __name__ == "__main__":
    append_to_gold()