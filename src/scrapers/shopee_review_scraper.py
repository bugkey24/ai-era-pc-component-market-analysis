"""Shopee review scraper — dynamic JS content via Selenium WebDriver.

Selectors are best-effort against Shopee's current markup and MUST be
re-validated against live pages before production use (see docs/04).
"""

from __future__ import annotations

import re
import time
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_review_scraper import BaseReviewScraper


class ShopeeReviewScraper(BaseReviewScraper):
    """Scrape product reviews from Shopee (requires Selenium)."""

    platform_name = "shopee"

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.driver: webdriver.Chrome | None = None

    def build_review_url(self, product_url: str) -> str:
        base = product_url.rstrip("/")
        return f"{base}?page=0&filter=0&by=default&limit=20"

    # ------------------------------------------------------------------
    # BaseReviewScraper interface
    # ------------------------------------------------------------------

    def fetch_page(self, url: str) -> str:
        if self.driver is None:
            self.driver = self._init_driver()
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".shopee-product-rating"))
        )
        self._scroll_to_load()
        return self.driver.page_source

    def get_next_page_url(self, current_url: str) -> str | None:
        match = re.search(r"[?&]page=(\d+)", current_url)
        if not match:
            return None
        return re.sub(r"page=\d+", f"page={int(match.group(1)) + 1}", current_url)

    def _extract_review_items(self, page: str) -> list[WebElement]:
        if self.driver is None:
            return []
        return self.driver.find_elements(By.CSS_SELECTOR, ".shopee-product-rating")

    def parse_review(self, element: WebElement) -> dict[str, Any]:
        return {
            "product_id": "",
            "review_text": self._safe_text(element, ".shopee-product-rating__text"),
            "rating": self._extract_rating(element),
            "review_date": self._safe_text(element, ".shopee-product-rating__time"),
            "helpful_count": self._extract_helpful(element),
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __del__(self) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _init_driver(self) -> webdriver.Chrome:
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument(f"--user-agent={self.headers.get('User-Agent', '')}")
        return webdriver.Chrome(options=opts)

    def _scroll_to_load(self) -> None:
        for _ in range(2):
            if self.driver is None:
                break
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

    @staticmethod
    def _safe_text(parent: WebElement, css: str) -> str:
        try:
            el = parent.find_element(By.CSS_SELECTOR, css)
            return el.get_attribute("textContent") or ""
        except Exception:
            return ""

    @staticmethod
    def _extract_rating(parent: WebElement) -> float:
        """Shopee encodes star rating as lit-star width % (20% per star)."""
        try:
            stars = parent.find_elements(By.CSS_SELECTOR, ".shopee-rating-stars__lit-star")
            if not stars:
                return 0.0
            full = len(stars)
            partial = parent.find_element(By.CSS_SELECTOR, ".shopee-rating-stars__lit")
            width = re.search(r"width:\s*([\d.]+)%", partial.get_attribute("style") or "")
            extra = float(width.group(1)) / 20 if width else 0.0
            return round(min(full - 1 + extra, 5.0), 1)
        except Exception:
            return 0.0

    @staticmethod
    def _extract_helpful(parent: WebElement) -> int:
        try:
            el = parent.find_element(By.CSS_SELECTOR, ".shopee-product-rating__like-count")
            digits = re.sub(r"[^0-9]", "", el.get_attribute("textContent") or "")
            return int(digits) if digits else 0
        except Exception:
            return 0
