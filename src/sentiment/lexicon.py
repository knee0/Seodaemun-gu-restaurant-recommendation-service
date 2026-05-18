from src.utils.paths import INTERIM
import json
import numpy as np

def run_absa():
    with open(INTERIM / "aspect_lexicon.json", "r", encoding="utf-8") as f:
        aspect_lexicon = json.load(f)
    with open(INTERIM / "sentiment_lexicon.json", "r", encoding="utf-8") as f:
        sentiment_lexicon = json.load(f)
    with open(INTERIM / "preprocessed.json", "r", encoding="utf-8") as f:
        reviews = json.load(f)

    output_results = []

    for rev in reviews:
        rev_id = rev["rev_id"]
        raw_text = rev["raw"]
        tokens = rev["tokens"]
        
        # Make pure word list
        words = [t.split("/")[0] for t in tokens if "/" in t]
        
        # What aspect was mentioned?
        detected_aspects = set()
        for word in words:
            for aspect_cat, aspect_words in aspect_lexicon.items():
                if word in aspect_words:
                    detected_aspects.add(aspect_cat)
                    
        # Does it contain sentiment words?
        scores = []
        for word in words:
            if word in sentiment_lexicon:
                scores.append(sentiment_lexicon[word])
                
        # Average sentiment score
        final_score = float(np.mean(scores)) if scores else 0.0
        
        # Score on mentioned aspect, null on others
        aspect_score = {}
        for aspect_cat in aspect_lexicon.keys():
            if aspect_cat in detected_aspects:
                aspect_score[aspect_cat] = round(final_score, 4)
            else:
                aspect_score[aspect_cat] = None
                
        # Save results
        output_results.append({
            "rev_id": rev_id,
            "raw": raw_text,
            #"tokens": tokens,
            "aspect_score": aspect_score
        })
        
    # Output to .json
    with open(INTERIM/"aspect_scores.json", "w", encoding="utf-8") as f:
        json.dump(output_results, f, ensure_ascii=False, indent=4)
        
    print("Over and out")

if __name__ == "__main__":
    run_absa()


