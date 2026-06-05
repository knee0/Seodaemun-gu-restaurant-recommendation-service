import json
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from src.utils import MODELS, DATASET, load_json, save_json
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score, hamming_loss
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, DataCollatorWithPadding, EvalPrediction
)

print(torch.cuda.is_available())

# Data prep
MODEL_NAME = "beomi/KcELECTRA-base-v2022"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
TRAIN = DATASET / "train_data.json"
VALIDATE = DATASET / "golden_val.json"
RESULT = MODELS / "./results"
MODEL = MODELS / "./models"

ASPECT_LABELS = ['음식_긍정', '음식_부정', '서비스_긍정', '서비스_부정', '분위기_긍정', '분위기_부정', '가격_긍정', '가격_부정']
NUM_LABELS = len(ASPECT_LABELS)

LABEL_TO_ID = {}
ID_TO_LABEL = {}
for idx, label in enumerate(ASPECT_LABELS):
    LABEL_TO_ID[label] = idx
    ID_TO_LABEL[idx] = label


def multi_label_vector(raw_data):
    processed = []
    for item in raw_data:
        text = item.get("raw", "")
        labels = item.get("labels", [])
        
        label_vector = [0.0] * NUM_LABELS

        # If labels is a dictionary (Soft labels from Train Lexicon)
        if isinstance(labels, dict):
            for idx, label in enumerate(ASPECT_LABELS):
                label_vector[idx] = float(labels.get(label, 0.05))
                
        # If labels is a list (Hard labels from Golden Val)
        else:
            for idx, label in enumerate(ASPECT_LABELS):
                if label in labels:
                    label_vector[idx] = 1.0

        processed.append({"text": text, "labels": label_vector})

    return pd.DataFrame(processed)


def tokenize_and_format(batch):
    tokenized = tokenizer(batch["text"], truncation=True, padding=False, max_length=128)
    tokenized["labels"] = batch["labels"]
    return tokenized


def compute_metrics(p: EvalPrediction):
    logits = p.predictions[0] if isinstance(p.predictions, tuple) else p.predictions
    labels = p.label_ids
    true_labels = (labels > 0.5).astype(int)

    sigmoid = lambda x: 1 / (1 + np.exp(-x))
    probs = sigmoid(logits)
    preds = (probs > 0.5).astype(int)

    macro_f1 = f1_score(true_labels, preds, average="macro", zero_division=0)
    micro_f1 = f1_score(true_labels, preds, average="micro", zero_division=0)

    subset_accuracy = accuracy_score(labels, preds)
    h_loss = hamming_loss(labels, preds)

    return {
        "macro_f1": float(macro_f1), "micro_f1": float(micro_f1),
        "subset_accuracy": float(subset_accuracy), "hamming_loss": float(h_loss)
    }


def find_best_thresholds(trainer, val_dataset):
    predictions = trainer.predict(val_dataset)
    logits = predictions.predictions[0] if isinstance(predictions.predictions, tuple) else predictions.predictions
    labels = predictions.label_ids
    true_labels = (labels > 0.5).astype(int)

    probs = 1 / (1 + np.exp(-logits))
    best_thresholds = {}
    
    for idx, label_name in enumerate(ASPECT_LABELS):
        best_f1 = 0.0
        best_th = 0.5
        
        for th in np.arange(0.01, 0.99, 0.01):
            preds = (probs[:, idx] > th).astype(int)
            f1 = f1_score(true_labels[:, idx], preds, zero_division=0)
            
            if f1 > best_f1:
                best_f1 = f1
                best_th = th
                
        best_thresholds[label_name] = float(best_th)
        print(f"{label_name:<10} | Best Threshold: {best_th:.2f} | F1-Score: {best_f1:.4f}")

    save_json(best_thresholds, MODELS / "best_thresholds.json")
        
    return best_thresholds


class CustomTrainer(Trainer):
    def __init__(self, pos_weight, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pos_weight = torch.tensor(pos_weight, dtype=torch.float32)

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        
        if self._pos_weight.device != logits.device:
            self._pos_weight = self._pos_weight.to(logits.device)
        
        loss_fct = nn.BCEWithLogitsLoss(pos_weight=self._pos_weight)
        loss = loss_fct(logits, labels.float())
        
        return (loss, outputs) if return_outputs else loss



def train_model():
    raw_train = load_json(TRAIN)
    raw_val = load_json(VALIDATE)

    train_df = multi_label_vector(raw_train)
    val_df = multi_label_vector(raw_val)

    labels_matrix = np.array(train_df['labels'].tolist())  # Shape: (N, 8)
    pos_counts = labels_matrix.sum(axis=0)
    neg_counts = len(labels_matrix) - pos_counts
    
    # Add a tiny epsilon to prevent division by zero
    raw_weights = neg_counts / (pos_counts + 1e-6)
    dynamic_weights = np.clip(np.sqrt(raw_weights), a_min=1.0, a_max=None)

    print(f"Calculated pos_weights: {dynamic_weights.tolist()}")

    # Convert to HuggingFace Datasets
    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)

    # Tokenize
    train_dataset = train_dataset.map(tokenize_and_format, batched=True, remove_columns=["text"])
    val_dataset = val_dataset.map(tokenize_and_format, batched=True, remove_columns=["text"])

    # Set format to PyTorch tensors
    train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
    val_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])


    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels = NUM_LABELS,
        problem_type = "multi_label_classification",
        id2label = ID_TO_LABEL,
        label2id = LABEL_TO_ID
    )

    training_args = TrainingArguments(
        output_dir = RESULT,
        eval_strategy = "epoch",
        save_strategy = "epoch",
        learning_rate = 2e-5,
        per_device_train_batch_size = 4,
        gradient_accumulation_steps = 4,
        per_device_eval_batch_size = 4,
        num_train_epochs = 2,
        weight_decay = 0.01,
        logging_steps = 50,
        save_total_limit = 2,
        fp16 = False,
        dataloader_num_workers = 0,
        report_to = "none",
        load_best_model_at_end = True,
        metric_for_best_model = "eval_macro_f1",
        greater_is_better = True,
        remove_unused_columns = False
    )

    trainer = CustomTrainer(
        pos_weight = dynamic_weights,
        model = model,
        args = training_args,
        train_dataset = train_dataset,
        eval_dataset = val_dataset,
        compute_metrics = compute_metrics,
        data_collator = DataCollatorWithPadding(tokenizer = tokenizer)
    )

    print(f"Trainer device: {training_args.device}")

    trainer.train()
    best_ths = find_best_thresholds(trainer, val_dataset)

    trainer.save_model(MODEL / "kcelectra_multilabel")
    tokenizer.save_pretrained(MODEL / "kcelectra_multilabel")

def main():
    train_model()

if __name__ == "__main__":
    main()
