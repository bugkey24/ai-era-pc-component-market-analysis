"""Shopee scraper — dynamic JS content via Selenium WebDriver."""

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

from .base_scraper import BaseScraper


class ShopeeScraper(BaseScraper):
    """Scrape product listings from Shopee (requires Selenium)."""

    platform_name = "shopee"

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.driver: webdriver.Chrome | None = None

    # ------------------------------------------------------------------
    # BaseScraper interface
    # ------------------------------------------------------------------

    def _build_search_url(self, category: str) -> str:
        base = self.config.get("base_url", "https://shopee.co.id/search")
        return f"{base}?keyword={category}"

    def fetch_page(self, url: str) -> str:
        if self.driver is None:
            self.driver = self._init_driver()
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-testid="product-item"]')
            )
        )
        self._scroll_to_load()
        return self.driver.page_source

    def get_next_page_url(self, current_url: str) -> str | None:
        # Shopee loads products via infinite scroll; return None to stop.
        return None

    def _extract_items(self, html: str) -> list[WebElement]:
        if self.driver is None:
            return []
        return self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="product-item"]')

    def parse_product(self, element: WebElement) -> dict[str, Any]:
        return {
            "product_id": element.get_attribute("data-sqe") or "",
            "name": self._safe_attr(element, '[data-testid="nameOfProduct"]', "textContent"),
            "price": self._extract_price(element),
            "rating": self._extract_rating(element),
            "review_count": self._extract_review_count(element),
            "seller_name": self._safe_attr(element, ".seller-name", "textContent"),
            "location": self._safe_attr(element, ".location", "textContent"),
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
        for _ in range(3):
            if self.driver is None:
                break
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

    @staticmethod
    def _safe_attr(parent: WebElement, css: str, attr: str) -> str:
        try:
            el = parent.find_element(By.CSS_SELECTOR, css)
            return el.get_attribute(attr) or ""
        except Exception:
            return ""

    @staticmethod
    def _extract_price(parent: WebElement) -> int:
        try:
            el = parent.find_element(By.CSS_SELECTOR, '[data-testid="product-price"]')
            raw = el.get_attribute("textContent") or ""
        except Exception:
            return 0
        digits = re.sub(r"[^0-9]", "", raw)
        return int(digits) if digits else 0

    @staticmethod
    def _extract_rating(parent: WebElement) -> float:
        try:
            el = parent.find_element(By.CSS_SELECTOR, ".shopee-rating-stars__lit")
            style = el.get_attribute("style") or ""
            match = re.search(r"width:\s*([\d.]+)%", style)
            if match:
                return round(float(match.group(1)) / 20, 1)
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _extract_review_count(parent: WebElement) -> int:
        try:
            el = parent.find_element(By.CSS_SELECTOR, ".shopee-rating-normal__ Sold")
            raw = el.get_attribute("textContent") or ""
            digits = re.sub(r"[^0-9]", "", raw)
            return int(digits) if digits else 0
        except Exception:
            return 0
