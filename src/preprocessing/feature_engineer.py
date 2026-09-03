"""Feature engineering for the PC component market analysis."""

from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger("preprocessing.feature_engineer")


def _parse_capacity_gb(raw: str | float | int) -> float:
    """Convert a spec_capacity string like ``'1TB'`` or ``'512GB'`` to GB."""
    if pd.isna(raw) or raw == "":
        return 0.0
    raw_str = str(raw).upper().strip()
    match = re.match(r"(\d+)\s*(GB|TB)", raw_str)
    if not match:
        return 0.0
    value = float(match.group(1))
    unit = match.group(2)
    return value * 1024 if unit == "TB" else value


class FeatureEngineer:
    """Create derived features from preprocessed product data."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()
        logger.info("FeatureEngineer initialised with %d rows", len(self.df))

    # ------------------------------------------------------------------
    # Price-based features
    # ------------------------------------------------------------------

    def create_price_per_gb(
        self, price_col: str = "price", capacity_col: str = "spec_capacity"
    ) -> FeatureEngineer:
        """Add ``price_per_gb`` = price / capacity_in_gb."""
        if price_col not in self.df.columns or capacity_col not in self.df.columns:
            logger.warning("Required columns missing — skipping price_per_gb")
            return self

        gb = self.df[capacity_col].apply(_parse_capacity_gb)
        gb = gb.replace(0, np.nan)
        self.df["price_per_gb"] = (self.df[price_col] / gb).round(2)
        logger.info("Created price_per_gb — non-null: %d", self.df["price_per_gb"].notna().sum())
        return self

    def create_discount_depth(self) -> FeatureEngineer:
        """Add ``discount_depth`` percentage if original price is available."""
        if "price" not in self.df.columns or "original_price" not in self.df.columns:
            return self
        orig = self.df["original_price"].replace(0, np.nan)
        self.df["discount_depth"] = ((orig - self.df["price"]) / orig * 100).round(2)
        return self

    # ------------------------------------------------------------------
    # Rating-based features
    # ------------------------------------------------------------------

    def create_weighted_rating(
        self,
        rating_col: str = "rating",
        review_col: str = "review_count",
        min_reviews: int = 5,
    ) -> FeatureEngineer:
        """Add ``weighted_rating`` that penalises products with few reviews.

        Formula: ``rating * (review_count / (review_count + min_reviews))``
        """
        if rating_col not in self.df.columns or review_col not in self.df.columns:
            return self

        reviews = self.df[review_col].fillna(0)
        weights = reviews / (reviews + min_reviews)
        self.df["weighted_rating"] = (self.df[rating_col] * weights).round(3)
        logger.info("Created weighted_rating")
        return self

    # ------------------------------------------------------------------
    # Seller features
    # ------------------------------------------------------------------

    def create_seller_trust_score(
        self,
        rating_col: str = "seller_rating",
        followers_col: str = "seller_followers",
    ) -> FeatureEngineer:
        """Add ``seller_trust`` = seller_rating * log(followers + 1)."""
        if rating_col not in self.df.columns:
            return self

        rating = self.df[rating_col].fillna(0)
        if followers_col in self.df.columns:
            followers = self.df[followers_col].fillna(0)
        else:
            followers = pd.Series(0, index=self.df.index)

        self.df["seller_trust"] = (rating * np.log1p(followers)).round(3)
        logger.info("Created seller_trust")
        return self

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def get_engineered_data(self) -> pd.DataFrame:
        """Return the DataFrame with engineered features."""
        logger.info("Returning engineered data — %d cols", len(self.df.columns))
        return self.df
