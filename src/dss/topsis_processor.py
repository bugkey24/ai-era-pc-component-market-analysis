"""TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)."""

from __future__ import annotations

import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger("dss.topsis")


class TOPSISProcessor:
    """Rank alternatives by their relative closeness to the ideal solution.

    Usage::

        topsis = TOPSISProcessor(
            decision_matrix=matrix,       # m alternatives × n criteria
            weights=np.array([...]),       # n weights from AHP
            criteria_types=["cost", "benefit", ...],
        )
        ranking = topsis.rank()
    """

    def __init__(
        self,
        decision_matrix: np.ndarray | list[list[float]],
        weights: np.ndarray | list[float],
        criteria_types: List[str],
    ) -> None:
        self.matrix = np.array(decision_matrix, dtype=float)
        self.weights = np.array(weights, dtype=float)
        self.criteria_types = criteria_types

        self.n_alternatives, self.n_criteria = self.matrix.shape

        if len(self.weights) != self.n_criteria:
            raise ValueError(
                f"Weight count ({len(self.weights)}) must match criteria count ({self.n_criteria})."
            )
        if len(self.criteria_types) != self.n_criteria:
            raise ValueError(
                f"criteria_types count ({len(self.criteria_types)}) must match criteria count."
            )
        for ct in self.criteria_types:
            if ct not in ("benefit", "cost"):
                raise ValueError(f"criteria_type must be 'benefit' or 'cost', got '{ct}'.")

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    def normalize_matrix(self) -> TOPSISProcessor:
        """Vector-normalise the decision matrix."""
        norms = np.sqrt((self.matrix ** 2).sum(axis=0))
        norms[norms == 0] = 1  # prevent division by zero
        self._normalized = self.matrix / norms
        return self

    def apply_weights(self) -> TOPSISProcessor:
        """Multiply normalised matrix by AHP weights."""
        self._weighted = self._normalized * self.weights
        return self

    def find_ideal_solutions(self) -> TOPSISProcessor:
        """Determine positive (A+) and negative (A-) ideal solutions."""
        self._ideal_pos = np.zeros(self.n_criteria)
        self._ideal_neg = np.zeros(self.n_criteria)

        for j in range(self.n_criteria):
            col = self._weighted[:, j]
            if self.criteria_types[j] == "benefit":
                self._ideal_pos[j] = col.max()
                self._ideal_neg[j] = col.min()
            else:  # cost
                self._ideal_pos[j] = col.min()
                self._ideal_neg[j] = col.max()
        return self

    def calculate_separation(self) -> TOPSISProcessor:
        """Compute Euclidean distance from A+ and A-."""
        self._d_plus = np.sqrt(((self._weighted - self._ideal_pos) ** 2).sum(axis=1))
        self._d_minus = np.sqrt(((self._weighted - self._ideal_neg) ** 2).sum(axis=1))
        return self

    def calculate_scores(self) -> TOPSISProcessor:
        """Relative closeness: C_i = D- / (D+ + D-)."""
        denom = self._d_plus + self._d_minus
        denom[denom == 0] = 1  # prevent division by zero
        self._scores = self._d_minus / denom
        return self

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def rank(self) -> pd.DataFrame:
        """Execute the full TOPSIS pipeline and return a ranked DataFrame."""
        self.normalize_matrix().apply_weights().find_ideal_solutions()
        self.calculate_separation().calculate_scores()

        df = pd.DataFrame({
            "Alternative": range(self.n_alternatives),
            "Score": self._scores.round(4),
            "Rank": self._scores.argsort()[::-1] + 1,
        })
        df = df.sort_values("Rank").reset_index(drop=True)
        logger.info("TOPSIS ranking:\n%s", df.head(10).to_string())
        return df

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def get_scores(self) -> np.ndarray:
        if not hasattr(self, "_scores"):
            raise ValueError("Call rank() first.")
        return self._scores

    def get_top_n(self, n: int = 5) -> pd.DataFrame:
        """Return the top-*n* ranked alternatives."""
        return self.rank().head(n)
