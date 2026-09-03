"""Tests for review scrapers — offline, network mocked or absent."""

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.scrapers import (
    REVIEW_SCHEMA,
    REVIEW_SCRAPER_REGISTRY,
    BaseReviewScraper,
    BlibliReviewScraper,
    ShopeeReviewScraper,
    TokopediaReviewScraper,
    get_review_scraper,
)


def _tokopedia_review_cache() -> dict:
    """Synthetic review-page cache mirroring the live Apollo structure."""
    return {
        "$ROOT_QUERY.productrevGetProductReviewList("
        '{"filterBy":"","limit":10,"page":1,"productID":"TPD-001","sortBy":"informative_score desc"})': {
            "productID": "TPD-001",
            "list": [
                {"type": "id", "id": "reviewListPDPType9001", "typename": "reviewListPDPType"},
                {"type": "id", "id": "reviewListPDPType9002", "typename": "reviewListPDPType"},
            ],
            "hasNext": False,
            "totalReviews": 2,
        },
        "reviewListPDPType9001": {
            "feedbackID": "9001",
            "message": "barang bagus sekali, cepat sampai",
            "productRating": 5,
            "reviewCreateTimestamp": "5 hari lalu",
            "user": {"type": "id", "id": "$reviewListPDPType9001.user"},
            "likeDislike": {"type": "id", "id": "$reviewListPDPType9001.likeDislike"},
        },
        "$reviewListPDPType9001.user": {
            "name": "Andi",
            "__typename": "reviewReviewUserPDPType",
        },
        "$reviewListPDPType9001.likeDislike": {
            "countLike": 3,
            "__typename": "reviewLikeDislikePDPType",
        },
        "reviewListPDPType9002": {
            "feedbackID": "9002",
            "message": "barang jelek, kecewa",
            "productRating": 1,
            "reviewCreateTimestamp": "4 hari lalu",
            "user": None,
            "likeDislike": None,
        },
    }


def _tokopedia_reviews_html() -> str:
    return (
        "<html><script>window.__cache = "
        + json.dumps(_tokopedia_review_cache())
        + ";</script></html>"
    )


BLIBLI_REVIEWS_HTML = """
<div class="review-card" data-pid="BLI-100">
    <div class="review-card__text">kualitas oke worth it</div>
    <div class="review-card__rating-value">4.5</div>
    <div class="review-card__date">01 Sep 2026</div>
    <div class="review-card__helpful-count">(12)</div>
</div>
"""


@pytest.fixture
def review_config():
    return {
        "user_agent": "test-agent",
        "timeout": 5,
        "retry_count": 3,
        "delay": 0.0,
        "robots": {"enabled": False},  # compliance behaviour tested in test_robots_guard.py
    }


class _FakeWebElement:
    """Minimal WebElement stand-in for offline Shopee parsing tests."""

    def __init__(self, children: dict[str, "_FakeWebElement"] | None = None):
        self._children = children or {}

    def find_element(self, by, selector):
        return self._children[selector]

    def get_attribute(self, attr):
        return None


class TestFactory:
    def test_review_registry_contains_all_platforms(self):
        assert set(REVIEW_SCRAPER_REGISTRY.keys()) == {"tokopedia", "shopee", "blibli"}

    def test_get_review_scraper_returns_correct_type(self, review_config):
        assert isinstance(get_review_scraper("tokopedia", review_config), TokopediaReviewScraper)
        assert isinstance(get_review_scraper("shopee", review_config), ShopeeReviewScraper)
        assert isinstance(get_review_scraper("blibli", review_config), BlibliReviewScraper)

    def test_unknown_platform_raises(self, review_config):
        with pytest.raises(ValueError, match="Unknown platform"):
            get_review_scraper("amazon", review_config)

    def test_base_review_scraper_is_abstract(self, review_config):
        with pytest.raises(TypeError):
            BaseReviewScraper(review_config)  # type: ignore[abstract]

    def test_schema_fields_documented(self):
        assert set(REVIEW_SCHEMA) >= {"product_id", "review_text", "rating", "source"}

    def test_blibli_reviews_marked_robots_blocked(self, review_config):
        # Blibli robots disallows /p/*/pr* — the scraper must be gated off
        scraper = get_review_scraper("blibli", review_config)
        assert scraper.robots_permitted is False

    def test_tokopedia_reviews_robots_permitted(self, review_config):
        # Tokopedia robots explicitly allows /*/review
        scraper = get_review_scraper("tokopedia", review_config)
        assert scraper.robots_permitted is True


