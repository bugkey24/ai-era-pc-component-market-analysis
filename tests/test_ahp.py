"""Tests for AHPProcessor."""

import numpy as np
import pytest

from src.dss import AHPProcessor
from src.utils import load_config


class TestPairwiseMatrix:
    def test_accepts_valid_matrix(self, pairwise_matrix_consistent):
        ahp = AHPProcessor(["a", "b", "c"])
        ahp.build_pairwise_matrix(pairwise_matrix_consistent)
        assert ahp.pairwise_matrix.shape == (3, 3)

    def test_rejects_wrong_size(self):
        ahp = AHPProcessor(["a", "b", "c"])
        with pytest.raises(ValueError, match="[Mm]atrix must be"):
            ahp.build_pairwise_matrix([[1, 2], [2, 1]])

    def test_rejects_non_unit_diagonal(self):
        ahp = AHPProcessor(["a", "b"])
        with pytest.raises(ValueError, match="[Dd]iagonal"):
            ahp.build_pairwise_matrix([[2, 1], [1, 2]])


class TestWeights:
    def test_weights_match_saaty_example(self, pairwise_matrix_consistent):
        ahp = AHPProcessor(["a", "b", "c"])
        ahp.build_pairwise_matrix(pairwise_matrix_consistent).calculate_weights()
        expected = np.array([0.633, 0.260, 0.106])
        np.testing.assert_allclose(ahp.get_weights(), expected, atol=0.01)

    def test_weights_sum_to_one(self, pairwise_matrix_consistent):
        ahp = AHPProcessor(["a", "b", "c"])
        ahp.build_pairwise_matrix(pairwise_matrix_consistent).calculate_weights()
        assert ahp.get_weights().sum() == pytest.approx(1.0, abs=1e-6)

    def test_raises_without_matrix(self):
        ahp = AHPProcessor(["a", "b", "c"])
        with pytest.raises(ValueError, match="build_pairwise_matrix"):
            ahp.calculate_weights()

    def test_get_weights_raises_before_calculation(self, pairwise_matrix_consistent):
        ahp = AHPProcessor(["a", "b", "c"])
        ahp.build_pairwise_matrix(pairwise_matrix_consistent)
        with pytest.raises(ValueError, match="not calculated"):
            ahp.get_weights()


class TestConsistency:
    def test_consistent_matrix_has_low_cr(self, pairwise_matrix_consistent):
        ahp = AHPProcessor(["a", "b", "c"])
        ahp.build_pairwise_matrix(pairwise_matrix_consistent)
        ahp.calculate_weights().check_consistency()
        assert ahp.consistency_ratio < 0.1
        assert ahp.is_consistent()

    def test_inconsistent_matrix_has_high_cr(self, pairwise_matrix_inconsistent):
        ahp = AHPProcessor(["a", "b", "c"])
        ahp.build_pairwise_matrix(pairwise_matrix_inconsistent)
        ahp.calculate_weights().check_consistency()
        assert ahp.consistency_ratio > 0.1
        assert not ahp.is_consistent()

    def test_check_raises_without_weights(self, pairwise_matrix_consistent):
        ahp = AHPProcessor(["a", "b", "c"])
        ahp.build_pairwise_matrix(pairwise_matrix_consistent)
        with pytest.raises(ValueError, match="calculate_weights"):
            ahp.check_consistency()

    def test_is_consistent_raises_before_check(self, pairwise_matrix_consistent):
        ahp = AHPProcessor(["a", "b", "c"])
        ahp.build_pairwise_matrix(pairwise_matrix_consistent).calculate_weights()
        with pytest.raises(ValueError, match="check_consistency"):
            ahp.is_consistent()


class TestSummary:
    def test_summary_contains_all_fields(self, pairwise_matrix_consistent):
        ahp = AHPProcessor(["a", "b", "c"])
        ahp.build_pairwise_matrix(pairwise_matrix_consistent)
        ahp.calculate_weights().check_consistency()
        summary = ahp.summary()
        assert summary["criteria"] == ["a", "b", "c"]
        assert summary["is_consistent"] is True
        assert set(summary["weights"].keys()) == {"a", "b", "c"}


class TestConfigDrivenMatrix:
    """Regression: YAML parses ``1/3`` as a *string* — the processor must accept it."""

    def test_accepts_fraction_strings(self):
        ahp = AHPProcessor(["a", "b", "c"])
        ahp.build_pairwise_matrix([["1", "3", "5"], ["1/3", "1", "3"], ["1/5", "1/3", "1"]])
        ahp.calculate_weights().check_consistency()
        assert ahp.is_consistent()
        assert ahp.get_weights().sum() == pytest.approx(1.0, abs=1e-6)

    def test_accepts_real_config_matrix(self):
        config = load_config("config.yaml")
        dss = config["dss"]
        ahp = AHPProcessor(dss["criteria"])
        ahp.build_pairwise_matrix(dss["pairwise_matrix"])
        ahp.calculate_weights().check_consistency()
        assert ahp.is_consistent(), f"CR = {ahp.consistency_ratio}"
