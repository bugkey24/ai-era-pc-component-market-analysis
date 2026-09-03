"""Tokopedia review scraper — parses the server-rendered Apollo cache.

Live finding (2026-09-03, product ``/review`` page): review markup carries
no stable test-ids and fields load progressively, but ``window.__cache``
contains the full review list — ``$ROOT_QUERY.productrevGetProductReviewList``
referencing ``reviewListPDPType{feedbackID}`` entities with message,
productRating, timestamps, and pagination metadata (``hasNext``,
``totalReviews``).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .base_review_scraper import BaseReviewScraper

logger = logging.getLogger("scraper.tokopedia.reviews")


class TokopediaReviewScraper(BaseReviewScraper):
    """Scrape product reviews from Tokopedia via the embedded cache JSON."""

    platform_name = "tokopedia"

    def build_review_url(self, product_url: str) -> str:
        base = product_url.rstrip("/").split("?")[0]
        return f"{base}/review"

    def fetch_page(self, url: str) -> str:
        return self._request_with_retry(url)

    def get_next_page_url(self, current_url: str) -> str | None:
        match = re.search(r"[?&]page=(\d+)", current_url)
        if match:
            return re.sub(r"page=\d+", f"page={int(match.group(1)) + 1}", current_url)
        sep = "&" if "?" in current_url else "?"
        return f"{current_url}{sep}page=2"

    # ------------------------------------------------------------------
    # BaseReviewScraper interface
    # ------------------------------------------------------------------

    def _extract_review_items(self, page: str) -> list[dict]:
        """Pull resolved review entities from ``window.__cache``."""
        cache = self._parse_cache(page)
        if cache is None:
            self.logger.warning("window.__cache not found on review page")
            return []
        return self._resolve_reviews(cache)

    def parse_review(self, element: dict) -> dict[str, Any]:
        """Map a resolved ``reviewListPDPType`` entity to the review schema."""
        user = element.get("_user") or {}
        likes = element.get("_likes") or {}
        helpful = likes.get("countLike") or likes.get("likeCount") or likes.get("count") or 0
        return {
            "review_id": str(element.get("feedbackID", "")),
            "review_text": (element.get("message") or "").strip(),
            "rating": float(element.get("productRating") or 0),
            "review_date": element.get("reviewCreateTimestamp", ""),
            "helpful_count": int(helpful),
            "user_name": user.get("name", ""),
        }

    # ------------------------------------------------------------------
    # Cache parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_cache(page: str) -> dict | None:
        match = re.search(r"window\.__cache\s*=\s*(\{.*?\})\s*;", page, re.DOTALL)
        if match is None:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            logger.warning("window.__cache JSON is malformed: %s", exc)
            return None

    def _resolve_reviews(self, cache: dict) -> list[dict]:
        """Resolve review entities (with user/likes) in ROOT_QUERY order."""
        list_key = next(
            (k for k in cache if "productrevGetProductReviewList" in k and ")." not in k),
            None,
        )
        if list_key is None:
            return []

        listing = cache[list_key]
        reviews: list[dict] = []
        for ref in listing.get("list", []):
            entity = self._resolve_ref(cache, ref)
            if entity is None:
                continue
            entity = {
                **entity,
                "_user": self._resolve_ref(cache, entity.get("user")),
                "_likes": self._resolve_ref(cache, entity.get("likeDislike")),
            }
            reviews.append(entity)

        logger.info(
            "Resolved %d reviews (totalReviews=%s, hasNext=%s)",
            len(reviews),
            listing.get("totalReviews"),
            listing.get("hasNext"),
        )
        return reviews

    @staticmethod
    def _resolve_ref(cache: dict, ref: Any, hops: int = 0) -> dict | None:
        """Follow Apollo id-references until a concrete dict resolves."""
        while isinstance(ref, dict) and ref.get("type") == "id" and ref.get("id") and hops < 10:
            ref = cache.get(ref["id"])
            hops += 1
        return ref if isinstance(ref, dict) else None
