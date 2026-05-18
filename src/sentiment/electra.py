import json
import pandas as pd
from tqdm import tqdm
from src.utils.paths import INTERIM, MODELS
import numpy as np
from datasets import Dataset, ClassLabel
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from collections import defaultdict
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, DataCollatorWithPadding

print(torch.cuda.is_available())

# Data prep
MODEL_NAME = "monologg/koelectra-base-v3-discriminator"
ASPECTS = ["맛", "서비스", "분위기", "가격", "시스템"]
LABEL_MAP = {0: "Negative", 1: "Positive"}

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_and_format(batch):
    tokenized = tokenizer(text=batch["text"], text_pair=batch["aspect"], truncation=True, 
                          padding=False, max_length=128)
    tokenized["label"] = batch["label"]
    return tokenized

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)

    acc = accuracy_score(labels, preds)
    macro_f1 = f1_score(labels, preds, average="macro")

    return {"accuracy": float(acc), "macro_f1": float(macro_f1)}

def label_score(score):
    if score is None: return None
    elif score < -0.75: return 0
    elif score > 0.75: return 1
    return None

def train_model(raw_data):
    processed_data = []
    for item in raw_data:
        for aspect in ASPECTS:
            raw_score = item["aspect_score"].get(aspect)
            class_label = label_score(raw_score)
            if class_label is not None:
                processed_data.append({"text": item["raw"], "aspect": aspect, "label": class_label})

    df = pd.DataFrame(processed_data)

    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)
    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)

    features = train_dataset.features.copy()
    features["label"] = ClassLabel(num_classes=2, names=["Negative", "Positive"])
    train_dataset = train_dataset.cast(features)
    val_dataset = val_dataset.cast(features)

    train_dataset = train_dataset.map(tokenize_and_format, batched=True)
    val_dataset = val_dataset.map(tokenize_and_format, batched=True)

    train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    val_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

    training_args = TrainingArguments(
        output_dir="./results",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=1,
        weight_decay=0.01,
        logging_steps=100,
        fp16=True,
        dataloader_num_workers=0,
        report_to="none",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer)
    )

    print(f"Trainer device: {training_args.device}")
    print(f"Model device: {model.device}")
    trainer.train()
    trainer.save_model(MODELS / "koelectra_aspect_model")
    tokenizer.save_pretrained(MODELS / "koelectra_aspect_model")


def main():
    with open(INTERIM / "aspect_scores.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    train_model(raw_data)

if __name__ == "__main__":
    main()
