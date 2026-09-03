"""Blibli review scraper — static HTML via Requests + BeautifulSoup.

Selectors are best-effort against Blibli's current markup and MUST be
re-validated against live pages before production use (see docs/04).
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from .base_review_scraper import BaseReviewScraper


class BlibliReviewScraper(BaseReviewScraper):
    """Scrape product reviews from Blibli."""

    platform_name = "blibli"

    def build_review_url(self, product_url: str) -> str:
        base = product_url.rstrip("/")
        return f"{base}/reviews"

    def fetch_page(self, url: str) -> str:
        return self._request_with_retry(url)

    def get_next_page_url(self, current_url: str) -> str | None:
        match = re.search(r"[?&]page=(\d+)", current_url)
        if match:
            return re.sub(r"page=\d+", f"page={int(match.group(1)) + 1}", current_url)
        sep = "&" if "?" in current_url else "?"
        return f"{current_url}{sep}page=2"

    def _extract_review_items(self, page: str) -> list[Tag]:
        soup = BeautifulSoup(page, "lxml")
        return soup.find_all("div", class_="review-card")

    def parse_review(self, element: Tag) -> dict[str, Any]:
        return {
            "product_id": element.get("data-pid", ""),
            "review_text": self._safe_text(element, ".review-card__text"),
            "rating": self._extract_rating(element),
            "review_date": self._safe_text(element, ".review-card__date"),
            "helpful_count": self._extract_helpful(element),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_text(parent: Tag, selector: str) -> str:
        el = parent.select_one(selector)
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _extract_rating(element: Tag) -> float:
        el = element.select_one(".review-card__rating-value")
        if el is None:
            return 0.0
        match = re.search(r"[\d.]+", el.get_text())
        return float(match.group()) if match else 0.0

    @staticmethod
    def _extract_helpful(element: Tag) -> int:
        el = element.select_one(".review-card__helpful-count")
        if el is None:
            return 0
        digits = re.sub(r"[^0-9]", "", el.get_text())
        return int(digits) if digits else 0
