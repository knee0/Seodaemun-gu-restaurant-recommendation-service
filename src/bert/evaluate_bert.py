import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import classification_report
from src.utils import DATASET, MODELS, load_json, LEXICON

GOLDEN_TEST = DATASET / "golden_test.json"
MODEL_PATH = MODELS / "models" / "kcelectra_multilabel"
ASPECT_LABELS = ['음식_긍정', '음식_부정', '서비스_긍정', '서비스_부정', '분위기_긍정', '분위기_부정', '가격_긍정', '가격_부정']

def evaluate():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load Data, Model, Tokenizer, and Thresholds
    test_data = load_json(GOLDEN_TEST)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
    model.eval()

    threshold_data = load_json(MODELS / "best_thresholds.json")
    th_tensor = torch.tensor([threshold_data[label] for label in ASPECT_LABELS], device=device)

    texts = [rev.get("raw", "") for rev in test_data]
    y_true = [rev.get("labels", []) for rev in test_data]
    y_pred_bin_list = []

    batch_size = 8
    print("Running BERT inference...")
    
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            
            inputs = tokenizer(
                batch_texts, 
                truncation=True, 
                padding=True, 
                max_length=128, 
                return_tensors="pt"
            ).to(device)
            
            outputs = model(**inputs)
            probs = torch.sigmoid(outputs.logits)
            preds = (probs > th_tensor).int().cpu().tolist()
            
            y_pred_bin_list.extend(preds) 

    mlb = MultiLabelBinarizer(classes=ASPECT_LABELS)
    y_true_bin = mlb.fit_transform(y_true)
    y_pred_bin = np.array(y_pred_bin_list)

    print("\n=== Bert Model Performance Report ===")
    print(classification_report(y_true_bin, y_pred_bin, target_names=ASPECT_LABELS, zero_division=0))

if __name__ == "__main__":
    evaluate()
