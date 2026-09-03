"""Tests for utils (config loading + logger) and StatisticalAnalyzer."""

import logging

import pandas as pd
import pytest

from src.analysis import StatisticalAnalyzer
from src.utils import load_config, setup_logger


class TestLoadConfig:
    def test_loads_project_config(self):
        config = load_config("config.yaml")
        assert config["project"]["name"] == "AI-Driven Market Analysis"
        assert "scraping" in config
        assert "dss" in config

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(str(tmp_path / "nonexistent.yaml"))


class TestSetupLogger:
    def test_returns_named_logger(self):
        logger = setup_logger(name="test-logger-x")
        assert logger.name == "test-logger-x"

    def test_repeated_calls_do_not_duplicate_handlers(self):
        setup_logger(name="test-logger-y")
        logger = setup_logger(name="test-logger-y")
        assert len(logger.handlers) == 1


class TestStatisticalAnalyzer:
    @pytest.fixture
    def analyzer_df(self):
        return pd.DataFrame(
            {
                "price": [100, 200, 150, 300, 250, 180, 220, 190],
                "rating": [4.5, 4.8, 4.6, 4.9, 4.7, 4.4, 4.8, 4.5],
                "category": ["gpu"] * 4 + ["ram"] * 4,
                "source": ["tokopedia", "shopee"] * 4,
            }
        )

    def test_describe_produces_summary(self, analyzer_df):
        analyzer = StatisticalAnalyzer(analyzer_df)
        result = analyzer.describe()
        summary = result.get_summary()
        assert "price" in summary.index
        assert "median" in summary.columns
        assert "iqr" in summary.columns

    def test_correlation_matrix(self, analyzer_df):
        analyzer = StatisticalAnalyzer(analyzer_df)
        result = analyzer.correlation_matrix()
        corr = result.get_correlations()
        assert corr.loc["price", "rating"] == corr.loc["rating", "price"]  # symmetric
        assert corr.loc["price", "price"] == pytest.approx(1.0)

    def test_price_trend_by_category(self, analyzer_df):
        analyzer = StatisticalAnalyzer(analyzer_df)
        trend = analyzer.price_trend_by_category()
        assert set(trend.index) == {"gpu", "ram"}
        assert "cv" in trend.columns

    def test_price_by_source(self, analyzer_df):
        analyzer = StatisticalAnalyzer(analyzer_df)
        by_source = analyzer.price_by_source()
        assert set(by_source.index) == {"tokopedia", "shopee"}

    def test_normality_test_structure(self, analyzer_df):
        analyzer = StatisticalAnalyzer(analyzer_df)
        result = analyzer.normality_test("price")
        assert "statistic" in result and "p_value" in result
        assert isinstance(result["normal_at_0.05"], bool)

    def test_normality_test_insufficient_data(self):
        analyzer = StatisticalAnalyzer(pd.DataFrame({"price": [1.0]}))
        assert "error" in analyzer.normality_test("price")
