"""Analytic Hierarchy Process (AHP) processor."""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np

logger = logging.getLogger("dss.ahp")

# Random Index table (Saaty, 1980) — maps n_criteria → RI value
_RI_TABLE = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}


class AHPProcessor:
    """Compute criteria weights via the Analytic Hierarchy Process.

    Usage::

        ahp = AHPProcessor(criteria=["price", "performance", "rating"])
        ahp.build_pairwise_matrix(matrix)
        ahp.calculate_weights().check_consistency()
        assert ahp.is_consistent()
        weights = ahp.get_weights()
    """

    def __init__(self, criteria: List[str]) -> None:
        self.criteria = criteria
        self.n = len(criteria)
        self.pairwise_matrix: Optional[np.ndarray] = None
        self.weights: Optional[np.ndarray] = None
        self.consistency_ratio: Optional[float] = None
        self.lambda_max: Optional[float] = None

    # ------------------------------------------------------------------
    # Matrix construction
    # ------------------------------------------------------------------

    def build_pairwise_matrix(self, comparisons: list[list[float]]) -> AHPProcessor:
        """Set the pairwise comparison matrix (n × n)."""
        if len(comparisons) != self.n or any(len(row) != self.n for row in comparisons):
            raise ValueError(
                f"Matrix must be {self.n}×{self.n}. Got {len(comparisons)} rows."
            )
        self.pairwise_matrix = np.array(comparisons, dtype=float)
        # Validate Saaty scale: diagonal must be 1
        diag = np.diag(self.pairwise_matrix)
        if not np.allclose(diag, 1.0):
            raise ValueError("Diagonal of the pairwise matrix must be all 1.")
        return self

    # ------------------------------------------------------------------
    # Weight calculation
    # ------------------------------------------------------------------

    def calculate_weights(self) -> AHPProcessor:
        """Calculate priority weights using the column-normalisation method."""
        if self.pairwise_matrix is None:
            raise ValueError("No pairwise matrix. Call build_pairwise_matrix() first.")

        col_sums = self.pairwise_matrix.sum(axis=0)
        if np.any(col_sums == 0):
            raise ValueError("Column sums contain zero — matrix is invalid.")

        normalised = self.pairwise_matrix / col_sums
        self.weights = normalised.mean(axis=1)

        # Also compute lambda_max for consistency check
        weighted_sum = self.pairwise_matrix @ self.weights
        self.lambda_max = float((weighted_sum / self.weights).mean())

        logger.info("Weights: %s", dict(zip(self.criteria, self.weights.round(4))))
        return self

    # ------------------------------------------------------------------
    # Consistency check
    # ------------------------------------------------------------------

    def check_consistency(self) -> AHPProcessor:
        """Compute Consistency Ratio (CR).  CR < 0.1 is acceptable."""
        if self.weights is None:
            raise ValueError("Weights not calculated. Call calculate_weights() first.")
        if self.lambda_max is None:
            raise ValueError("lambda_max not computed.")

        ci = (self.lambda_max - self.n) / (self.n - 1) if self.n > 1 else 0.0
        ri = _RI_TABLE.get(self.n, 1.45)
        self.consistency_ratio = ci / ri if ri > 0 else 0.0

        logger.info("CR = %.4f (%s)", self.consistency_ratio,
                     "consistent" if self.is_consistent() else "INCONSISTENT")
        return self

    def is_consistent(self, threshold: float = 0.1) -> bool:
        """Return ``True`` if CR < *threshold*."""
        if self.consistency_ratio is None:
            raise ValueError("Consistency not checked. Call check_consistency() first.")
        return self.consistency_ratio < threshold

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def get_weights(self) -> np.ndarray:
        if self.weights is None:
            raise ValueError("Weights not calculated.")
        return self.weights

    def get_criteria_weights_dict(self) -> dict[str, float]:
        if self.weights is None:
            raise ValueError("Weights not calculated.")
        return dict(zip(self.criteria, self.weights.round(4)))

    def summary(self) -> dict:
        """Return a human-readable summary dict."""
        return {
            "criteria": self.criteria,
            "weights": self.get_criteria_weights_dict() if self.weights is not None else {},
            "lambda_max": round(self.lambda_max, 4) if self.lambda_max is not None else None,
            "consistency_ratio": round(self.consistency_ratio, 4) if self.consistency_ratio is not None else None,
            "is_consistent": self.is_consistent() if self.consistency_ratio is not None else None,
        }
