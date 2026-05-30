import json
import numpy as np
import torch
from tqdm import tqdm
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from src.utils import PREP, MODELS, SCORES, load_json, save_json

MODEL = MODELS / "models" / "kcelectra_multilabel"
INPUT = PREP / "preprocessed.json"
OUTPUT = SCORES / "bert_scores.json"
THRESHOLDS = MODELS / "best_thresholds.json"

ASPECT_LABELS = ['음식_긍정', '음식_부정', '서비스_긍정', '서비스_부정', '분위기_긍정', '분위기_부정', 
    '가격_긍정', '가격_부정', '편의성_긍정', '편의성_부정']

class InferenceDataset(Dataset):
    def __init__(self, data, tokenizer, max_length=256):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = item.get("raw", "")
        rev_id = item.get("rev_id", "")
        
        inputs = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        # Squeeze out batch dimension added by return_tensors
        return {
            "rev_id": rev_id,
            "input_ids": inputs["input_ids"].squeeze(0),
            "attention_mask": inputs["attention_mask"].squeeze(0)
        }

def run_inference():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)
    model.to(device)
    model.eval()

    id2label = model.config.id2label

    thresholds = load_json(THRESHOLDS)
    th_list = [thresholds[label] for label in ASPECT_LABELS]
    th_tensor = torch.tensor(th_list, device = device)

    raw_data = load_json(INPUT)
    dataset = InferenceDataset(raw_data, tokenizer)
    dataloader = DataLoader(dataset, batch_size=8) 

    results = []

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Inferencing"):
            rev_ids = batch["rev_id"]
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            
            probs = torch.sigmoid(logits)
            preds = (probs > th_tensor).int()

            for i in range(len(rev_ids)):
                predicted_labels = []
                for idx, val in enumerate(preds[i].tolist()):
                    if val == 1:
                        predicted_labels.append(id2label[idx])

                results.append({
                    "rev_id": rev_ids[i],
                    "labels": predicted_labels
                })

    save_json(results, OUTPUT)

if __name__ == "__main__":
    run_inference()
