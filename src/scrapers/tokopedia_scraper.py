"""Tokopedia scraper — parses the server-rendered Apollo cache.

Live-page findings (2026-09-03, /find/gpu & /find/rtx):

- Product cards are server-rendered but carry **no field-level test-ids**
  and obfuscated, rotating CSS class names — DOM parsing is brittle.
- The page embeds ``window.__cache``, an Apollo normalized JSON cache with
  full product entities (``searchProductV5Product{ID}``: name, url, rating,
  price incl. original, shop, category breadcrumb, meta.countReview).
  This is the sanctioned, zero-extra-request data source.
- Keyword caveat: searching the bare category word ("gpu") returns
  accessories and title-matched books. ``search_keywords`` in config maps
  categories to chip-level keywords ("rtx", "ddr5", "nvme"); a breadcrumb
  filter plus an accessory/laptop exclusion list handles the rest.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import requests

from .base_scraper import BaseScraper

logger = logging.getLogger("scraper.tokopedia")

# Apollo cache reference objects look like {"type": "id", "id": "..."}
_REF = "type"
_REF_ID = "id"

# Breadcrumb segments that identify the target component categories
# (verified against live pages 2026-09-03: /find/rtx, /find/ddr5, /find/nvme)
_CATEGORY_SEGMENTS = {
    "gpu": "vga-card",
    "ram": "ram-komputer",
    "ssd": "media-penyimpanan-data/ssd",
}

# Name fragments that mark accessories, peripherals, or whole systems —
# not the component itself (keyword search surfaces these heavily)
_EXCLUDE_PATTERNS = re.compile(
    r"holder|riser|bracket|stand|cable|kabel|extension|adapter|support"
    r"|laptop|notebook|mini pc|pc rakitan|desktop|all.in.one|monitor"
    r"|motherboard|mobo|enclosure|casing|heatsink|heat sink|baut"
    r"|ssd cooler|thickener|vga bracket",
    re.IGNORECASE,
)


class TokopediaScraper(BaseScraper):
    """Scrape product listings from Tokopedia via the embedded cache JSON."""

    platform_name = "tokopedia"

    # ------------------------------------------------------------------
    # BaseScraper interface
    # ------------------------------------------------------------------

    def _build_search_url(self, category: str) -> str:
        """Robots-compliant surface: ``Allow: /find/*?page``.

        The legacy ``/search?q=`` path is robots-DISALLOWED. Categories are
        searched via chip-level keywords (config ``search_keywords``)
        because bare category words return accessories and noise.
        """
        base = self.config.get("base_url", "https://www.tokopedia.com")
        keyword = self.config.get("search_keywords", {}).get(category, category)
        return f"{base}/find/{keyword}?page=1"

    def fetch_page(self, url: str) -> str:
        resp = requests.get(url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

    def get_next_page_url(self, current_url: str) -> str | None:
        match = re.search(r"[?&]page=(\d+)", current_url)
        if match:
            return re.sub(r"page=\d+", f"page={int(match.group(1)) + 1}", current_url)
        sep = "&" if "?" in current_url else "?"
        return f"{current_url}{sep}page=2"

    def _extract_items(self, html: str) -> list[dict[str, Any]]:
        """Pull resolved product dicts out of ``window.__cache``."""
        cache = self._parse_cache(html)
        if cache is None:
            self.logger.warning("window.__cache not found — page structure changed?")
            return []
        return self._resolve_products(cache, category=self._current_category)

    def parse_product(self, element: dict[str, Any]) -> dict[str, Any]:
        """Map a resolved cache entity to the project product schema."""
        shop = element.get("_shop") or {}
        price = element.get("_price") or {}
        meta = element.get("_meta") or {}
        original = self._parse_rupiah(price.get("original"))

        return {
            "product_id": str(element.get("id", "")),
            "name": element.get("name", ""),
            "url": (element.get("url") or "").split("?")[0],  # strip tracking params
            "price": int(price.get("number") or 0),
            "original_price": original,
            "discount": price.get("discountPercentage") or 0,
            "rating": float(element.get("rating") or 0.0),
            "review_count": int(meta.get("countReview") or 0),
            "seller_name": shop.get("name", ""),
            "location": shop.get("city", ""),
        }

    # ------------------------------------------------------------------
    # Cache parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_cache(html: str) -> dict | None:
        match = re.search(r"window\.__cache\s*=\s*(\{.*?\})\s*;", html, re.DOTALL)
        if match is None:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            logger.warning("window.__cache JSON is malformed: %s", exc)
            return None

    def _resolve_products(self, cache: dict, category: str = "") -> list[dict[str, Any]]:
        """Resolve product entities (with shop/price/meta) and filter noise."""
        seen_ids: set[str] = set()
        products: list[dict[str, Any]] = []

        for key, raw in cache.items():
            if not re.match(r"^searchProductV5Product\d+$", key):
                continue
            product_id = str(raw.get("id", ""))
            if product_id in seen_ids:  # cache holds duplicates
                continue

            entity = {
                **raw,
                "_price": self._resolve_ref(cache, raw.get("price")),
                "_shop": self._resolve_ref(cache, raw.get("shop")),
                "_meta": self._resolve_ref(cache, raw.get("meta")),
                "_category": self._resolve_ref(cache, raw.get("category")),
            }

            if not self._is_relevant(entity, category):
                continue

            seen_ids.add(product_id)
            products.append(entity)

        logger.info(
            "Resolved %d relevant products from %d cache entities",
            len(products),
            sum(1 for k in cache if k.startswith("searchProductV5Product")),
        )
        return products

    @staticmethod
    def _resolve_ref(cache: dict, ref: Any, hops: int = 0) -> dict | None:
        """Follow Apollo id-references until a concrete dict resolves."""
        while isinstance(ref, dict) and ref.get(_REF) == "id" and ref.get(_REF_ID) and hops < 10:
            ref = cache.get(ref[_REF_ID])
            hops += 1
        return ref if isinstance(ref, dict) else None

    def _is_relevant(self, entity: dict, category: str) -> bool:
        """Breadcrumb filter + accessory/laptop exclusion + text sanity."""
        name = entity.get("name") or ""
        if not name or _EXCLUDE_PATTERNS.search(name):
            return False

        expected = _CATEGORY_SEGMENTS.get(category)
        if expected is None:
            return True  # unknown category — keep (caller decides)

        cat = entity.get("_category") or {}
        breadcrumb = (cat.get("breadcrumb") or "").lower()
        return expected in breadcrumb

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_rupiah(raw: Any) -> int:
        """'Rp70.000' -> 70000."""
        if not raw:
            return 0
        digits = re.sub(r"[^0-9]", "", str(raw))
        return int(digits) if digits else 0