class TestTokopediaReviews:
    def test_parses_reviews(self, review_config):
        scraper = TokopediaReviewScraper(review_config)
        items = scraper._extract_review_items(_tokopedia_reviews_html())
        assert len(items) == 2
        first = scraper.parse_review(items[0])
        assert first["review_id"] == "9001"
        assert first["review_text"] == "barang bagus sekali, cepat sampai"
        assert first["rating"] == 5.0
        assert first["review_date"] == "5 hari lalu"
        assert first["helpful_count"] == 3
        assert first["user_name"] == "Andi"

    def test_missing_fields_default_safely(self, review_config):
        scraper = TokopediaReviewScraper(review_config)
        item = scraper._extract_review_items(_tokopedia_reviews_html())[1]
        parsed = scraper.parse_review(item)
        assert parsed["helpful_count"] == 0
        assert parsed["user_name"] == ""
        assert parsed["rating"] == 1.0

    def test_build_review_url(self, review_config):
        scraper = TokopediaReviewScraper(review_config)
        url = scraper.build_review_url("https://tokopedia.com/shop/gpu-x")
        assert url.endswith("/gpu-x/review")


class TestBlibliReviews:
    def test_parses_reviews(self, review_config):
        scraper = BlibliReviewScraper(review_config)
        items = scraper._extract_review_items(BLIBLI_REVIEWS_HTML)
        assert len(items) == 1
        parsed = scraper.parse_review(items[0])
        assert parsed["review_text"] == "kualitas oke worth it"
        assert parsed["rating"] == 4.5
        assert parsed["helpful_count"] == 12

    def test_build_review_url(self, review_config):
        scraper = BlibliReviewScraper(review_config)
        assert scraper.build_review_url("https://blibli.com/p/x").endswith("/x/reviews")


class TestShopeeReviews:
    def test_build_review_url(self, review_config):
        scraper = ShopeeReviewScraper(review_config)
        url = scraper.build_review_url("https://shopee.co.id/product/x")
        assert "page=0" in url and "product/x?" in url

    def test_lazy_driver_init(self, review_config):
        scraper = ShopeeReviewScraper(review_config)
        assert scraper.driver is None

    def test_next_page_increments(self, review_config):
        scraper = ShopeeReviewScraper(review_config)
        first = scraper.build_review_url("https://shopee.co.id/product/x")
        second = scraper.get_next_page_url(first)
        assert second is not None and "page=1" in second


class TestFetchLoop:
    """Exercise fetch_reviews with fetch_page/get_next_page_url monkeypatched."""

    def test_tags_source_and_product_id(self, review_config):
        scraper = TokopediaReviewScraper(review_config)
        scraper.fetch_page = MagicMock(return_value=_tokopedia_reviews_html())
        scraper.get_next_page_url = MagicMock(return_value=None)

        df = scraper.fetch_reviews("https://tokopedia.com/shop/gpu-x", product_id="TPD-001")
        assert len(df) == 2
        assert set(df["source"]) == {"tokopedia"}
        assert set(df["product_id"]) == {"TPD-001"}
        assert list(df.columns) == REVIEW_SCHEMA

    def test_multi_page_and_delay(self, review_config):
        scraper = TokopediaReviewScraper(review_config)
        page_1 = _tokopedia_reviews_html()
        page_2_cache = _tokopedia_review_cache()
        # distinct reviews on page 2 so dedup doesn't collapse them
        page_2_cache["reviewListPDPType9001"]["feedbackID"] = "9101"
        page_2_cache["reviewListPDPType9001"]["message"] = "page dua bagus"
        page_2_cache["reviewListPDPType9002"]["feedbackID"] = "9102"
        page_2_cache["reviewListPDPType9002"]["message"] = "page dua jelek"
        page_2 = "<html><script>window.__cache = " + json.dumps(page_2_cache) + ";</script></html>"
        scraper.fetch_page = MagicMock(side_effect=[page_1, page_2])
        scraper.get_next_page_url = MagicMock(
            side_effect=["https://tokopedia.com/shop/gpu-x/review?page=2", None]
        )

        with patch("src.scrapers.base_review_scraper.time.sleep") as mock_sleep:
            df = scraper.fetch_reviews("https://tokopedia.com/shop/gpu-x", max_pages=2)
        assert len(df) == 4
        mock_sleep.assert_called_once()  # between pages, not after the last

    def test_deduplicates_identical_reviews(self, review_config):
        # Same page served twice via pagination → identical reviews → dedup
        scraper = TokopediaReviewScraper(review_config)
        scraper.fetch_page = MagicMock(return_value=_tokopedia_reviews_html())
        scraper.get_next_page_url = MagicMock(
            side_effect=["https://tokopedia.com/shop/gpu-x/review?page=2", None]
        )
        df = scraper.fetch_reviews("https://tokopedia.com/shop/gpu-x")
        assert len(df) == 2  # 4 raw rows collapsed to the 2 unique reviews

    def test_fetch_error_stops_loop(self, review_config):
        scraper = TokopediaReviewScraper(review_config)
        scraper.fetch_page = MagicMock(side_effect=RuntimeError("boom"))
        df = scraper.fetch_reviews("https://tokopedia.com/shop/gpu-x")
        assert isinstance(df, pd.DataFrame)
        assert df.empty


