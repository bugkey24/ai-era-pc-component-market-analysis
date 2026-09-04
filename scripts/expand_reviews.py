"""Expand the review snapshot with a larger, more diverse corpus.

Run this script from a residential IP after live scraping to rebuild
data/snapshot/reviews_tokopedia.csv with broader category coverage and
more varied sentiment.

Usage:
    python scripts/expand_reviews.py [--max-products N] [--max-pages N]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.scrapers import get_review_scraper
from src.utils import load_config

logger = logging.getLogger("expand_reviews")


def sample_product_ids(products: pd.DataFrame, n_per_category: int = 10) -> list[str]:
    """Select *n_per_category* products from each category, stratified by
    review_count (top quartile gets priority)."""
    sampled: list[str] = []
    for _cat, grp in products.groupby("category"):
        # Prefer products with reviews; fall back to random if none have reviews
        if grp["review_count"].sum() > 0:
            grp = grp.sort_values("review_count", ascending=False)
        sampled.extend(grp["product_id"].head(n_per_category).tolist())
    return sampled


def main(args: argparse.Namespace) -> None:
    config = load_config("config.yaml")
    scrap_cfg = config["scraping"]

    # Load existing products
    product_files = sorted(Path("data/snapshot").glob("*products*.csv"))
    if not product_files:
        product_files = sorted(Path("data/raw").glob("*products*.csv"))
    if not product_files:
        logger.error("No product CSVs found in data/snapshot/ or data/raw/")
        sys.exit(1)

    products = pd.concat([pd.read_csv(f) for f in product_files], ignore_index=True)
    product_ids = sample_product_ids(products, n_per_category=args.max_products)

    logger.info("Sampling %d products for review collection", len(product_ids))

    all_reviews: list[pd.DataFrame] = []
    scraper = get_review_scraper("tokopedia", {**scrap_cfg, **scrap_cfg["platforms"][0]})

    for pid in product_ids:
        row = products[products["product_id"] == pid].iloc[0]
        url = row.get("url", "")
        if not url:
            continue
        logger.info("Fetching reviews for product %s (%s)", pid, row.get("name", "")[:40])
        try:
            df = scraper.fetch_reviews(
                product_url=url, product_id=str(pid), max_pages=args.max_pages
            )
            if not df.empty:
                all_reviews.append(df)
        except Exception as exc:
            logger.warning("Failed for %s: %s", pid, exc)

    if not all_reviews:
        logger.error("No reviews collected")
        sys.exit(1)

    combined = pd.concat(all_reviews, ignore_index=True)
    # Keep existing reviews too
    existing = Path("data/snapshot/reviews_tokopedia.csv")
    if existing.exists():
        old = pd.read_csv(existing)
        combined = pd.concat([old, combined], ignore_index=True)

    combined = combined.drop_duplicates(subset=["review_id"], keep="last")
    combined.to_csv(existing, index=False)
    logger.info("Saved %d total reviews to %s", len(combined), existing)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expand review corpus")
    parser.add_argument("--max-products", type=int, default=10, help="Products per category")
    parser.add_argument("--max-pages", type=int, default=4, help="Review pages per product")
    main(parser.parse_args())
