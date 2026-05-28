import json
import pandas as pd
import numpy as np
import torch
from src.utils import MODELS, DATASET, load_json
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
VALIDATE = DATASET / "golden_val_final.json"
RESULT = MODELS / "./results"
MODEL = MODELS / "./models"

ASPECT_LABELS = ['맛_긍정', '맛_중립', '맛_부정', '서비스_긍정', '서비스_중립', '서비스_부정', 
    '분위기_긍정', '분위기_중립', '분위기_부정', '가격_긍정', '가격_중립', '가격_부정', '편의성_긍정', '편의성_중립', '편의성_부정']
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
        for label in labels:
            label_vector[LABEL_TO_ID[label]] = 1.0

        processed.append({"text": text, "labels": label_vector})

    return pd.DataFrame(processed)


def tokenize_and_format(batch):
    tokenized = tokenizer(batch["text"], truncation=True, padding=False, max_length=128)
    tokenized["labels"] = batch["labels"]
    return tokenized

def compute_metrics(p: EvalPrediction):
    logits = p.predictions[0] if isinstance(p.predictions, tuple) else p.predictions
    labels = p.label_ids

    sigmoid = lambda x: 1 / (1 + np.exp(-x))
    probs = sigmoid(logits)
    preds = (probs > 0.5).astype(int)

    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
    micro_f1 = f1_score(labels, preds, average="micro", zero_division=0)

    subset_accuracy = accuracy_score(labels, preds)
    h_loss = hamming_loss(labels, preds)

    return {
        "macro_f1": float(macro_f1), "micro_f1": float(micro_f1),
        "subset_accuracy": float(subset_accuracy), "hamming_loss": float(h_loss)
    }


def train_model():
    raw_train = load_json(TRAIN)
    raw_val = load_json(VALIDATE)

    train_df = multi_label_vector(raw_train)
    val_df = multi_label_vector(raw_val)

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
        per_device_train_batch_size = 16,
        per_device_eval_batch_size = 16,
        num_train_epochs = 3,
        weight_decay = 0.01,
        logging_steps = 50,
        save_total_limit = 2,
        fp16 = False,
        dataloader_num_workers = 0,
        report_to = "none",
        load_best_model_at_end = True,
        metric_for_best_model = "subset_accuracy",
        greater_is_better = True
    )

    trainer = Trainer(
        model = model,
        args = training_args,
        train_dataset = train_dataset,
        eval_dataset = val_dataset,
        compute_metrics = compute_metrics,
        data_collator = DataCollatorWithPadding(tokenizer = tokenizer)
    )

    print(f"Trainer device: {training_args.device}")

    trainer.train()
    trainer.save_model(MODEL / "kcelectra_multilabel")
    tokenizer.save_pretrained(MODEL / "kcelectra_multilabel")


def main():
    train_model()

if __name__ == "__main__":
    main()
