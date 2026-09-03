"""Blibli scraper — static HTML via Requests + BeautifulSoup."""

from __future__ import annotations

import re
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from .base_scraper import BaseScraper


class BlibliScraper(BaseScraper):
    """Scrape product listings from Blibli."""

    platform_name = "blibli"

    # ------------------------------------------------------------------
    # BaseScraper interface
    # ------------------------------------------------------------------

    def _build_search_url(self, category: str) -> str:
        base = self.config.get("base_url", "https://www.blibli.com/search")
        return f"{base}/{category}"

    def fetch_page(self, url: str) -> str:
        resp = requests.get(url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

    def get_next_page_url(self, current_url: str) -> str | None:
        match = re.search(r"[?&]page=(\d+)", current_url)
        if not match:
            return None
        next_page = int(match.group(1)) + 1
        if "page=" in current_url:
            return re.sub(r"page=\d+", f"page={next_page}", current_url)
        sep = "&" if "?" in current_url else "?"
        return f"{current_url}{sep}page={next_page}"

    def _extract_items(self, html: str) -> list[Tag]:
        soup = BeautifulSoup(html, "lxml")
        return soup.find_all("div", class_="product-card")

    def parse_product(self, element: Tag) -> dict[str, Any]:
        return {
            "product_id": element.get("data-pid", ""),
            "name": self._safe_text(element, ".product-card__name"),
            "price": self._extract_price(element),
            "rating": self._extract_rating(element),
            "review_count": self._extract_review_count(element),
            "seller_name": self._safe_text(element, ".product-card__store"),
            "location": self._safe_text(element, ".product-card__location"),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_text(parent: Tag, selector: str) -> str:
        el = parent.select_one(selector)
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _extract_price(parent: Tag) -> int:
        el = parent.select_one(".product-card__price")
        if el is None:
            return 0
        digits = re.sub(r"[^0-9]", "", el.get_text())
        return int(digits) if digits else 0

    @staticmethod
    def _extract_rating(parent: Tag) -> float:
        el = parent.select_one(".product-card__rating-value")
        if el is None:
            return 0.0
        match = re.search(r"[\d.]+", el.get_text())
        return float(match.group()) if match else 0.0

    @staticmethod
    def _extract_review_count(parent: Tag) -> int:
        el = parent.select_one(".product-card__review-count")
        if el is None:
            return 0
        digits = re.sub(r"[^0-9]", "", el.get_text())
        return int(digits) if digits else 0
