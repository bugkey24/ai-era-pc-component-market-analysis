"""Tokopedia scraper — static HTML via Requests + BeautifulSoup."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup, Tag

from .base_scraper import BaseScraper


class TokopediaScraper(BaseScraper):
    """Scrape product listings from Tokopedia."""

    platform_name = "tokopedia"

    # ------------------------------------------------------------------
    # BaseScraper interface
    # ------------------------------------------------------------------

    def _build_search_url(self, category: str) -> str:
        base = self.config.get("base_url", "https://www.tokopedia.com/search")
        return f"{base}?q={category}&st=product"

    def fetch_page(self, url: str) -> str:
        resp = requests.get(url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

    def get_next_page_url(self, current_url: str) -> Optional[str]:
        """Increment the ``page`` query param, appending it on first use."""
        match = re.search(r"[?&]page=(\d+)", current_url)
        if match:
            return re.sub(r"page=\d+", f"page={int(match.group(1)) + 1}", current_url)
        # First pagination step — no page param yet
        sep = "&" if "?" in current_url else "?"
        return f"{current_url}{sep}page=2"

    def _extract_items(self, html: str) -> list[Tag]:
        soup = BeautifulSoup(html, "lxml")
        return soup.find_all("div", {"data-testid": "divProductWrapper"})

    def parse_product(self, element: Tag) -> Dict[str, Any]:
        return {
            "product_id": element.get("data-product-id", ""),
            "name": self._safe_text(element, "span", {"data-testid": "productName"}),
            "price": self._extract_price(element),
            "rating": self._extract_rating(element),
            "review_count": self._extract_review_count(element),
            "seller_name": self._safe_text(element, "span", {"data-testid": "linkStore"}),
            "location": self._safe_text(element, "span", {"data-testid": "linkLocation"}),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_text(parent: Tag, tag: str, attrs: dict) -> str:
        el = parent.find(tag, attrs)
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _extract_price(parent: Tag) -> int:
        raw = parent.find("span", {"data-testid": "productPrice"})
        if raw is None:
            return 0
        digits = re.sub(r"[^0-9]", "", raw.get_text())
        return int(digits) if digits else 0

    @staticmethod
    def _extract_rating(parent: Tag) -> float:
        el = parent.find("span", {"data-testid": "productRating"})
        if el is None:
            return 0.0
        text = el.get_text(strip=True)
        match = re.search(r"[\d.]+", text)
        return float(match.group()) if match else 0.0

    @staticmethod
    def _extract_review_count(parent: Tag) -> int:
        el = parent.find("span", {"data-testid": "productRating"})
        if el is None:
            return 0
        # review count is often in a sibling; fall back to 0
        return 0
