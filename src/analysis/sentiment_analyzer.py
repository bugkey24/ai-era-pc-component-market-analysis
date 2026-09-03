"""Sentiment analysis using SVM on product reviews."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC

logger = logging.getLogger("analysis.sentiment")


class SentimentAnalyzer:
    """SVM-based sentiment classifier with aspect-based analysis."""

    _STOPWORDS_ID = [
        "yang", "dan", "di", "ini", "itu", "untuk", "dengan", "pada",
        "adalah", "ke", "dari", "tidak", "akan", "juga", "sudah", "ada",
        "bisa", "lebih", "mereka", "saya", "kami", "kita", "bagi", "atau",
        "namun", "jika", "maka", "hanya", "masih", "lagi", "setiap",
        "oleh", "karena", "itu", "sangat", "telah", "dalam", "belum",
        "sedang", "bahwa", "selalu", "hampir", "walau", "walaupun",
    ]

    _STOPWORDS_EN = [
        "the", "is", "at", "which", "on", "a", "an", "and", "or", "but",
        "in", "with", "to", "for", "of", "not", "no", "can", "had", "has",
        "it", "its", "was", "were", "be", "been", "are", "do", "did",
        "this", "that", "these", "those", "i", "you", "he", "she", "we",
        "they", "me", "him", "her", "us", "them", "my", "your", "his",
    ]

    def __init__(self, language: str = "indonesian", max_features: int = 5000) -> None:
        self.language = language
        self.vectorizer = TfidfVectorizer(max_features=max_features)
        self.model = LinearSVC(class_weight="balanced", random_state=42, max_iter=1000)
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.accuracy: Optional[float] = None
        self.report: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Text preprocessing
    # ------------------------------------------------------------------

    def preprocess_text(self, text: str) -> str:
        """Clean, lowercase, remove non-alpha chars, strip stopwords."""
        if not isinstance(text, str) or not text.strip():
            return ""

        text = text.lower()
        text = re.sub(r"[^a-z\s]", " ", text)
        tokens = text.split()

        stop_words = set(self._STOPWORDS_ID + self._STOPWORDS_EN)
        tokens = [t for t in tokens if t not in stop_words and len(t) > 1]
        return " ".join(tokens)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(
        self,
        texts: List[str],
        labels: List[str],
        test_size: float = 0.2,
    ) -> SentimentAnalyzer:
        """Train the SVM classifier and evaluate on a held-out split."""
        logger.info("Training sentiment model on %d samples", len(texts))

        processed = [self.preprocess_text(t) for t in texts]
        valid_mask = [bool(p.strip()) for p in processed]
        processed = [p for p, v in zip(processed, valid_mask) if v]
        labels = [l for l, v in zip(labels, valid_mask) if v]

        if len(processed) < 10:
            raise ValueError("Too few valid samples after preprocessing")

        X = self.vectorizer.fit_transform(processed)
        y = self.label_encoder.fit_transform(labels)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y if len(set(y)) > 1 else None
        )

        self.model.fit(X_train, y_train)
        self.is_trained = True

        y_pred = self.model.predict(X_test)
        self.accuracy = float((y_pred == y_test).mean())
        self.report = classification_report(
            y_test, y_pred, target_names=self.label_encoder.classes_, output_dict=True
        )
        logger.info("Model trained — accuracy: %.3f", self.accuracy)
        return self

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, texts: List[str]) -> List[str]:
        """Predict sentiment labels for new texts."""
        if not self.is_trained:
            raise ValueError("Model not trained yet. Call train() first.")
        processed = [self.preprocess_text(t) for t in texts]
        X = self.vectorizer.transform(processed)
        encoded = self.model.predict(X)
        return self.label_encoder.inverse_transform(encoded).tolist()

    # ------------------------------------------------------------------
    # Aspect-based analysis
    # ------------------------------------------------------------------

    def aspect_sentiment(
        self, texts: List[str], aspects: Dict[str, List[str]]
    ) -> Dict[str, Dict[str, float]]:
        """Run sentiment per aspect (keyword-filtered)."""
        if not self.is_trained:
            raise ValueError("Model not trained yet.")

        results: Dict[str, Dict[str, float]] = {}
        all_preds = self.predict(texts)
        lower_texts = [t.lower() for t in texts]

        for aspect_name, keywords in aspects.items():
            indices = [
                i for i, t in enumerate(lower_texts)
                if any(kw.lower() in t for kw in keywords)
            ]
            if not indices:
                continue
            preds = [all_preds[i] for i in indices]
            total = len(preds)
            results[aspect_name] = {
                label: round(preds.count(label) / total, 3)
                for label in self.label_encoder.classes_
            }
        return results

    # ------------------------------------------------------------------
    # Bulk analysis helper
    # ------------------------------------------------------------------

    def analyse_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str = "review_text",
        source_col: str = "source",
    ) -> pd.DataFrame:
        """Add a ``sentiment`` column to *df* in-place."""
        if text_col not in df.columns:
            logger.warning("Column '%s' not found — skipping", text_col)
            return df
        df["sentiment"] = self.predict(df[text_col].fillna("").tolist())
        return df
