"""Sentiment analysis using SVM on product reviews."""

from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC

logger = logging.getLogger("analysis.sentiment")


def _load_nltk_stopwords(language: str) -> list[str] | None:
    """Try to load NLTK stopwords for *language*; return None if unavailable."""
    try:
        import nltk

        try:
            from nltk.corpus import stopwords as nltk_stopwords

            return list(nltk_stopwords.words(language))
        except LookupError:
            # Corpus not downloaded yet — attempt a quiet download, then retry
            nltk.download("stopwords", quiet=True)
            from nltk.corpus import stopwords as nltk_stopwords

            return list(nltk_stopwords.words(language))
    except Exception:  # noqa: BLE001 — offline environments fall back gracefully
        logger.info("NLTK stopwords unavailable for '%s' — using built-in list", language)
        return None


class SentimentAnalyzer:
    """SVM-based sentiment classifier with aspect-based analysis."""

    # Built-in fallback stopwords (used when the NLTK corpus is unavailable)
    _STOPWORDS_ID = [
        "yang",
        "dan",
        "di",
        "ini",
        "itu",
        "untuk",
        "dengan",
        "pada",
        "adalah",
        "ke",
        "dari",
        "tidak",
        "akan",
        "juga",
        "sudah",
        "ada",
        "bisa",
        "lebih",
        "mereka",
        "saya",
        "kami",
        "kita",
        "bagi",
        "atau",
        "namun",
        "jika",
        "maka",
        "hanya",
        "masih",
        "lagi",
        "setiap",
        "oleh",
        "karena",
        "itu",
        "sangat",
        "telah",
        "dalam",
        "belum",
        "sedang",
        "bahwa",
        "selalu",
        "hampir",
        "walau",
        "walaupun",
    ]

    _STOPWORDS_EN = [
        "the",
        "is",
        "at",
        "which",
        "on",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "with",
        "to",
        "for",
        "of",
        "not",
        "no",
        "can",
        "had",
        "has",
        "it",
        "its",
        "was",
        "were",
        "be",
        "been",
        "are",
        "do",
        "did",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
    ]

    def __init__(self, language: str = "indonesian", max_features: int = 5000) -> None:
        self.language = language
        self.vectorizer = TfidfVectorizer(max_features=max_features)
        self.model = LinearSVC(class_weight="balanced", random_state=42, max_iter=1000)
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.accuracy: float | None = None
        self.report: dict[str, Any] | None = None
        self._stopword_cache: set[str] | None = None

    # ------------------------------------------------------------------
    # Text preprocessing
    # ------------------------------------------------------------------

    def _get_stopwords(self) -> set[str]:
        """Return the combined stopword set, preferring NLTK corpora."""
        if self._stopword_cache is not None:
            return self._stopword_cache

        nltk_id = _load_nltk_stopwords("indonesian")
        nltk_en = _load_nltk_stopwords("english")

        stop = set(self._STOPWORDS_ID + self._STOPWORDS_EN)
        if nltk_id:
            stop.update(w for w in nltk_id if w.isalpha())
        if nltk_en:
            stop.update(w for w in nltk_en if w.isalpha())

        self._stopword_cache = stop
        return stop

    def preprocess_text(self, text: str) -> str:
        """Clean, lowercase, remove non-alpha chars, strip stopwords."""
        if not isinstance(text, str) or not text.strip():
            return ""

        text = text.lower()
        text = re.sub(r"[^a-z\s]", " ", text)
        tokens = text.split()

        stop_words = self._get_stopwords()
        tokens = [t for t in tokens if t not in stop_words and len(t) > 1]
        return " ".join(tokens)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(
        self,
        texts: list[str],
        labels: list[str],
        test_size: float = 0.2,
    ) -> SentimentAnalyzer:
        """Train the SVM classifier and evaluate on a held-out split."""
        logger.info("Training sentiment model on %d samples", len(texts))

        processed = [self.preprocess_text(t) for t in texts]
        valid_mask = [bool(p.strip()) for p in processed]
        processed = [p for p, v in zip(processed, valid_mask) if v]
        labels = [lab for lab, v in zip(labels, valid_mask) if v]

        if len(processed) < 10:
            raise ValueError("Too few valid samples after preprocessing")

        X = self.vectorizer.fit_transform(processed)
        y = self.label_encoder.fit_transform(labels)

        # A classifier needs at least two classes — fail fast otherwise
        class_counts = pd.Series(y).value_counts()
        if len(class_counts) < 2:
            raise ValueError(
                f"Corpus contains a single class ({class_counts.index[0]!r}) — "
                "sentiment training is impossible; collect negative reviews too"
            )

        # Skewed/small corpora (e-commerce reality: ~all positive): train on
        # the full data without a held-out split — accuracy not measurable
        if class_counts.min() < 2:
            logger.warning(
                "Skewed class distribution %s — fitting on full corpus; "
                "held-out accuracy is not measurable",
                class_counts.to_dict(),
            )
            self.model.fit(X, y)
            self.is_trained = True
            self.accuracy = None
            self.report = None
            return self

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        self.model.fit(X_train, y_train)
        self.is_trained = True

        y_pred = self.model.predict(X_test)
        self.accuracy = float((y_pred == y_test).mean())
        self.report = classification_report(
            y_test,
            y_pred,
            labels=list(range(len(self.label_encoder.classes_))),
            target_names=self.label_encoder.classes_,
            output_dict=True,
            zero_division=0,
        )
        logger.info("Model trained — accuracy: %.3f", self.accuracy)
        return self

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, texts: list[str]) -> list[str]:
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
        self, texts: list[str], aspects: dict[str, list[str]]
    ) -> dict[str, dict[str, float]]:
        """Run sentiment per aspect (keyword-filtered)."""
        if not self.is_trained:
            raise ValueError("Model not trained yet.")

        results: dict[str, dict[str, float]] = {}
        all_preds = self.predict(texts)
        lower_texts = [t.lower() for t in texts]

        for aspect_name, keywords in aspects.items():
            indices = [
                i for i, t in enumerate(lower_texts) if any(kw.lower() in t for kw in keywords)
            ]
            if not indices:
                continue
            preds = [all_preds[i] for i in indices]
            total = len(preds)
            results[aspect_name] = {
                label: round(preds.count(label) / total, 3) for label in self.label_encoder.classes_
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
