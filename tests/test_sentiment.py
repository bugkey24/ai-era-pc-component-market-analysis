"""Tests for SentimentAnalyzer (offline — no NLTK download dependency)."""

import pytest

from src.analysis import SentimentAnalyzer


@pytest.fixture
def labeled_reviews():
    """Small balanced dataset for smoke-testing the training path."""
    texts = [
        # positive
        "barang bagus sekali, sangat puas",
        "kualitas oke, cepat sampai",
        "performa mantap,Recommended banget",
        "puas dengan pembelian ini",
        " Produk bagus dan awet",
        # negative
        "barang jelek, kecewa sekali",
        "mahal tapi kualitas buruk",
        "rusak saat diterima, kecewa",
        "layanan lambat dan mengecewakan",
        "tidak recommended, buruk",
    ] * 2  # 20 samples — minimum viable for a split
    labels = (["positive"] * 5 + ["negative"] * 5) * 2
    return texts, labels


class TestPreprocessText:
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()

    def test_empty_input_returns_empty(self):
        assert self.analyzer.preprocess_text("") == ""
        assert self.analyzer.preprocess_text("   ") == ""
        assert self.analyzer.preprocess_text(None) == ""

    def test_lowercases_and_strips(self):
        result = self.analyzer.preprocess_text("Barang BAGUS Sekali!!!")
        assert result == result.lower()
        assert "!" not in result

    def test_removes_stopwords(self):
        result = self.analyzer.preprocess_text("barang ini bagus dan murah")
        assert "ini" not in result
        assert "dan" not in result
        assert "bagus" in result  # content word preserved

    def test_drops_single_chars(self):
        result = self.analyzer.preprocess_text("a bagus b murah")
        assert " a " not in f" {result} "
        assert "bagus" in result


class TestTraining:
    def test_train_sets_flag_and_accuracy(self, labeled_reviews):
        analyzer = SentimentAnalyzer()
        analyzer.train(*labeled_reviews)
        assert analyzer.is_trained
        assert 0.0 <= analyzer.accuracy <= 1.0

    def test_train_produces_report(self, labeled_reviews):
        analyzer = SentimentAnalyzer()
        analyzer.train(*labeled_reviews)
        assert analyzer.report is not None
        assert "positive" in analyzer.report or "0" in analyzer.report

    def test_train_too_few_samples_raises(self):
        analyzer = SentimentAnalyzer()
        with pytest.raises(ValueError, match="Too few"):
            analyzer.train(["bagus"], ["positive"])

    def test_train_filters_empty_strings(self, labeled_reviews):
        texts, labels = labeled_reviews
        texts_with_empty = texts + ["", "   "]
        labels_with_empty = labels + ["positive", "negative"]
        analyzer = SentimentAnalyzer()
        analyzer.train(texts_with_empty, labels_with_empty)  # must not crash
        assert analyzer.is_trained


class TestPrediction:
    def test_predict_before_train_raises(self):
        analyzer = SentimentAnalyzer()
        with pytest.raises(ValueError, match="not trained"):
            analyzer.predict(["bagus"])

    def test_predict_returns_labels(self, labeled_reviews):
        analyzer = SentimentAnalyzer()
        analyzer.train(*labeled_reviews)
        preds = analyzer.predict(["barang bagus sekali", "barang jelek sekali"])
        assert len(preds) == 2
        assert all(p in ("positive", "negative") for p in preds)

    def test_aspect_sentiment_structure(self, labeled_reviews):
        analyzer = SentimentAnalyzer()
        analyzer.train(*labeled_reviews)
        texts = ["harga mahal", "kualitas bagus", "performa cepat"]
        aspects = {"price": ["harga"], "performance": ["performa"]}
        results = analyzer.aspect_sentiment(texts, aspects)
        for _aspect, dist in results.items():
            assert set(dist.keys()) <= {"positive", "negative", "neutral"}
            assert all(0.0 <= v <= 1.0 for v in dist.values())
