"""Visualization module for the PC component market analysis."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
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
        show: bool = False,
    ) -> None:
        self.df = df
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.style = self._resolve_style(style)
        self.palette = palette
        self.figsize = figsize
        self.dpi = dpi
        self.show = show

        sns.set_theme(style=self.style)
        plt.rcParams.update({"figure.figsize": self.figsize, "figure.dpi": self.dpi})

    @staticmethod
    def _resolve_style(style: str) -> str:
        """Normalise legacy matplotlib style names to current seaborn styles."""
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

    def plot_price_trends(self, save: bool = True, show: bool | None = None) -> plt.Figure:
        """Subplots of price distribution per category (log scale for visibility)."""
        categories = sorted(self.df["category"].unique()) if "category" in self.df.columns else []
        if not categories:
            logger.warning("No 'category' column — skipping price_trends")
            return plt.figure()

        n = len(categories)
        fig, axes = plt.subplots(1, n, figsize=(5 * n, 5), sharey=False)
        if n == 1:
            axes = [axes]

        cat_colors = dict(zip(categories, sns.color_palette(self.palette, n)))

        for ax, cat in zip(axes, categories):
            cat_data = self.df[self.df["category"] == cat]["price"].dropna()
            if cat_data.empty:
                ax.set_title(f"{cat.upper()} (no data)", fontsize=12)
                continue

            sns.boxplot(y=cat_data, color=cat_colors[cat], ax=ax, width=0.5)
            sns.stripplot(y=cat_data, color="black", alpha=0.3, size=3, ax=ax)

            ax.set_title(cat.upper(), fontsize=13, fontweight="bold")
            ax.set_ylabel("Price (IDR)")
            ax.set_yscale("log")
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda x, _: f"Rp{x:,.0f}")
            )

        fig.suptitle("Price Distribution by Component Category", fontsize=15, y=1.02)
        self._finish(fig, "price_trends", save, show)
        return fig

    # ------------------------------------------------------------------
    # 2. Sentiment distribution
    # ------------------------------------------------------------------

    def plot_sentiment_distribution(
        self, save: bool = True, show: bool | None = None
    ) -> plt.Figure:
        """Pie chart of overall sentiment breakdown."""
        fig, ax = plt.subplots()
        if "sentiment" not in self.df.columns:
            logger.warning("No 'sentiment' column — skipping")
            return fig

        counts = self.df["sentiment"].value_counts()
        colors = sns.color_palette(self.palette, len(counts))
        ax.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=colors, startangle=90)
        ax.set_title("Sentiment Distribution", fontsize=14)
        self._finish(fig, "sentiment_distribution", save, show)
        return fig

    # ------------------------------------------------------------------
    # 3. Correlation heatmap
    # ------------------------------------------------------------------

    def plot_correlation_heatmap(
        self, columns: list[str] | None = None, save: bool = True, show: bool | None = None
    ) -> plt.Figure:
        """Heatmap of numeric column correlations."""
        fig, ax = plt.subplots(figsize=(10, 8))
        cols = columns or self.df.select_dtypes(include=np.number).columns.tolist()
        corr = self.df[cols].corr()
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(
            corr, mask=mask, annot=True, fmt=".2f", cmap=self.palette, linewidths=0.5, ax=ax
        )
        ax.set_title("Feature Correlation Matrix", fontsize=14)
        self._finish(fig, "correlation_heatmap", save, show)
        return fig

    # ------------------------------------------------------------------
    # 4. TOPSIS ranking bar chart
    # ------------------------------------------------------------------

    def plot_ranking_bar_chart(
        self,
        ranking_df: pd.DataFrame,
        save: bool = True,
        show: bool | None = None,
        top_n: int = 10,
        name_col: str = "name",
    ) -> plt.Figure:
        """Horizontal bar chart of TOPSIS scores — top N products by name."""
        fig, ax = plt.subplots(figsize=(12, 7))
        top = ranking_df.head(top_n).copy()

        if name_col in top.columns:
            top["label"] = top[name_col].apply(
                lambda s: (s[:55] + "...") if isinstance(s, str) and len(s) > 55 else str(s)
            )
        else:
            top["label"] = [f"#{i}" for i in range(1, len(top) + 1)]

        palette = sns.color_palette(self.palette, len(top))
        bars = ax.barh(
            top["label"][::-1],
            top["Score"][::-1],
            color=palette[::-1],
            edgecolor="white",
        )

        for bar, score in zip(bars, top["Score"][::-1]):
            ax.text(
                bar.get_width() + 0.005,
                bar.get_y() + bar.get_height() / 2,
                f"{score:.4f}",
                va="center",
                fontsize=9,
            )

        ax.set_title(f"TOPSIS Ranking — Top {top_n} Products", fontsize=14)
        ax.set_xlabel("Relative Closeness Score")
        ax.set_ylabel("")
        ax.set_xlim(0, top["Score"].max() * 1.12)
        self._finish(fig, "ranking_results", save, show)
        return fig

    # ------------------------------------------------------------------
    # 5. Word cloud
    # ------------------------------------------------------------------

    def plot_wordcloud(
        self,
        text_series: pd.Series,
        title: str = "Word Cloud",
        save: bool = True,
        show: bool | None = None,
    ) -> plt.Figure:
        """Generate a word cloud from a text series."""
        try:
            from wordcloud import WordCloud
        except ImportError:
            logger.warning("wordcloud not installed — skipping")
            return plt.figure()

        text = " ".join(text_series.dropna().astype(str))
        wc = WordCloud(
            width=1200, height=600, background_color="white", colormap="viridis", max_words=200
        ).generate(text)
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title(title, fontsize=14)
        self._finish(fig, "wordcloud", save, show)
        return fig

    # ------------------------------------------------------------------
    # 6. Radar chart (for AHP-TOPSIS scores)
    # ------------------------------------------------------------------

    def plot_radar_chart(
        self,
        labels: list[str],
        values: list[float],
        title: str = "Criteria Profile",
        save: bool = True,
        show: bool | None = None,
    ) -> plt.Figure:
        """Radar/spider chart for a single alternative's criteria profile."""
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values_closed = values + values[:1]
        angles_closed = angles + angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.fill(
            angles_closed, values_closed, alpha=0.25, color=sns.color_palette(self.palette, 1)[0]
        )
        ax.plot(angles_closed, values_closed, linewidth=2)
        ax.set_xticks(angles)
        ax.set_xticklabels(labels, fontsize=10)
        ax.set_title(title, fontsize=14, pad=20)
        self._finish(fig, "radar_chart", save, show)
        return fig

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _finish(
        self,
        fig: plt.Figure,
        name: str,
        save: bool,
        show: bool | None = None,
    ) -> None:
        fig.tight_layout()
        effective_show = self.show if show is None else show
        if save:
            path = self.output_dir / f"{name}.png"
            fig.savefig(path, dpi=self.dpi, bbox_inches="tight")
            logger.info("Saved %s", path)
        if effective_show:
            plt.show()  # render while the figure is still open (inline backends)
        plt.close(fig)

    def create_all_plots(self, show: bool | None = None) -> None:
        """Run the standard set of project visualisations."""
        logger.info("Generating all standard plots")
        self.plot_price_trends(show=show)
        self.plot_sentiment_distribution(show=show)
        self.plot_correlation_heatmap(show=show)
        logger.info("All plots generated")
