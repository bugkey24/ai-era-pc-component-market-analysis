"""Visualization module for the PC component market analysis."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — safe for Colab / headless
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger("visualization")

# ── Defaults (overridable via config) ────────────────────────────────
_STYLE = "seaborn-v0_8-darkgrid"
_PALETTE = "viridis"
_FIGSIZE = (12, 8)
_DPI = 150


class Visualizer:
    """Generate all project charts from a single DataFrame or result objects."""

    def __init__(
        self,
        df: pd.DataFrame,
        output_dir: str = "outputs/visualizations",
        style: str = _STYLE,
        palette: str = _PALETTE,
        figsize: tuple[int, int] = _FIGSIZE,
        dpi: int = _DPI,
    ) -> None:
        self.df = df
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.style = self._resolve_style(style)
        self.palette = palette
        self.figsize = figsize
        self.dpi = dpi

        sns.set_theme(style=self.style)
        plt.rcParams.update({"figure.figsize": self.figsize, "figure.dpi": self.dpi})

    @staticmethod
    def _resolve_style(style: str) -> str:
        """Normalise legacy matplotlib style names to current seaborn styles.

        Newer seaborn releases dropped the ``seaborn-v0_8-*`` aliases, so
        ``seaborn-v0_8-darkgrid`` → ``darkgrid``. Unknown styles fall back to
        ``darkgrid``.
        """
        if style in {"white", "dark", "whitegrid", "darkgrid", "ticks"}:
            return style
        for candidate in ("darkgrid", "whitegrid", "dark", "white", "ticks"):
            if style.endswith(candidate):
                return candidate
        logger.warning("Unknown style '%s' — falling back to 'darkgrid'", style)
        return "darkgrid"

    # ------------------------------------------------------------------
    # 1. Price trends
    # ------------------------------------------------------------------

    def plot_price_trends(self, save: bool = True) -> plt.Figure:
        """Box-plot of price distribution per category."""
        fig, ax = plt.subplots()
        categories = self.df["category"].unique() if "category" in self.df.columns else []
        if len(categories) == 0:
            logger.warning("No 'category' column — skipping price_trends")
            return fig

        sns.boxplot(data=self.df, x="category", y="price", hue="category",
                    palette=self.palette, legend=False, ax=ax)
        ax.set_title("Price Distribution by Component Category", fontsize=14)
        ax.set_xlabel("Category")
        ax.set_ylabel("Price (IDR)")
        self._finish(fig, "price_trends", save)
        return fig

    # ------------------------------------------------------------------
    # 2. Sentiment distribution
    # ------------------------------------------------------------------

    def plot_sentiment_distribution(self, save: bool = True) -> plt.Figure:
        """Pie chart of overall sentiment breakdown."""
        fig, ax = plt.subplots()
        if "sentiment" not in self.df.columns:
            logger.warning("No 'sentiment' column — skipping")
            return fig

        counts = self.df["sentiment"].value_counts()
        colors = sns.color_palette(self.palette, len(counts))
        ax.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=colors, startangle=90)
        ax.set_title("Sentiment Distribution", fontsize=14)
        self._finish(fig, "sentiment_distribution", save)
        return fig

    # ------------------------------------------------------------------
    # 3. Correlation heatmap
    # ------------------------------------------------------------------

    def plot_correlation_heatmap(self, columns: list[str] | None = None, save: bool = True) -> plt.Figure:
        """Heatmap of numeric column correlations."""
        fig, ax = plt.subplots(figsize=(10, 8))
        cols = columns or self.df.select_dtypes(include=np.number).columns.tolist()
        corr = self.df[cols].corr()
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap=self.palette,
                    linewidths=0.5, ax=ax)
        ax.set_title("Feature Correlation Matrix", fontsize=14)
        self._finish(fig, "correlation_heatmap", save)
        return fig

    # ------------------------------------------------------------------
    # 4. TOPSIS ranking bar chart
    # ------------------------------------------------------------------

    def plot_ranking_bar_chart(self, ranking_df: pd.DataFrame, save: bool = True) -> plt.Figure:
        """Horizontal bar chart of TOPSIS scores."""
        fig, ax = plt.subplots()
        top = ranking_df.head(10)
        sns.barplot(data=top, x="Score", y="Alternative", hue="Alternative",
                    palette="viridis", legend=False, ax=ax)
        ax.set_title("TOPSIS Ranking — Top Alternatives", fontsize=14)
        ax.set_xlabel("Relative Closeness Score")
        ax.set_ylabel("Alternative Index")
        self._finish(fig, "ranking_results", save)
        return fig

    # ------------------------------------------------------------------
    # 5. Word cloud
    # ------------------------------------------------------------------

    def plot_wordcloud(self, text_series: pd.Series, title: str = "Word Cloud", save: bool = True) -> plt.Figure:
        """Generate a word cloud from a text series."""
        try:
            from wordcloud import WordCloud
        except ImportError:
            logger.warning("wordcloud not installed — skipping")
            return plt.figure()

        text = " ".join(text_series.dropna().astype(str))
        wc = WordCloud(width=1200, height=600, background_color="white",
                       colormap="viridis", max_words=200).generate(text)
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title(title, fontsize=14)
        self._finish(fig, "wordcloud", save)
        return fig

    # ------------------------------------------------------------------
    # 6. Radar chart (for AHP-TOPSIS scores)
    # ------------------------------------------------------------------

    def plot_radar_chart(self, labels: list[str], values: list[float], title: str = "Criteria Profile", save: bool = True) -> plt.Figure:
        """Radar/spider chart for a single alternative's criteria profile."""
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values_closed = values + values[:1]
        angles_closed = angles + angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.fill(angles_closed, values_closed, alpha=0.25, color=sns.color_palette(self.palette, 1)[0])
        ax.plot(angles_closed, values_closed, linewidth=2)
        ax.set_xticks(angles)
        ax.set_xticklabels(labels, fontsize=10)
        ax.set_title(title, fontsize=14, pad=20)
        self._finish(fig, "radar_chart", save)
        return fig

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _finish(self, fig: plt.Figure, name: str, save: bool) -> None:
        fig.tight_layout()
        if save:
            path = self.output_dir / f"{name}.png"
            fig.savefig(path, dpi=self.dpi, bbox_inches="tight")
            logger.info("Saved %s", path)
        plt.close(fig)

    def create_all_plots(self) -> None:
        """Run the standard set of project visualisations."""
        logger.info("Generating all standard plots")
        self.plot_price_trends()
        self.plot_sentiment_distribution()
        self.plot_correlation_heatmap()
        logger.info("All plots generated")
