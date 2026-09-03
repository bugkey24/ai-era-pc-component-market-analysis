"""Price normalization prediction (methodology Phase 6).

Scenario modeling for when component prices may normalize, based on
historical semiconductor cycles, AI investment trends, and fab
construction timelines. See docs/03-methodology.md, Phase 6.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger("analysis.normalization")


@dataclass(frozen=True)
class Scenario:
    """One normalization scenario (bull / base / bear).

    In this project's terminology (docs/03 Phase 6, docs/07.4):
    - **bull** = a bull market for *sellers* — AI investment stays
      aggressive, prices keep rising, normalization lands latest.
    - **bear** = the AI bubble bursts — surplus fab capacity, prices
      normalize earliest.
    """

    name: str
    description: str
    timeframe: str
    recovery_probability: float
    recommendation: str
    investment_multiplier: float  # AI-investment intensity for this scenario
    fab_relief: float  # fab-capacity relief factor (0-1) for this scenario


# Baseline scenarios from docs/03 — probabilities must sum to 1.0
DEFAULT_SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        name="bull",
        description="AI investment continues aggressive",
        timeframe="2028-2029",
        recovery_probability=0.3,
        recommendation="Buy now, prices will continue to rise",
        investment_multiplier=1.6,
        fab_relief=0.1,
    ),
    Scenario(
        name="base",
        description="AI investment stabilizes, new fabs operational",
        timeframe="2027-2028",
        recovery_probability=0.5,
        recommendation="Hold for 6-12 months, then consider buying",
        investment_multiplier=1.0,
        fab_relief=0.5,
    ),
    Scenario(
        name="bear",
        description="AI bubble bursts, surplus capacity",
        timeframe="2026-2027",
        recovery_probability=0.2,
        recommendation="Wait if possible, buy if necessary",
        investment_multiplier=0.4,
        fab_relief=1.0,
    ),
)


class NormalizationPredictor:
    """Predict normalized prices under bull / base / bear scenarios."""

    def __init__(self, scenarios: tuple[Scenario, ...] = DEFAULT_SCENARIOS) -> None:
        total = sum(s.recovery_probability for s in scenarios)
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"Scenario probabilities must sum to 1.0 (got {total:.3f})")
        self.scenarios = scenarios

    # ------------------------------------------------------------------
    # Regression-based prediction (docs/03 Phase 6.C)
    # ------------------------------------------------------------------

    @staticmethod
    def predict_normalization(
        prices: float | np.ndarray,
        investment_rate: float,
        fab_completion: float,
        base_price: float = 0.0,
    ) -> float | np.ndarray:
        """Linear model with industry multipliers.

        ``normalized = base_price + (price * investment_rate * 1.5 - fab_completion * 0.8)``

        Parameters
        ----------
        prices : current price(s) in IDR
        investment_rate : AI-investment intensity multiplier (0 = frozen, 1 = current pace)
        fab_completion : normalized fab-capacity relief factor (0-1 scale)
        base_price : historical baseline price to anchor against
        """
        prices_arr = np.asarray(prices, dtype=float)
        if np.any(prices_arr < 0):
            raise ValueError("prices must be non-negative")
        if investment_rate < 0 or fab_completion < 0:
            raise ValueError("investment_rate and fab_completion must be non-negative")

        normalized = base_price + prices_arr * (investment_rate * 1.5) - fab_completion * 0.8
        return float(normalized) if np.isscalar(prices) else normalized

    # ------------------------------------------------------------------
    # Scenario analysis
    # ------------------------------------------------------------------

    def run_scenarios(
        self,
        current_price: float,
        base_price: float = 0.0,
    ) -> dict[str, dict]:
        """Evaluate every scenario and return per-scenario projections.

        Each scenario applies its own ``investment_multiplier`` and
        ``fab_relief`` to the regression model (see :class:`Scenario`).
        """
        results: dict[str, dict] = {}
        for scenario in self.scenarios:
            projected = self.predict_normalization(
                current_price,
                scenario.investment_multiplier,
                scenario.fab_relief,
                base_price,
            )
            results[scenario.name] = {
                "description": scenario.description,
                "timeframe": scenario.timeframe,
                "recovery_probability": scenario.recovery_probability,
                "projected_price": round(float(projected), 2),
                "recommendation": scenario.recommendation,
            }
        logger.info("Scenario analysis complete for price %.0f", current_price)
        return results

    def summarize(self, current_price: float, **kwargs: float) -> dict:
        """Probability-weighted summary across all scenarios."""
        per_scenario = self.run_scenarios(current_price, **kwargs)
        weighted_price = sum(
            s["projected_price"] * s["recovery_probability"] for s in per_scenario.values()
        )
        most_likely = max(per_scenario.items(), key=lambda kv: kv[1]["recovery_probability"])
        return {
            "current_price": current_price,
            "expected_normalized_price": round(weighted_price, 2),
            "most_likely_scenario": most_likely[0],
            "most_likely_timeframe": most_likely[1]["timeframe"],
            "scenarios": per_scenario,
        }
