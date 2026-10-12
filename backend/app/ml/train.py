import os
import csv
import pickle
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def train_classifier(output_path: Optional[str] = None):
    # Locate labeled dataset
    possible_paths = [
        "dataset/training/labeled_transactions.csv",
        "../dataset/training/labeled_transactions.csv",
        "backend/data/fixtures/labeled_transactions.csv",
        "data/fixtures/labeled_transactions.csv"
    ]
    
    dataset_path = None
    for p in possible_paths:
        if os.path.exists(p):
            dataset_path = p
            break
            
    descriptions = []
    categories = []
    
    if dataset_path:
        with open(dataset_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                descriptions.append(row["description"])
                categories.append(row["category"])
    else:
        # Fallback synthetic training pairs
        defaults = [
            ("SWIGGY ORDER", "Food & Dining"),
            ("ZOMATO FOOD DELIVERY", "Food & Dining"),
            ("STARBUCKS CAFE", "Food & Dining"),
            ("BLINKIT GROCERY", "Groceries"),
            ("ZEPTO COMMERCE", "Groceries"),
            ("BESCOM ELECTRICITY", "Utilities"),
            ("AIRTEL FIBER BROADBAND", "Utilities"),
            ("APARTMENT RENT TRANSFER", "Housing & Rent"),
            ("UBER TRIP", "Transportation"),
            ("SHELL PETROL FUEL", "Transportation"),
            ("NETFLIX SUBSCRIPTION", "Entertainment"),
            ("SPOTIFY PREMIUM", "Entertainment"),
            ("CULT FIT GYM", "Health & Fitness"),
            ("APOLLO PHARMACY", "Health & Fitness"),
            ("AMAZON SELLER INDIA", "Shopping"),
            ("ZERODHA BROKING", "Investments"),
            ("TECHCORP SALARY CREDIT", "Income")
        ]
        descriptions = [d[0] for d in defaults]
        categories = [d[1] for d in defaults]

    # Try scikit-learn first
    model = None
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        
        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=500, C=1.0))
        ])
        pipe.fit(descriptions, categories)
        model = pipe
        logger.info(f"Trained scikit-learn LogisticRegression classifier with {len(descriptions)} samples.")
    except ImportError:
        from app.ml.classifier import LightweightTFIDFClassifier
        lw = LightweightTFIDFClassifier()
        lw.fit(descriptions, categories)
        model = lw
        logger.info(f"Trained pure-Python LightweightTFIDFClassifier with {len(descriptions)} samples.")

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(model, f)
        logger.info(f"Saved trained classifier to {output_path}")

    return model

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_classifier("backend/app/ml/category_model.pkl")
