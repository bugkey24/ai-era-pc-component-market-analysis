"""End-to-end integration test: PipelineOrchestrator with sample data.

Scraping is monkeypatched (no network); every downstream phase —
preprocessing, statistics, sentiment, AHP-TOPSIS, prediction,
visualisation — runs for real against the resulting DataFrame.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src import PipelineOrchestrator


@pytest.fixture
def orchestrator(tmp_path, monkeypatch):
    """A PipelineOrchestrator with a temp config and mocked scraping."""
    config = {
        "project": {"name": "test", "version": "0", "environment": "local"},
        "scraping": {
            "categories": ["gpu"],
            "max_pages": 1,
            "delay": 0.0,
            "retry_count": 1,
            "timeout": 1,
            "user_agent": "test",
            "platforms": [{"name": "tokopedia", "enabled": True, "method": "static"}],
        },
        "preprocessing": {"handle_missing": "drop", "outlier_threshold": 3.0},
        "sentiment": {"language": "indonesian", "max_features": 1000},
        "dss": {
            "criteria": [
                "price",
                "performance",
                "rating",
                "seller_reliability",
                "sentiment",
                "future_value",
            ],
            "criteria_types": ["cost", "benefit", "benefit", "benefit", "benefit", "benefit"],
            "pairwise_matrix": [
                [1, "1/3", 3, 5, 5, 3],
                [3, 1, 5, 7, 7, 5],
                ["1/3", "1/5", 1, 3, 3, "1/3"],
                ["1/5", "1/7", "1/3", 1, 1, "1/5"],
                ["1/5", "1/7", "1/3", 1, 1, "1/5"],
                ["1/3", "1/5", 3, 5, 5, 1],
            ],
        },
        "visualization": {"style": "darkgrid", "palette": "viridis", "dpi": 72},
        "logging": {"level": "WARNING", "file": None},
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w", encoding="utf-8") as fh:
        yaml.safe_dump(config, fh)

    # Run in tmp_path so outputs/logs never touch the repo
    monkeypatch.chdir(tmp_path)
    pipe = PipelineOrchestrator(str(config_file))

    # Patch the scraping phase — offline sample data instead of network
    def fake_scraping():
        rng = np.random.default_rng(42)
        rows = []
        for i in range(30):
            cap = rng.choice(["8GB", "16GB", "512GB", "1TB"])
            rows.append(
                {
                    "product_id": f"GPU-{i:03d}",
                    "name": f"GPU Model {i} {cap}",
                    "category": "gpu",
                    "price": f"Rp {int(8_000_000 * rng.uniform(0.6, 1.6)):,}".replace(",", "."),
                    "rating": round(rng.uniform(3.9, 5.0), 1),
                    "review_count": int(rng.integers(5, 400)),
                    "seller_rating": round(rng.uniform(4.0, 5.0), 1),
                    "seller_followers": int(rng.integers(10, 5000)),
                    "source": "tokopedia",
                }
            )
        return pd.DataFrame(rows)

    monkeypatch.setattr(pipe, "_run_scraping", fake_scraping)
    return pipe


class TestFullPipeline:
    def test_run_full_pipeline_returns_all_outputs(self, orchestrator):
        data, stats, ranking = orchestrator.run_full_pipeline()

        assert isinstance(data, pd.DataFrame) and len(data) > 0
        assert isinstance(stats, dict) and "summary" in stats
        assert isinstance(ranking, pd.DataFrame) and len(ranking) == 30
        # TOPSIS ranks are 1..n
        assert sorted(ranking["Rank"]) == list(range(1, 31))
        # Prediction phase ran
        assert orchestrator.prediction is not None
        assert orchestrator.prediction["most_likely_scenario"] == "base"

    def test_preprocessing_applied(self, orchestrator):
        data, _, _ = orchestrator.run_full_pipeline()
        assert pd.api.types.is_integer_dtype(data["price"])  # clean_prices ran
        assert "spec_capacity" in data.columns  # extract_specifications ran

    def test_save_results_writes_files(self, orchestrator):
        orchestrator.run_full_pipeline()
        orchestrator.save_results()

        out = Path("outputs")
        assert (out / "cleaned_data.csv").exists()
        assert (out / "ranking.csv").exists()
        assert (out / "statistics.json").exists()
        assert (out / "prediction.json").exists()

    def test_visualizations_written(self, orchestrator):
        orchestrator.run_full_pipeline()
        charts = Path("outputs/visualizations")
        assert (charts / "price_trends.png").exists()
        assert (charts / "correlation_heatmap.png").exists()
        assert (charts / "ranking_results.png").exists()
