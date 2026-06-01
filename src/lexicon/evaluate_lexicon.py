import numpy as np
from kiwipiepy import Kiwi
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import classification_report
from src.utils import DATASET, LEXICON, load_json
from src.lexicon.weak_labeler import find_aspect_sentiment

ASPECT_LEXICON = LEXICON / "aspect_lexicon.json"
SENTIMENT_LEXICON = LEXICON / "sentiment_lexicon.json"
SPECIFIC_MAP = LEXICON / "specific_sentiment_map.json"
GOLDEN_TEST = DATASET / "golden_test.json"


def evaluate():
    test_data = load_json(GOLDEN_TEST)
    raw_aspect_lexicon = load_json(ASPECT_LEXICON)
    raw_sentiment_lexicon = load_json(SENTIMENT_LEXICON)
    specific_sentiment_map = load_json(SPECIFIC_MAP)

    aspect_lexicon = {aspect: set(words) for aspect, words in raw_aspect_lexicon.items()}
    sentiment_lexicon = {word: float(score) for word, score in raw_sentiment_lexicon.items()}
    find_aspect = {}
    for aspect, words in aspect_lexicon.items():
        for word in words:
            find_aspect[word] = aspect

    y_true = []
    y_pred = []
    kiwi = Kiwi()

    for rev in test_data:
        tokens = rev["tokens"]
        raw_data = rev["raw"]

        # 정답(Golden) 라벨
        y_true.append(rev["labels"])

        # 예측(Lexicon) 라벨
        soft_preds = find_aspect_sentiment(raw_data, aspect_lexicon, sentiment_lexicon, find_aspect, specific_sentiment_map, kiwi)

        POS_THRESH = 0.2
        NEG_THRESH = 0.2
        for label, score in soft_preds.items():
            if label[-2:] == "긍정":
                pred_labels = [label for label, score in soft_preds.items() if score >= POS_THRESH]
            else:
                pred_labels = [label for label, score in soft_preds.items() if score >= NEG_THRESH]

        y_pred.append(pred_labels)


    classes = [
        "음식_긍정", "음식_부정",
        "서비스_긍정", "서비스_부정",
        "분위기_긍정", "분위기_부정",
        "가격_긍정", "가격_부정"
    ]
    
    mlb = MultiLabelBinarizer(classes=classes)
    
    # 텍스트 라벨을 [1, 0, 0, 1, 0...] 형태의 텐서로 변환
    y_true_bin = mlb.fit_transform(y_true)
    y_pred_bin = mlb.transform(y_pred)

    # 성능 리포트 출력
    print("\n=== Lexicon Model Performance Report ===")
    print(classification_report(y_true_bin, y_pred_bin, target_names=classes, zero_division=0))

if __name__ == "__main__":
    evaluate()
