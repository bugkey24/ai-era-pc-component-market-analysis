"""Pipeline orchestrator — ties all layers together."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.analysis import SentimentAnalyzer, StatisticalAnalyzer
from src.dss import AHPProcessor, TOPSISProcessor
from src.preprocessing import DataPreprocessor
from src.scrapers import get_scraper
from src.utils import load_config, setup_logger
from src.visualization import Visualizer

logger = logging.getLogger("pipeline")


class PipelineOrchestrator:
    """Execute the full data → analysis → DSS → visualisation pipeline.

    Usage::

        pipeline = PipelineOrchestrator("config.yaml")
        data, stats, ranking = pipeline.run_full_pipeline()
    """

    def __init__(self, config_path: str = "config.yaml") -> None:
        self.config = load_config(config_path)
        log_cfg = self.config.get("logging", {})
        setup_logger(
            name="pipeline",
            level=log_cfg.get("level", "INFO"),
            fmt=log_cfg.get("format"),
            log_file=log_cfg.get("file"),
        )
        self.data: pd.DataFrame | None = None
        self.stats: dict[str, Any] | None = None
        self.ranking: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def run_full_pipeline(self) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
        """Execute all phases in sequence and return (data, stats, ranking)."""
        logger.info("=" * 60)
        logger.info("PIPELINE START")
        logger.info("=" * 60)

        # Phase 1 — Scraping
        logger.info("Phase 1: Scraping")
        self.data = self._run_scraping()

        # Phase 2 — Preprocessing
        logger.info("Phase 2: Preprocessing")
        self.data = self._run_preprocessing()

        # Phase 3 — Statistical analysis
        logger.info("Phase 3: Statistical analysis")
        self.stats = self._run_statistics()

        # Phase 4 — Sentiment analysis
        logger.info("Phase 4: Sentiment analysis")
        self._run_sentiment()

        # Phase 5 — AHP-TOPSIS
        logger.info("Phase 5: DSS (AHP-TOPSIS)")
        self.ranking = self._run_dss()

        # Phase 6 — Visualisation
        logger.info("Phase 6: Visualisation")
        self._run_visualisation()

        logger.info("PIPELINE COMPLETE")
        return self.data, self.stats, self.ranking

    # ------------------------------------------------------------------
    # Individual phases
    # ------------------------------------------------------------------

    def _run_scraping(self) -> pd.DataFrame:
        scrap_cfg = self.config["scraping"]
        all_frames: list[pd.DataFrame] = []

        for platform_cfg in scrap_cfg["platforms"]:
            if not platform_cfg.get("enabled", True):
                logger.info("Skipping disabled platform: %s", platform_cfg["name"])
                continue

            scraper = get_scraper(platform_cfg["name"], {**scrap_cfg, **platform_cfg})
            for cat in scrap_cfg["categories"]:
                df = scraper.scrape(category=cat, max_pages=scrap_cfg.get("max_pages", 5))
                all_frames.append(df)

        if not all_frames:
            logger.warning("No data scraped — returning empty DataFrame")
            return pd.DataFrame()

        combined = pd.concat(all_frames, ignore_index=True)
        logger.info("Scraping complete — %d rows", len(combined))
        return combined

    def _run_preprocessing(self) -> pd.DataFrame:
        pre_cfg = self.config.get("preprocessing", {})
        return (
            DataPreprocessor(self.data)
            .clean_prices()
            .handle_missing(strategy=pre_cfg.get("handle_missing", "drop"))
            .extract_specifications()
            .remove_outliers(threshold=pre_cfg.get("outlier_threshold", 3.0))
            .get_cleaned_data()
        )

    def _run_statistics(self) -> dict:
        analyzer = StatisticalAnalyzer(self.data)
        analyzer.describe().correlation_matrix()
        summary = analyzer.get_summary()
        corrs = analyzer.get_correlations()
        return {
            "summary": summary.to_dict() if summary is not None else {},
            "correlations": corrs.to_dict() if corrs is not None else {},
            "price_by_category": analyzer.price_trend_by_category().to_dict(),
        }

    def _run_sentiment(self) -> None:
        sent_cfg = self.config.get("sentiment", {})
        sentiment = SentimentAnalyzer(
            language=sent_cfg.get("language", "indonesian"),
            max_features=sent_cfg.get("max_features", 5000),
        )
        # Training is deferred to when labelled review data is available
        # For now, store the untrained model for the pipeline to proceed
        self._sentiment_analyzer = sentiment

    def _run_dss(self) -> pd.DataFrame:
        dss_cfg = self.config.get("dss", {})
        criteria = dss_cfg["criteria"]

        # AHP
        ahp = AHPProcessor(criteria)
        ahp.build_pairwise_matrix(dss_cfg["pairwise_matrix"])
        ahp.calculate_weights().check_consistency()

        if not ahp.is_consistent():
            logger.warning("AHP consistency ratio exceeds 0.1 — review pairwise comparisons")

        weights = ahp.get_weights()

        # Build a decision matrix from the current data
        matrix = self._prepare_decision_matrix(criteria)
        if matrix.size == 0:
            logger.warning("Decision matrix is empty — skipping TOPSIS")
            return pd.DataFrame()

        topsis = TOPSISProcessor(matrix, weights, dss_cfg["criteria_types"])
        return topsis.rank()

    def _prepare_decision_matrix(self, criteria: list[str]) -> pd.DataFrame:
        """Map data columns to the criteria defined in config.

        Returns an m × n numpy array.
        """
        col_map = {
            "price": "price",
            "performance": "rating",  # proxy
            "rating": "weighted_rating",  # if available, else rating
            "seller_reliability": "seller_trust",
            "sentiment": "sentiment_score",  # placeholder
            "future_value": "price_per_gb",  # proxy
        }
        matrix_data: dict[str, pd.Series] = {}
        for c in criteria:
            src_col = col_map.get(c, c)
            if src_col in self.data.columns:
                matrix_data[c] = pd.to_numeric(self.data[src_col], errors="coerce").fillna(0)
            else:
                matrix_data[c] = pd.Series(0, index=self.data.index)

        if not matrix_data:
            return pd.DataFrame()
        return pd.DataFrame(matrix_data)

    def _run_visualisation(self) -> None:
        vis_cfg = self.config.get("visualization", {})
        viz = Visualizer(
            self.data,
            output_dir="outputs/visualizations",
            style=vis_cfg.get("style", "seaborn-v0_8-darkgrid"),
            palette=vis_cfg.get("palette", "viridis"),
            figsize=tuple(vis_cfg.get("figsize", [12, 8])),
            dpi=vis_cfg.get("dpi", 150),
        )
        viz.create_all_plots()
        if self.ranking is not None and not self.ranking.empty:
            viz.plot_ranking_bar_chart(self.ranking)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def save_results(self, output_dir: str = "outputs") -> None:
        """Persist processed data, rankings, and stats to disk."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        if self.data is not None:
            self.data.to_csv(out / "cleaned_data.csv", index=False)
        if self.ranking is not None:
            self.ranking.to_csv(out / "ranking.csv", index=False)
        if self.stats:
            import json

            # Convert numpy types for JSON serialisation
            def _convert(obj: Any) -> Any:
                if isinstance(obj, (int, float, str, bool)):
                    return obj
                if isinstance(obj, dict):
                    return {k: _convert(v) for k, v in obj.items()}
                if isinstance(obj, (list, tuple)):
                    return [_convert(v) for v in obj]
                return str(obj)

            with open(out / "statistics.json", "w", encoding="utf-8") as fh:
                json.dump(_convert(self.stats), fh, indent=2)

        logger.info("Results saved to %s", out)
