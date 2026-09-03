"""Data cleaning and preprocessing pipeline."""

from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger("preprocessing")


class DataPreprocessor:
    """Chainable data-cleaning pipeline for scraped product data.

    Each public method returns ``self`` so calls can be fluently chained::

        df = (
            DataPreprocessor(raw_df)
            .clean_prices()
            .handle_missing("drop")
            .extract_specifications()
            .remove_outliers()
            .get_cleaned_data()
        )
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()
        logger.info("DataPreprocessor initialised with %d rows", len(self.df))

    # ------------------------------------------------------------------
    # Price cleaning
    # ------------------------------------------------------------------

    def clean_prices(self, column: str = "price") -> DataPreprocessor:
        """Convert price strings like ``'Rp 1.250.000'`` to integers."""
        if column not in self.df.columns:
            logger.warning("Column '%s' not found — skipping clean_prices", column)
            return self

        pattern = r"[^0-9]"
        self.df[column] = (
            self.df[column]
            .astype(str)
            .str.replace(pattern, "", regex=True)
        )
        self.df[column] = pd.to_numeric(self.df[column], errors="coerce").fillna(0).astype(int)
        logger.info("Prices cleaned — non-zero rows: %d", (self.df[column] > 0).sum())
        return self

    # ------------------------------------------------------------------
    # Missing values
    # ------------------------------------------------------------------

    def handle_missing(
        self, strategy: str = "drop", subset: list[str] | None = None
    ) -> DataPreprocessor:
        """Handle missing values.

        Parameters
        ----------
        strategy : ``'drop'`` | ``'fill'``
            ``drop`` removes rows with any NaN in *subset* (or all columns).
            ``fill`` fills numeric columns with their median.
        subset : list of column names to consider (optional).
        """
        before = len(self.df)

        if strategy == "drop":
            self.df.dropna(subset=subset, inplace=True)
        elif strategy == "fill":
            numeric_cols = self.df.select_dtypes(include=np.number).columns
            self.df[numeric_cols] = self.df[numeric_cols].fillna(
                self.df[numeric_cols].median()
            )
        else:
            raise ValueError(f"Unknown strategy '{strategy}'. Use 'drop' or 'fill'.")

        logger.info(
            "handle_missing(%s): %d → %d rows",
            strategy, before, len(self.df),
        )
        return self

    # ------------------------------------------------------------------
    # Specification extraction
    # ------------------------------------------------------------------

    def extract_specifications(self) -> DataPreprocessor:
        """Derive spec columns from the product *name* field.

        Extracts capacity (``1TB``, ``512GB``), speed (``DDR5-5600``),
        and interface (``NVMe``, ``SATA``) where applicable.
        """
        if "name" not in self.df.columns:
            return self

        name = self.df["name"].astype(str)

        # Capacity (e.g. 1TB, 512GB, 2TB)
        self.df["spec_capacity"] = name.str.extract(
            r"(\d+)\s*(GB|TB)", flags=re.IGNORECASE
        ).apply(lambda r: f"{r[0]}{r[1].upper()}" if pd.notna(r[0]) else "", axis=1)

        # Memory type (DDR4 / DDR5)
        self.df["spec_memory_type"] = name.str.extract(
            r"(DDR[45])", flags=re.IGNORECASE
        )[0].fillna("")

        # Interface (NVMe / SATA / PCIe)
        self.df["spec_interface"] = name.str.extract(
            r"(NVMe|SATA|PCIe\s*Ge\s*\d+)", flags=re.IGNORECASE
        )[0].fillna("")

        logger.info("Specifications extracted from product names")
        return self

    # ------------------------------------------------------------------
    # Outlier removal
    # ------------------------------------------------------------------

    def remove_outliers(
        self, column: str = "price", threshold: float = 3.0
    ) -> DataPreprocessor:
        """Remove rows whose z-score in *column* exceeds *threshold*."""
        if column not in self.df.columns or len(self.df) == 0:
            return self

        mean = self.df[column].mean()
        std = self.df[column].std()
        if std == 0:
            logger.warning("Std is zero — skipping outlier removal")
            return self

        z = np.abs((self.df[column] - mean) / std)
        before = len(self.df)
        self.df = self.df[z < threshold].reset_index(drop=True)
        logger.info(
            "remove_outliers(%s, %.1f): %d → %d rows",
            column, threshold, before, len(self.df),
        )
        return self

    # ------------------------------------------------------------------
    # Rating normalisation
    # ------------------------------------------------------------------

    def normalize_ratings(self, column: str = "rating", max_scale: float = 5.0) -> DataPreprocessor:
        """Normalise ratings to a 0–*max_scale* range."""
        if column not in self.df.columns:
            return self
        col_max = self.df[column].max()
        if col_max > 0 and col_max != max_scale:
            self.df[column] = (self.df[column] / col_max) * max_scale
        return self

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def get_cleaned_data(self) -> pd.DataFrame:
        """Return the cleaned DataFrame."""
        logger.info("Returning cleaned data — %d rows", len(self.df))
        return self.df
