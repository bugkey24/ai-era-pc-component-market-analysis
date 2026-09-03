"""Abstract base class for all platform scrapers."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd


class BaseScraper(ABC):
    """Contract that every concrete scraper must fulfil."""

    platform_name: str  # subclasses MUST set this

    def __init__(self, config: Dict[str, Any]) -> None:
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
        self.logger = logging.getLogger(f"scraper.{self.platform_name}")

    # ------------------------------------------------------------------
    # Abstract methods — each platform MUST implement these
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch_page(self, url: str) -> str:
        """Return the raw HTML of *url*."""

    @abstractmethod
    def parse_product(self, element: Any) -> Dict[str, Any]:
        """Extract a product dictionary from a single HTML element."""

    @abstractmethod
    def get_next_page_url(self, current_url: str) -> Optional[str]:
        """Return the URL of the next page, or ``None`` if no more pages."""

    @abstractmethod
    def _build_search_url(self, category: str) -> str:
        """Build the initial search URL for *category*."""

    # ------------------------------------------------------------------
    # Concrete helpers
    # ------------------------------------------------------------------

    def _extract_items(self, html: str) -> List[Any]:
        """Override in subclasses to pull product elements from *html*."""
        raise NotImplementedError

    def scrape(self, category: str, max_pages: int = 5) -> pd.DataFrame:
        """Run the full scrape loop and return a DataFrame of products."""
        self.logger.info("Starting scrape for %s on %s", category, self.platform_name)
        products: List[Dict[str, Any]] = []
        url = self._build_search_url(category)

        for page in range(1, max_pages + 1):
            self.logger.info("Page %d/%d — %s", page, max_pages, url)
            try:
                html = self.fetch_page(url)
                items = self._extract_items(html)
                for item in items:
                    product = self.parse_product(item)
                    product["source"] = self.platform_name
                    product["category"] = category
                    products.append(product)
            except Exception as exc:
                self.logger.warning("Failed on page %d: %s", page, exc)
                break

            next_url = self.get_next_page_url(url)
            if not next_url:
                break
            url = next_url
            time.sleep(self.delay)

        self.logger.info("Scraped %d products from %s", len(products), self.platform_name)
        return pd.DataFrame(products)
