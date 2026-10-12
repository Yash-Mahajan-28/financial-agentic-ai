import os
import re
import math
import pickle
import logging
from typing import Tuple, Dict, List, Optional
from collections import defaultdict
from app.config import settings

logger = logging.getLogger(__name__)

class LightweightTFIDFClassifier:
    """A resilient pure-Python TF-IDF + Multinomial Naive Bayes classifier.
    Guarantees ML categorization even in lightweight runtime environments without binary dependencies.
    """
    def __init__(self):
        self.classes: List[str] = []
        self.vocab: Dict[str, int] = {}
        self.class_word_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.class_totals: Dict[str, int] = defaultdict(int)
        self.doc_counts: Dict[str, int] = defaultdict(int)
        self.total_docs: int = 0

    def tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        tokens = [t for t in cleaned.split() if len(t) > 1 and not t.isdigit()]
        return tokens

    def fit(self, texts: List[str], labels: List[str]):
        self.classes = list(set(labels))
        self.total_docs = len(texts)
        for text, label in zip(texts, labels):
            tokens = set(self.tokenize(text))
            for tok in tokens:
                self.doc_counts[tok] += 1
            for tok in self.tokenize(text):
                self.class_word_counts[label][tok] += 1
                self.class_totals[label] += 1
                if tok not in self.vocab:
                    self.vocab[tok] = len(self.vocab)

    def predict_proba(self, text: str) -> Dict[str, float]:
        tokens = self.tokenize(text)
        if not tokens or not self.classes:
            return {c: 1.0 / max(1, len(self.classes)) for c in self.classes}
        
        scores: Dict[str, float] = {}
        v_size = max(1, len(self.vocab))
        for c in self.classes:
            log_prob = math.log(max(1, sum(1 for tok in tokens if self.class_word_counts[c][tok] > 0) + 1) / (self.total_docs + len(self.classes)))
            for tok in tokens:
                count = self.class_word_counts[c][tok]
                tf_idf = (count + 1.0) / (self.class_totals[c] + v_size)
                log_prob += math.log(tf_idf)
            scores[c] = log_prob
            
        # Softmax normalize
        max_score = max(scores.values()) if scores else 0.0
        exp_scores = {c: math.exp(s - max_score) for c, s in scores.items()}
        sum_exp = sum(exp_scores.values())
        return {c: (v / sum_exp) for c, v in exp_scores.items()}

    def predict(self, text: str) -> Tuple[str, float]:
        probas = self.predict_proba(text)
        if not probas:
            return "Unclassified", 0.0
        best_cat = max(probas, key=probas.get)
        return best_cat, probas[best_cat]

class TransactionClassifier:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.MODEL_PATH
        self.model = None
        self._load_or_train_model()

    def _load_or_train_model(self):
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                logger.info(f"Loaded classifier from {self.model_path}")
                return
            except Exception as e:
                logger.warning(f"Could not load classifier from {self.model_path}: {e}")
        
        # Self-bootstrap model from training dataset
        from app.ml.train import train_classifier
        self.model = train_classifier(self.model_path)

    def predict(self, description: str) -> Tuple[str, float]:
        if not self.model:
            return "Unclassified", 0.0
        try:
            # Check if scikit-learn pipeline or lightweight classifier
            if hasattr(self.model, "predict_proba"):
                try:
                    # scikit-learn
                    proba = self.model.predict_proba([description])[0]
                    classes = self.model.classes_
                    best_idx = proba.argmax()
                    return str(classes[best_idx]), float(proba[best_idx])
                except Exception:
                    pass
            if hasattr(self.model, "predict"):
                return self.model.predict(description)
        except Exception as e:
            logger.error(f"Prediction error for '{description}': {e}")
        return "Unclassified", 0.0

classifier = TransactionClassifier()
