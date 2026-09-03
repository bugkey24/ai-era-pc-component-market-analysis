"""Tests for the Phase 6 normalization predictor."""

import numpy as np
import pytest

from src.analysis import NormalizationPredictor
from src.analysis.normalization_predictor import DEFAULT_SCENARIOS, Scenario


class TestPredictNormalization:
    def test_matches_documented_formula(self):
        # docs/03: base_price + (price * investment_rate * 1.5) - (fab_completion * 0.8)
        result = NormalizationPredictor.predict_normalization(
            prices=1_000_000, investment_rate=1.0, fab_completion=0.0, base_price=500_000
        )
        assert result == pytest.approx(500_000 + 1_000_000 * 1.5)

    def test_fab_relief_reduces_price(self):
        high_relief = NormalizationPredictor.predict_normalization(1_000, 1.0, 1.0)
        no_relief = NormalizationPredictor.predict_normalization(1_000, 1.0, 0.0)
        assert high_relief < no_relief

    def test_accepts_vectorized_prices(self):
        result = NormalizationPredictor.predict_normalization(
            np.array([100.0, 200.0]), investment_rate=1.0, fab_completion=0.0
        )
        assert np.allclose(result, [150.0, 300.0])

    def test_scalar_in_scalar_out(self):
        result = NormalizationPredictor.predict_normalization(100.0, 1.0, 0.0)
        assert isinstance(result, float)

    def test_negative_price_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            NormalizationPredictor.predict_normalization(-5, 1.0, 0.0)

    def test_negative_driver_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            NormalizationPredictor.predict_normalization(100, -1.0, 0.0)


class TestScenarios:
    def test_default_probabilities_sum_to_one(self):
        total = sum(s.recovery_probability for s in DEFAULT_SCENARIOS)
        assert total == pytest.approx(1.0)

    def test_invalid_probabilities_raise(self):
        bad = tuple(
            Scenario(
                name=f"s{i}",
                description="d",
                timeframe="t",
                recovery_probability=0.5,
                recommendation="r",
                investment_multiplier=1.0,
                fab_relief=0.5,
            )
            for i in range(3)
        )
        with pytest.raises(ValueError, match="sum to 1.0"):
            NormalizationPredictor(scenarios=bad)

    def test_docs_semantics_bull_is_highest_price(self):
        """Bull = aggressive AI investment → highest projected price."""
        predictor = NormalizationPredictor()
        results = predictor.run_scenarios(current_price=10_000_000, base_price=5_000_000)
        assert results["bull"]["projected_price"] > results["base"]["projected_price"]
        assert results["base"]["projected_price"] > results["bear"]["projected_price"]

    def test_bear_normalizes_earliest(self):
        assert DEFAULT_SCENARIOS[2].timeframe == "2026-2027"  # bear
        assert DEFAULT_SCENARIOS[0].timeframe == "2028-2029"  # bull

    def test_all_scenarios_have_required_fields(self):
        predictor = NormalizationPredictor()
        results = predictor.run_scenarios(1_000_000)
        for name, info in results.items():
            assert name in {"bull", "base", "bear"}
            assert {
                "description",
                "timeframe",
                "recovery_probability",
                "projected_price",
                "recommendation",
            } <= set(info.keys())


class TestSummarize:
    def test_weighted_price_is_probability_weighted(self):
        predictor = NormalizationPredictor()
        summary = predictor.summarize(current_price=1_000_000, base_price=0)
        expected = sum(
            s["projected_price"] * s["recovery_probability"] for s in summary["scenarios"].values()
        )
        assert summary["expected_normalized_price"] == pytest.approx(expected, abs=0.01)

    def test_most_likely_is_base_case(self):
        predictor = NormalizationPredictor()
        summary = predictor.summarize(current_price=1_000_000)
        assert summary["most_likely_scenario"] == "base"  # 0.5 probability
        assert summary["most_likely_timeframe"] == "2027-2028"

    def test_summary_structure(self):
        predictor = NormalizationPredictor()
        summary = predictor.summarize(current_price=1_000_000)
        assert {
            "current_price",
            "expected_normalized_price",
            "most_likely_scenario",
            "most_likely_timeframe",
            "scenarios",
        } == set(summary.keys())
