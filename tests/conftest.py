"""Shared pytest fixtures for the test suite."""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project root is importable (package not pip-installed yet)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_products() -> pd.DataFrame:
    """A small realistic product DataFrame for preprocessing tests."""
    return pd.DataFrame(
        {
            "product_id": ["P1", "P2", "P3", "P4", "P5"],
            "name": [
                "NVIDIA RTX 4060 8GB DDR5",
                "AMD RX 7600 8GB",
                "Corsair 16GB DDR5-5600",
                "Samsung 980 1TB NVMe SSD",
                "Kingston 512GB NVMe",
            ],
            "category": ["gpu", "gpu", "ram", "ssd", "ssd"],
            "price": ["Rp 4.500.000", "Rp 4.200.000", "Rp 1.250.000", "Rp 950.000", "Rp 480.000"],
            "rating": [4.8, 4.6, 4.9, 4.7, 4.5],
            "review_count": [120, 85, 40, 65, 30],
            "seller_rating": [4.9, 4.7, 5.0, 4.8, 4.6],
            "seller_followers": [1500, 300, 50, 900, 100],
            "source": ["tokopedia", "tokopedia", "shopee", "blibli", "blibli"],
        }
    )


@pytest.fixture
def pairwise_matrix_consistent() -> list[list[float]]:
    """Canonical Saaty 3x3 matrix — CR ≈ 0.03 (consistent)."""
    return [
        [1, 3, 5],
        [1 / 3, 1, 3],
        [1 / 5, 1 / 3, 1],
    ]


@pytest.fixture
def pairwise_matrix_inconsistent() -> list[list[float]]:
    """Cyclic contradictory matrix — CR >> 0.1 (inconsistent)."""
    return [
        [1, 9, 1 / 9],
        [1 / 9, 1, 9],
        [9, 1 / 9, 1],
    ]


@pytest.fixture
def topsis_known_case() -> dict:
    """Hand-computed TOPSIS case: 3 alternatives, 2 criteria.

    Criteria: price (cost, w=0.6), rating (benefit, w=0.4)
    Expected scores: A1≈0.813 > A3≈0.500 > A2≈0.187
    """
    return {
        "matrix": [
            [100, 4.0],
            [200, 5.0],
            [150, 4.5],
        ],
        "weights": [0.6, 0.4],
        "criteria_types": ["cost", "benefit"],
        "expected_order": [0, 2, 1],
        "expected_top_score": 0.81,
    }
