"""Abstract base class for platform review scrapers.

Reviews are a distinct entity from products (one product → many reviews),
so they get their own interface instead of overloading :class:`BaseScraper`.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from .retry import request_with_retry
from .robots_guard import RobotsGuard

# Schema fields every review scraper must produce (sentiment-phase contract):
#   product_id, review_id, review_text, rating, review_date,
#   helpful_count, user_name, source
REVIEW_SCHEMA = [
    "product_id",
    "review_id",
    "review_text",
    "rating",
    "review_date",
    "helpful_count",
    "user_name",
    "source",
]


class BaseReviewScraper(ABC):
    """Contract that every concrete review scraper must fulfil."""

    platform_name: str  # subclasses MUST set this
    robots_permitted: bool = True  # set False when robots.txt forbids reviews

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.headers = {
            "User-Agent": config.get(
                "user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
        }
        self.timeout: int = config.get("timeout", 10)
        self.retry_count: int = config.get("retry_count", 3)
        self.delay: float = config.get("delay", 2.0)
        self.logger = logging.getLogger(f"scraper.{self.platform_name}.reviews")
        self.robots_guard = RobotsGuard(config.get("robots", {}))

    # ------------------------------------------------------------------
    # Abstract methods — each platform MUST implement these
    # ------------------------------------------------------------------

    @abstractmethod
    def build_review_url(self, product_url: str) -> str:
        """Derive the first review-listing URL from a *product_url*."""

    @abstractmethod
    def fetch_page(self, url: str) -> str:
        """Return the raw page for *url* (HTML or rendered source)."""

    @abstractmethod
    def parse_review(self, element: Any) -> dict[str, Any]:
        """Extract a review dictionary from a single element."""

    @abstractmethod
    def get_next_page_url(self, current_url: str) -> str | None:
        """Return the URL of the next review page, or ``None`` when done."""

    def _extract_review_items(self, page: str) -> list[Any]:
        """Override in subclasses to pull review elements from *page*."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Retry with exponential backoff (methodology Phase 1, step 4)
    # ------------------------------------------------------------------

    def _request_with_retry(self, url: str) -> str:
        """GET *url* with exponential backoff; raises after *retry_count* tries."""
        return request_with_retry(
            url,
            headers=self.headers,
            timeout=self.timeout,
            retry_count=self.retry_count,
            delay=self.delay,
            logger=self.logger,
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def fetch_reviews(
        self, product_url: str, product_id: str = "", max_pages: int = 2
    ) -> pd.DataFrame:
        """Scrape review pages for one product and return a DataFrame.

        Rows are tagged with *product_id* and ``source``; duplicates within
        the same run (same text + date) are dropped.
        """
        self.logger.info("Fetching reviews for %s", product_url)
        reviews: list[dict[str, Any]] = []
        url = self.build_review_url(product_url)

        if not self.robots_guard.is_allowed(url):
            self.logger.warning(
                "robots.txt disallows %s — aborting %s review scrape",
                url,
                self.platform_name,
            )
            return pd.DataFrame(columns=REVIEW_SCHEMA)

        for page in range(1, max_pages + 1):
            self.logger.info("Review page %d/%d — %s", page, max_pages, url)
            try:
                page_html = self.fetch_page(url)
                for element in self._extract_review_items(page_html):
                    review = self.parse_review(element)
                    review["source"] = self.platform_name
                    if product_id:
                        review["product_id"] = product_id
                    reviews.append(review)
            except Exception as exc:
                self.logger.warning("Failed on review page %d: %s", page, exc)
                break

            next_url = self.get_next_page_url(url)
            if not next_url:
                break
            url = next_url
            time.sleep(max(self.delay, self.robots_guard.crawl_delay(url) or 0.0))

        df = pd.DataFrame(reviews)
        if not df.empty:
            df = df.drop_duplicates(subset=["review_text", "review_date"]).reset_index(drop=True)
        # Enforce the schema contract: exact column set and order
        df = df.reindex(columns=REVIEW_SCHEMA)
        self.logger.info("Collected %d reviews from %s", len(df), self.platform_name)
        return df
