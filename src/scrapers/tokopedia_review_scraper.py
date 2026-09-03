"""Tokopedia review scraper — static HTML via Requests + BeautifulSoup.

Selectors are best-effort against Tokopedia's current markup and MUST be
re-validated against live pages before production use (see docs/04).
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from .base_review_scraper import BaseReviewScraper


class TokopediaReviewScraper(BaseReviewScraper):
    """Scrape product reviews from Tokopedia."""

    platform_name = "tokopedia"

    def build_review_url(self, product_url: str) -> str:
        base = product_url.rstrip("/")
        return f"{base}/review"

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
        return soup.find_all("div", {"data-testid": "reviewItem"})

    def parse_review(self, element: Tag) -> dict[str, Any]:
        return {
            "product_id": element.get("data-product-id", ""),
            "review_text": self._safe_text(element, "div", {"data-testid": "lblReview"}),
            "rating": self._extract_rating(element),
            "review_date": self._safe_text(element, "span", {"data-testid": "lblReviewDate"}),
            "helpful_count": self._extract_helpful(element),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_text(parent: Tag, tag: str, attrs: dict) -> str:
        el = parent.find(tag, attrs)
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _extract_rating(element: Tag) -> float:
        el = element.find("span", {"data-testid": "ratingStar"})
        if el is None:
            return 0.0
        match = re.search(r"[\d.]+", el.get_text())
        return float(match.group()) if match else 0.0

    @staticmethod
    def _extract_helpful(element: Tag) -> int:
        el = element.find("button", {"data-testid": "btnHelpful"})
        if el is None:
            return 0
        digits = re.sub(r"[^0-9]", "", el.get_text())
        return int(digits) if digits else 0