class TestRetryBackoff:
    def test_succeeds_after_transient_failures(self, review_config):
        scraper = TokopediaReviewScraper(review_config)
        responses = [
            requests.exceptions.ConnectionError("f1"),
            requests.exceptions.ConnectionError("f2"),
            MagicMock(status_code=200, text="OK", raise_for_status=lambda: None),
        ]
        with (
            patch("src.scrapers.retry.requests.get", side_effect=responses),
            patch("src.scrapers.retry.time.sleep") as mock_sleep,
        ):
            html = scraper._request_with_retry("https://example.com")
        assert html == "OK"
        assert mock_sleep.call_count == 2  # backoff after each failure

    def test_raises_after_retry_exhaustion(self, review_config):
        scraper = TokopediaReviewScraper(review_config)
        with (
            patch(
                "src.scrapers.retry.requests.get",
                side_effect=requests.exceptions.ConnectionError("down"),
            ),
            patch("src.scrapers.retry.time.sleep"),
        ):
            with pytest.raises(requests.exceptions.ConnectionError):
                scraper._request_with_retry("https://example.com")

    def test_backoff_grows_exponentially(self, review_config):
        scraper = TokopediaReviewScraper(review_config)  # delay=0 → scale via config
        scraper.delay = 1.0
        responses = [
            requests.exceptions.ConnectionError("f1"),
            MagicMock(status_code=200, text="OK", raise_for_status=lambda: None),
        ]
        with (
            patch("src.scrapers.retry.requests.get", side_effect=responses),
            patch("src.scrapers.retry.time.sleep") as mock_sleep,
        ):
            scraper._request_with_retry("https://example.com")
        assert mock_sleep.call_args[0][0] == 1.0 * (2**0)  # base delay, first retry

    def test_client_errors_not_retried(self, review_config):
        """4xx will not heal with backoff — fail immediately, no sleep."""
        scraper = TokopediaReviewScraper(review_config)
        error = requests.exceptions.HTTPError()
        error.response = MagicMock(status_code=404)
        responses = [
            MagicMock(status_code=404, raise_for_status=lambda: (_ for _ in ()).throw(error))
        ]
        with (
            patch("src.scrapers.retry.requests.get", side_effect=responses),
            patch("src.scrapers.retry.time.sleep") as mock_sleep,
        ):
            with pytest.raises(requests.exceptions.HTTPError):
                scraper._request_with_retry("https://example.com")
        mock_sleep.assert_not_called()

    def test_product_scrapers_retry_timeouts(self, review_config):
        """Live Colab finding: a single timeout must not end a category."""
        from src.scrapers import TokopediaScraper

        scraper = TokopediaScraper(review_config)
        responses = [
            requests.exceptions.ReadTimeout("slow"),
            MagicMock(status_code=200, text="<html>cache</html>", raise_for_status=lambda: None),
        ]
        with (
            patch("src.scrapers.retry.requests.get", side_effect=responses),
            patch("src.scrapers.retry.time.sleep"),
        ):
            html = scraper.fetch_page("https://www.tokopedia.com/find/rtx?page=1")
        assert "cache" in html
