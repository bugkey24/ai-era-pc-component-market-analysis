"""Statistical analysis for PC component market data."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger("analysis.statistical")


class StatisticalAnalyzer:
    """Descriptive statistics, correlation, and trend analysis on product data."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()
        self.summary: Optional[pd.DataFrame] = None
        self.correlations: Optional[pd.DataFrame] = None
        logger.info("StatisticalAnalyzer initialised with %d rows", len(self.df))

    # ------------------------------------------------------------------
    # Descriptive
    # ------------------------------------------------------------------

    def describe(self, columns: list[str] | None = None) -> StatisticalAnalyzer:
        """Compute descriptive statistics (mean, median, std, quartiles)."""
        cols = columns or self.df.select_dtypes(include=np.number).columns.tolist()
        self.summary = self.df[cols].describe(percentiles=[0.25, 0.5, 0.75]).T
        self.summary["median"] = self.df[cols].median()
        self.summary["iqr"] = self.summary["75%"] - self.summary["25%"]
        self.summary["skewness"] = self.df[cols].skew()
        self.summary["kurtosis"] = self.df[cols].kurtosis()
        logger.info("Descriptive stats computed for %d columns", len(cols))
        return self

    # ------------------------------------------------------------------
    # Correlation
    # ------------------------------------------------------------------

    def correlation_matrix(
        self, method: str = "pearson", columns: list[str] | None = None
    ) -> StatisticalAnalyzer:
        """Compute pairwise correlation matrix."""
        cols = columns or self.df.select_dtypes(include=np.number).columns.tolist()
        self.correlations = self.df[cols].corr(method=method)
        logger.info("Correlation matrix computed (%s) — %d columns", method, len(cols))
        return self

    def price_correlation_with(self, target: str = "rating") -> dict:
        """Return correlation stats between ``price`` and *target* column."""
        if "price" not in self.df.columns or target not in self.df.columns:
            return {}
        r, p = stats.pearsonr(
            self.df["price"].dropna(), self.df[target].dropna()
        )
        return {"pearson_r": round(r, 4), "p_value": round(p, 6)}

    # ------------------------------------------------------------------
    # Trend analysis
    # ------------------------------------------------------------------

    def price_trend_by_category(self) -> pd.DataFrame:
        """Group by category and compute per-category price stats."""
        if "category" not in self.df.columns:
            return pd.DataFrame()

        trend = (
            self.df.groupby("category")["price"]
            .agg(["mean", "median", "std", "min", "max", "count"])
            .round(2)
        )
        trend["cv"] = (trend["std"] / trend["mean"]).round(3)  # coefficient of variation
        return trend

    def price_by_source(self) -> pd.DataFrame:
        """Compare price distributions across platforms."""
        if "source" not in self.df.columns:
            return pd.DataFrame()

        return (
            self.df.groupby("source")["price"]
            .agg(["mean", "median", "std", "count"])
            .round(2)
        )

    # ------------------------------------------------------------------
    # Normality
    # ------------------------------------------------------------------

    def normality_test(self, column: str = "price") -> dict:
        """Shapiro-Wilk normality test on *column*."""
        if column not in self.df.columns or len(self.df) < 3:
            return {"error": "insufficient data"}
        sample = self.df[column].dropna()
        if len(sample) > 5000:
            sample = sample.sample(5000, random_state=42)
        stat, p = stats.shapiro(sample)
        return {
            "statistic": round(float(stat), 4),
            "p_value": round(float(p), 6),
            "normal_at_0.05": bool(p > 0.05),
        }

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def get_summary(self) -> Optional[pd.DataFrame]:
        return self.summary

    def get_correlations(self) -> Optional[pd.DataFrame]:
        return self.correlations
