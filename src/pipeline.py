"""Pipeline orchestrator — ties all layers together."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.analysis import (
    NormalizationPredictor,
    SentimentAnalyzer,
    StatisticalAnalyzer,
)
from src.dss import AHPProcessor, TOPSISProcessor
from src.preprocessing import DataPreprocessor, FeatureEngineer
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
        self.prediction: dict[str, Any] | None = None

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

        # Check data requirements
        self._check_data_requirements()

        # Phase 3 — Statistical analysis
        logger.info("Phase 3: Statistical analysis")
        self.stats = self._run_statistics()

        # Phase 4 — Sentiment analysis
        logger.info("Phase 4: Sentiment analysis")
        self._run_sentiment()

        # Phase 5 — AHP-TOPSIS
        logger.info("Phase 5: DSS (AHP-TOPSIS)")
        self.ranking = self._run_dss()

        # Phase 6 — Price normalization prediction (methodology Phase 6)
        logger.info("Phase 6: Normalization prediction")
        self._run_prediction()

        # Phase 7 — Visualisation
        logger.info("Phase 7: Visualisation")
        self._run_visualisation()

        logger.info("PIPELINE COMPLETE")
        return self.data, self.stats, self.ranking

    # ------------------------------------------------------------------
    # Individual phases
    # ------------------------------------------------------------------

    def _check_data_requirements(self) -> None:
        """Validate collected data against minimum quality thresholds."""
        req = self.config.get("data_requirements", {})
        if not req or self.data is None:
            return

        n_products = len(self.data)
        min_total = req.get("min_total_products", 150)
        if n_products < min_total:
            logger.warning(
                "Data below threshold: %d products (minimum %d). "
                "Increase max_pages or enable additional platforms.",
                n_products,
                min_total,
            )

        if "category" in self.data.columns:
            cat_counts = self.data["category"].value_counts()
            min_per_cat = req.get("min_products_per_category", 50)
            for cat, count in cat_counts.items():
                if count < min_per_cat:
                    logger.warning(
                        "Category '%s' has %d products (minimum %d)", cat, count, min_per_cat
                    )

        # Check review data
        review_files = sorted(Path("data/raw").glob("reviews_*.csv")) + sorted(
            Path("data/snapshot").glob("reviews_*.csv")
        )
        total_reviews = 0
        if review_files:
            for f in review_files:
                try:
                    rdf = pd.read_csv(f)
                    total_reviews += len(rdf)
                except Exception:
                    pass

        min_reviews = req.get("min_reviews", 50)
        if total_reviews < min_reviews:
            logger.warning(
                "Review corpus below threshold: %d reviews (minimum %d). "
                "Run expand_reviews.py or increase review_max_pages.",
                total_reviews,
                min_reviews,
            )

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
        cleaned = (
            DataPreprocessor(self.data)
            .clean_prices()
            .handle_missing(strategy=pre_cfg.get("handle_missing", "drop"))
            .extract_specifications()
            .nullify_unrated_ratings()
            .remove_outliers(threshold=pre_cfg.get("outlier_threshold", 3.0))
            .get_cleaned_data()
        )
        engineer = FeatureEngineer(cleaned)
        return (
            engineer.create_price_per_gb()
            .create_weighted_rating()
            .create_seller_trust_score()
            .create_discount_depth()
            .get_engineered_data()
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
        """Train the sentiment model when review data is available.

        Reviews are loaded from ``data/raw/reviews_*.csv`` (produced by the
        review scrapers). Labels are *weak supervision* derived from the
        review rating: >=4 → positive, <=2 → negative, else neutral. For
        production-grade accuracy, replace with hand-labelled reviews.
        """
        sent_cfg = self.config.get("sentiment", {})
        sentiment = SentimentAnalyzer(
            language=sent_cfg.get("language", "indonesian"),
            max_features=sent_cfg.get("max_features", 5000),
        )

        reviews = self._load_reviews()
        if reviews is None or len(reviews) < 10:
            logger.info(
                "No usable review data (need ≥10 rows in data/raw/reviews_*.csv) "
                "— sentiment model left untrained"
            )
            self._sentiment_analyzer = sentiment
            return

        texts = reviews["review_text"].fillna("").astype(str).tolist()
        ratings = pd.to_numeric(reviews.get("rating"), errors="coerce").fillna(3)
        labels = pd.cut(
            ratings,
            bins=[float("-inf"), 2, 4, 5],
            labels=["negative", "neutral", "positive"],
        ).astype(str)

        try:
            sentiment.train(texts, labels.tolist())
            # Aggregate per-product sentiment score into the product data
            if "product_id" in reviews.columns and self.data is not None:
                reviews["sentiment_score"] = sentiment.predict(texts)
                pos = (reviews["sentiment_score"] == "positive").astype(float)
                reviews["sentiment_score"] = pos
                per_product = reviews.groupby("product_id")["sentiment_score"].mean()
                self.data["sentiment_score"] = self.data["product_id"].map(per_product).fillna(0.0)
                logger.info("Per-product sentiment scores merged into product data")
        except ValueError as exc:
            logger.warning("Sentiment training skipped: %s", exc)

        self._sentiment_analyzer = sentiment

    def _load_reviews(self) -> pd.DataFrame | None:
        """Concatenate any ``data/raw/reviews_*.csv`` files, or return None."""
        review_files = sorted(Path("data/raw").glob("reviews_*.csv"))
        if not review_files:
            return None
        frames = [pd.read_csv(f) for f in review_files]
        combined = pd.concat(frames, ignore_index=True)
        logger.info("Loaded %d reviews from %d file(s)", len(combined), len(frames))
        return combined

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
        ranking = topsis.rank()

        # Enrich ranking with product metadata for readable output
        if self.data is not None and not ranking.empty and "name" in self.data.columns:
            idx = ranking["Alternative"].astype(int).values
            ranking["name"] = self.data.iloc[idx]["name"].values
            if "category" in self.data.columns:
                ranking["category"] = self.data.iloc[idx]["category"].values
            if "price" in self.data.columns:
                ranking["price"] = self.data.iloc[idx]["price"].values

        return ranking

    def _prepare_decision_matrix(self, criteria: list[str]) -> pd.DataFrame:
        """Map config criteria to available data columns.

        Documented proxies (see docs/compliance/final-validation):
        - ``performance`` → ``rating`` (no benchmark data)
        - ``seller_reliability`` → ``seller_tier`` (Tokopedia shop tier;
          falls back to ``seller_trust`` which is 0 without seller metrics)
        - ``sentiment`` → per-product positive-review rate (0 = no reviews)
        - ``future_value`` → ``price_per_gb`` (value-per-capacity proxy)
        """
        col_map = {
            "price": "price",
            "performance": "rating",
            "rating": "weighted_rating",
            "seller_reliability": "seller_tier",
            "sentiment": "sentiment_score",
            "future_value": "price_per_gb",
        }
        matrix_data: dict[str, pd.Series] = {}
        for c in criteria:
            src_col = col_map.get(c, c)
            if src_col not in self.data.columns and c == "seller_reliability":
                src_col = "seller_trust"  # pre-tier fallback
            if src_col in self.data.columns:
                matrix_data[c] = pd.to_numeric(self.data[src_col], errors="coerce").fillna(0)
            else:
                matrix_data[c] = pd.Series(0, index=self.data.index)

        if not matrix_data:
            return pd.DataFrame()
        return pd.DataFrame(matrix_data)

    def _run_prediction(self) -> None:
        """Run Phase 6 scenario analysis on the median category price."""
        predictor = NormalizationPredictor()
        if self.data is None or "price" not in self.data.columns or self.data.empty:
            logger.warning("No price data — skipping normalization prediction")
            self.prediction = None
            return

        median_price = float(pd.to_numeric(self.data["price"], errors="coerce").median())
        summary = predictor.summarize(median_price)
        self.prediction = summary
        logger.info(
            "Normalization: expected price %.0f, most likely %s (%s)",
            summary["expected_normalized_price"],
            summary["most_likely_scenario"],
            summary["most_likely_timeframe"],
        )

    def _run_visualisation(self) -> None:
        vis_cfg = self.config.get("visualization", {})
        viz = Visualizer(
            self.data,
            output_dir="outputs/visualizations",
            style=vis_cfg.get("style", "darkgrid"),
            palette=vis_cfg.get("palette", "viridis"),
            figsize=tuple(vis_cfg.get("figsize", [12, 8])),
            dpi=vis_cfg.get("dpi", 150),
        )
        viz.create_all_plots()
        if self.ranking is not None and not self.ranking.empty:
            viz.plot_ranking_bar_chart(self.ranking, name_col="name")

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
            if self.prediction:
                with open(out / "prediction.json", "w", encoding="utf-8") as fh:
                    json.dump(_convert(self.prediction), fh, indent=2)

        logger.info("Results saved to %s", out)
