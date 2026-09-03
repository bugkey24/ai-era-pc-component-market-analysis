"""Tests for the Visualizer (headless Agg backend, tmp_path output)."""

import matplotlib

matplotlib.use("Agg")

import pandas as pd
import pytest

from src.visualization import Visualizer


@pytest.fixture
def viz_df():
    return pd.DataFrame(
        {
            "category": ["gpu", "gpu", "ram", "ram", "ssd", "ssd"],
            "price": [4_500_000, 4_200_000, 1_250_000, 1_100_000, 950_000, 480_000],
            "rating": [4.8, 4.6, 4.9, 4.7, 4.5, 4.3],
            "review_count": [120, 85, 40, 65, 30, 12],
            "sentiment": ["positive", "negative", "positive", "neutral", "positive", "negative"],
        }
    )


@pytest.fixture
def viz(viz_df, tmp_path):
    return Visualizer(viz_df, output_dir=str(tmp_path), dpi=72)


class TestPlots:
    def test_price_trends_saves_png(self, viz, tmp_path):
        viz.plot_price_trends()
        assert (tmp_path / "price_trends.png").exists()

    def test_sentiment_distribution_saves_png(self, viz, tmp_path):
        viz.plot_sentiment_distribution()
        assert (tmp_path / "sentiment_distribution.png").exists()

    def test_correlation_heatmap_saves_png(self, viz, tmp_path):
        viz.plot_correlation_heatmap()
        assert (tmp_path / "correlation_heatmap.png").exists()

    def test_ranking_bar_chart(self, viz, tmp_path):
        ranking = pd.DataFrame(
            {"Alternative": [0, 1, 2], "Score": [0.9, 0.7, 0.5], "Rank": [1, 2, 3]}
        )
        viz.plot_ranking_bar_chart(ranking)
        assert (tmp_path / "ranking_results.png").exists()

    def test_radar_chart(self, viz, tmp_path):
        viz.plot_radar_chart(labels=["price", "perf", "rating"], values=[0.8, 0.6, 0.9])
        assert (tmp_path / "radar_chart.png").exists()


class TestGracefulDegradation:
    def test_missing_column_does_not_crash(self, viz_df, tmp_path):
        viz = Visualizer(viz_df.drop(columns=["sentiment"]), output_dir=str(tmp_path))
        fig = viz.plot_sentiment_distribution()  # returns empty figure, no crash
        assert fig is not None

    def test_missing_category_does_not_crash(self, viz_df, tmp_path):
        viz = Visualizer(viz_df.drop(columns=["category"]), output_dir=str(tmp_path))
        fig = viz.plot_price_trends()
        assert fig is not None

    def test_create_all_plots_runs(self, viz):
        viz.create_all_plots()  # smoke test — must not raise
