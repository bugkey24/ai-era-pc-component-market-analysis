"""Tests for DataPreprocessor and FeatureEngineer."""

import numpy as np
import pandas as pd
import pytest

from src.preprocessing import DataPreprocessor, FeatureEngineer


class TestCleanPrices:
    def test_converts_rupiah_strings(self, sample_products):
        result = DataPreprocessor(sample_products).clean_prices().get_cleaned_data()
        assert result["price"].dtype == int
        assert result.loc[0, "price"] == 4_500_000

    def test_handles_missing_price_column(self, sample_products):
        df = sample_products.drop(columns=["price"])
        # Should not raise, just skip
        result = DataPreprocessor(df).clean_prices().get_cleaned_data()
        assert "price" not in result.columns

    def test_invalid_strings_become_zero(self):
        df = pd.DataFrame({"price": ["abc", "Rp 1.000", None]})
        result = DataPreprocessor(df).clean_prices().get_cleaned_data()
        assert result.loc[0, "price"] == 0
        assert result.loc[1, "price"] == 1_000


class TestHandleMissing:
    def test_drop_removes_nan_rows(self):
        df = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": [1, 2, 3]})
        result = DataPreprocessor(df).handle_missing("drop").get_cleaned_data()
        assert len(result) == 2

    def test_fill_uses_numeric_median(self):
        df = pd.DataFrame({"a": [1.0, np.nan, 3.0], "label": ["x", "y", "z"]})
        result = DataPreprocessor(df).handle_missing("fill").get_cleaned_data()
        assert result.loc[1, "a"] == 2.0
        assert result.loc[1, "label"] == "y"  # non-numeric untouched

    def test_invalid_strategy_raises(self, sample_products):
        with pytest.raises(ValueError, match="strategy"):
            DataPreprocessor(sample_products).handle_missing("explode")


class TestExtractSpecifications:
    def test_extracts_capacity(self, sample_products):
        result = DataPreprocessor(sample_products).extract_specifications().get_cleaned_data()
        assert result.loc[0, "spec_capacity"] == "8GB"
        assert result.loc[3, "spec_capacity"] == "1TB"

    def test_extracts_memory_type(self, sample_products):
        result = DataPreprocessor(sample_products).extract_specifications().get_cleaned_data()
        assert result.loc[0, "spec_memory_type"] == "DDR5"
        assert result.loc[2, "spec_memory_type"] == "DDR5"

    def test_extracts_interface(self, sample_products):
        result = DataPreprocessor(sample_products).extract_specifications().get_cleaned_data()
        assert result.loc[3, "spec_interface"] == "NVMe"


class TestRemoveOutliers:
    def test_removes_extreme_values(self):
        df = pd.DataFrame({"price": [100] * 10 + [1_000_000]})
        result = DataPreprocessor(df).remove_outliers("price", threshold=3.0).get_cleaned_data()
        assert len(result) == 10

    def test_skips_when_std_zero(self):
        df = pd.DataFrame({"price": [100, 100, 100]})
        result = DataPreprocessor(df).remove_outliers("price").get_cleaned_data()
        assert len(result) == 3  # nothing removed, no crash


class TestNormalizeRatings:
    def test_scales_to_5(self):
        df = pd.DataFrame({"rating": [5, 10, 7.5]})
        result = DataPreprocessor(df).normalize_ratings("rating").get_cleaned_data()
        assert result["rating"].max() == pytest.approx(5.0)
        assert result.loc[0, "rating"] == pytest.approx(2.5)


class TestChaining:
    def test_full_chain(self, sample_products):
        result = (
            DataPreprocessor(sample_products)
            .clean_prices()
            .handle_missing("drop")
            .extract_specifications()
            .remove_outliers()
            .get_cleaned_data()
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5  # no NaN rows in fixture


# ---------------------------------------------------------------------------
# FeatureEngineer
# ---------------------------------------------------------------------------


class TestPricePerGb:
    def test_computes_price_per_gb(self):
        df = pd.DataFrame({"price": [1_000_000, 500_000], "spec_capacity": ["1TB", "512GB"]})
        result = FeatureEngineer(df).create_price_per_gb().get_engineered_data()
        # 1TB = 1024 GB → ~976.56; 512GB → ~976.56
        assert result["price_per_gb"].iloc[0] == pytest.approx(976.56, abs=0.1)
        assert result["price_per_gb"].iloc[1] == pytest.approx(976.56, abs=0.1)

    def test_zero_capacity_becomes_nan(self):
        df = pd.DataFrame({"price": [100], "spec_capacity": [""]})
        result = FeatureEngineer(df).create_price_per_gb().get_engineered_data()
        assert pd.isna(result["price_per_gb"].iloc[0])


class TestWeightedRating:
    def test_more_reviews_increases_weight(self):
        df = pd.DataFrame({"rating": [5.0, 5.0], "review_count": [1000, 1]})
        result = FeatureEngineer(df).create_weighted_rating(min_reviews=5).get_engineered_data()
        assert result["weighted_rating"].iloc[0] > result["weighted_rating"].iloc[1]


class TestSellerTrust:
    def test_trust_increases_with_followers(self):
        df = pd.DataFrame({"seller_rating": [5.0, 5.0], "seller_followers": [10_000, 10]})
        result = FeatureEngineer(df).create_seller_trust_score().get_engineered_data()
        assert result["seller_trust"].iloc[0] > result["seller_trust"].iloc[1]

    def test_handles_missing_followers_column(self):
        df = pd.DataFrame({"seller_rating": [5.0]})
        result = FeatureEngineer(df).create_seller_trust_score().get_engineered_data()
        assert result["seller_trust"].iloc[0] == pytest.approx(0.0)
