"""Tests for TOPSISProcessor."""

import numpy as np
import pandas as pd
import pytest

from src.dss import TOPSISProcessor


class TestValidation:
    def test_rejects_weight_count_mismatch(self, topsis_known_case):
        with pytest.raises(ValueError, match="Weight count"):
            TOPSISProcessor(topsis_known_case["matrix"], [0.5, 0.3, 0.2], ["cost", "benefit"])

    def test_rejects_invalid_criteria_type(self, topsis_known_case):
        with pytest.raises(ValueError, match="benefit.*cost"):
            TOPSISProcessor(topsis_known_case["matrix"], [0.5, 0.5], ["cost", "nonsense"])

    def test_rejects_type_count_mismatch(self, topsis_known_case):
        with pytest.raises(ValueError, match="criteria_types"):
            TOPSISProcessor(topsis_known_case["matrix"], [0.5, 0.5], ["cost"])


class TestRanking:
    def test_known_case_ranking_order(self, topsis_known_case):
        topsis = TOPSISProcessor(
            topsis_known_case["matrix"],
            topsis_known_case["weights"],
            topsis_known_case["criteria_types"],
        )
        ranking = topsis.rank()
        # Rank 1 should be alternative 0 (cheap + decent rating)
        assert ranking.iloc[0]["Alternative"] == topsis_known_case["expected_order"][0]
        assert ranking.iloc[1]["Alternative"] == topsis_known_case["expected_order"][1]
        assert ranking.iloc[2]["Alternative"] == topsis_known_case["expected_order"][2]

    def test_known_case_top_score(self, topsis_known_case):
        topsis = TOPSISProcessor(
            topsis_known_case["matrix"],
            topsis_known_case["weights"],
            topsis_known_case["criteria_types"],
        )
        top_score = topsis.rank().iloc[0]["Score"]
        assert top_score == pytest.approx(topsis_known_case["expected_top_score"], abs=0.02)

    def test_scores_bounded_0_to_1(self, topsis_known_case):
        topsis = TOPSISProcessor(
            topsis_known_case["matrix"],
            topsis_known_case["weights"],
            topsis_known_case["criteria_types"],
        )
        topsis.rank()
        scores = topsis.get_scores()
        assert np.all(scores >= 0) and np.all(scores <= 1)

    def test_rank_column_is_sequential(self, topsis_known_case):
        topsis = TOPSISProcessor(
            topsis_known_case["matrix"],
            topsis_known_case["weights"],
            topsis_known_case["criteria_types"],
        )
        ranking = topsis.rank()
        assert list(ranking["Rank"]) == [1, 2, 3]

    def test_rank_ordering_is_monotonic_in_score(self, topsis_known_case):
        # Regression: Rank must follow Score ordering. The old implementation
        # assigned the descending-order permutation itself as ranks, which
        # scrambles Rank vs Score on non-trivial inputs.
        topsis = TOPSISProcessor(
            topsis_known_case["matrix"],
            topsis_known_case["weights"],
            topsis_known_case["criteria_types"],
        )
        ranking = topsis.rank()
        assert ranking["Score"].is_monotonic_decreasing

    def test_best_alternative_not_in_first_row_still_wins(self):
        # Alternative 1 (expensive, high benefit) wins under benefit-heavy
        # weights despite sitting mid-matrix — guards the inverse-permutation
        # rank assignment
        topsis = TOPSISProcessor(
            [[2, 3], [10, 9], [6, 5]],
            [0.3, 0.7],
            ["cost", "benefit"],
        )
        ranking = topsis.rank()
        assert ranking.iloc[0]["Alternative"] == 1
        assert ranking.iloc[0]["Score"] == ranking["Score"].max()

    def test_perfect_alternative_wins(self):
        # Alt 0 is best on BOTH criteria (cheap cost, high benefit)
        topsis = TOPSISProcessor(
            [[1, 10], [10, 1]],
            [0.5, 0.5],
            ["cost", "benefit"],
        )
        ranking = topsis.rank()
        assert ranking.iloc[0]["Alternative"] == 0


class TestEdgeCases:
    def test_zero_column_norm_does_not_crash(self):
        # A column of all zeros would produce norm=0
        topsis = TOPSISProcessor(
            [[0, 5], [0, 3]],
            [0.5, 0.5],
            ["cost", "benefit"],
        )
        ranking = topsis.rank()
        assert len(ranking) == 2

    def test_identical_alternatives_give_equal_scores(self):
        topsis = TOPSISProcessor(
            [[5, 5], [5, 5]],
            [0.5, 0.5],
            ["benefit", "benefit"],
        )
        topsis.rank()
        scores = topsis.get_scores()
        assert scores[0] == pytest.approx(scores[1])

    def test_get_scores_raises_before_rank(self, topsis_known_case):
        topsis = TOPSISProcessor(
            topsis_known_case["matrix"],
            topsis_known_case["weights"],
            topsis_known_case["criteria_types"],
        )
        with pytest.raises(ValueError, match="rank"):
            topsis.get_scores()

    def test_get_top_n(self, topsis_known_case):
        topsis = TOPSISProcessor(
            topsis_known_case["matrix"],
            topsis_known_case["weights"],
            topsis_known_case["criteria_types"],
        )
        top = topsis.get_top_n(2)
        assert isinstance(top, pd.DataFrame)
        assert len(top) == 2
