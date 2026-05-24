import json
from collections import Counter
from src.utils import PREP, load_json

INPUT = PREP / "metadata.json"

def main():
    data = load_json(INPUT)

    visit_times = []
    review_counts = []
    visit_counts = []
    
    for rid, restaurant in data.items():
        for review in restaurant.get("rev_data", []):
            vt = review.get("visit_time")
            rc = review.get("review_count")
            vc = review.get("visit_count")
            
            if vt:
                visit_times.append(vt)
            if rc is not None:
                review_counts.append(rc)
            if vc is not None:
                visit_counts.append(vc)

    visit_times.sort()
    review_counts.sort()
    visit_counts.sort()
    
    total_reviews = len(visit_times)

    print("=== Visit Time Distribution ===")
    # Extract first 4 characters (Year) from ISO format
    years = [vt[:4] for vt in visit_times]
    year_counts = Counter(years)
    
    for year in sorted(year_counts.keys()):
        count = year_counts[year]
        percentage = (count / total_reviews) * 100
        print(f"{year} reviews {count} / {percentage:.1f}%")
        
    # Statistics for Activity (Review Counts)
    print("\n=== Review Count Distribution Summary ===")
    n_rc = len(review_counts)
    if n_rc > 0:
        print(f"Min: {review_counts[0]}")
        print(f"25% (Q1): {review_counts[int(n_rc * 0.25)]}")
        print(f"50% (Median): {review_counts[int(n_rc * 0.50)]}")
        print(f"75% (Q3): {review_counts[int(n_rc * 0.75)]}")
        print(f"95% Cutoff: {review_counts[int(n_rc * 0.95)]}")
        print(f"Max: {review_counts[-1]}")
        
    # Statistics for Loyalty (Visit Counts)
    print("\n=== Visit Count Distribution Summary ===")
    n_vc = len(visit_counts)
    if n_vc > 0:
        print(f"Min: {visit_counts[0]}")
        print(f"25% (Q1): {visit_counts[int(n_vc * 0.25)]}")
        print(f"50% (Median): {visit_counts[int(n_vc * 0.50)]}")
        print(f"75% (Q3): {visit_counts[int(n_vc * 0.75)]}")
        print(f"95% Cutoff: {visit_counts[int(n_vc * 0.95)]}")
        print(f"Max: {visit_counts[-1]}")

if __name__ == "__main__":
    main()
