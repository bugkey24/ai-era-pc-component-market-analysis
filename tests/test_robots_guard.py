"""Tests for the RobotsGuard — RFC 9309 semantics via committed snapshots."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.scrapers import RobotsGuard

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = str(PROJECT_ROOT / "docs" / "compliance" / "robots")

TOKOPEDIA_PRODUCTS_HTML = """
<div data-testid="divProductWrapper" data-product-id="TPD-001">
    <span data-testid="productName">NVIDIA RTX 4060 8GB</span>
    <span data-testid="productPrice">Rp4.500.000</span>
    <span data-testid="productRating">4.8</span>
</div>
<div data-testid="divProductWrapper" data-product-id="TPD-002">
    <span data-testid="productName">AMD RX 7600</span>
    <span data-testid="productPrice">Rp4.200.000</span>
    <span data-testid="productRating">4.6</span>
</div>
"""


@pytest.fixture
def guard():
    return RobotsGuard(
        {"enabled": True, "fail_open": False, "snapshot_dir": SNAPSHOT_DIR, "timeout": 1}
    )


class TestSnapshotResolution:
    def test_tokopedia_find_allowed(self, guard):
        assert guard.is_allowed("https://www.tokopedia.com/find/gpu?page=1")

    def test_tokopedia_search_disallowed(self, guard):
        # The legacy /search surface is robots-DISALLOWED
        assert not guard.is_allowed("https://www.tokopedia.com/search?q=gpu")

    def test_tokopedia_reviews_allowed(self, guard):
        # Allow: /*/review and /*/*/review
        assert guard.is_allowed("https://www.tokopedia.com/shop-x/gpu-y/review")

    def test_blibli_product_detail_allowed(self, guard):
        # Allow: /p/*$ (clean product URLs, no query string)
        assert guard.is_allowed("https://www.blibli.com/p/gpu-amazing-000123")

    def test_blibli_product_with_query_disallowed(self, guard):
        # Disallow: /p/*?*
        assert not guard.is_allowed("https://www.blibli.com/p/gpu-000123?pickup=x")

    def test_blibli_search_disallowed(self, guard):
        assert not guard.is_allowed("https://www.blibli.com/search/gpu")

    def test_blibli_product_review_path_disallowed(self, guard):
        # Disallow: /p/*/pr* matches /p/{slug}/product-reviews (segment starts "pr")
        assert not guard.is_allowed("https://www.blibli.com/p/gpu-000123/product-reviews")

    def test_blibli_reviews_segment_not_matched_by_pr_rule(self, guard):
        # "/reviews" starts with "re", not "pr" — /p/*/pr* does NOT match it.
        # (Kept robots-permitted per spec; strategy still gates Blibli reviews
        # off via robots_permitted=False — no sanctioned review surface.)
        assert guard.is_allowed("https://www.blibli.com/p/gpu-000123/reviews")

    def test_shopee_search_allowed_for_star_agent(self, guard):
        # User-agent: * does not disallow plain /search
        assert guard.is_allowed("https://shopee.co.id/search?keyword=gpu")

    def test_shopee_crawl_delay_parsed(self, guard):
        delay = guard.crawl_delay("https://shopee.co.id/search?keyword=gpu")
        assert delay == 1.0  # Crawl-delay: 1 in the User-agent: * section

    def test_snapshot_loaded_once_per_origin(self, guard):
        guard.is_allowed("https://www.tokopedia.com/find/gpu?page=1")
        file_first = guard._get_file("https://www.tokopedia.com")
        file_second = guard._get_file("https://www.tokopedia.com")
        assert file_first is file_second  # cached instance reused


class TestFailModes:
    def _unreachable_guard(self, fail_open: bool) -> RobotsGuard:
        return RobotsGuard(
            {"enabled": True, "fail_open": fail_open, "snapshot_dir": "/nonexistent", "timeout": 1}
        )

    def test_fail_closed_blocks_when_unreachable(self):
        guard = self._unreachable_guard(fail_open=False)
        with patch(
            "src.scrapers.robots_guard.requests.get",
            side_effect=requests.exceptions.ConnectionError("down"),
        ):
            assert not guard.is_allowed("https://unknown.example.com/p/1")

    def test_fail_open_allows_when_unreachable(self):
        guard = self._unreachable_guard(fail_open=True)
        with patch(
            "src.scrapers.robots_guard.requests.get",
            side_effect=requests.exceptions.ConnectionError("down"),
        ):
            assert guard.is_allowed("https://unknown.example.com/p/1")

    def test_http_404_means_no_restrictions(self):
        guard = self._unreachable_guard(fail_open=False)
        resp = MagicMock(status_code=404, text="")
        with patch("src.scrapers.robots_guard.requests.get", return_value=resp):
            assert guard.is_allowed("https://no-robots.example.com/p/1")

    def test_http_403_blocks_everything(self):
        guard = self._unreachable_guard(fail_open=True)
        resp = MagicMock(status_code=403, text="")
        with patch("src.scrapers.robots_guard.requests.get", return_value=resp):
            assert not guard.is_allowed("https://forbidden.example.com/p/1")


class TestDisabledGuard:
    def test_disabled_guard_allows_all_without_io(self):
        guard = RobotsGuard({"enabled": False, "snapshot_dir": "/nonexistent"})
        assert guard.is_allowed("https://any.example.com/whatever")
        assert guard.crawl_delay("https://any.example.com/whatever") is None


class TestScrapeLoopIntegration:
    def test_scrape_stops_on_disallowed_url(self):
        from src.scrapers import BlibliScraper

        config = {
            "robots": {"enabled": True, "fail_open": False, "snapshot_dir": SNAPSHOT_DIR},
            "base_url": "https://www.blibli.com",
            "delay": 0.0,
        }
        scraper = BlibliScraper(config)
        scraper._build_search_url = lambda category: "https://www.blibli.com/search/gpu"
        scraper.fetch_page = MagicMock(return_value="<html></html>")

        df = scraper.scrape("gpu", max_pages=2)
        assert df.empty
        scraper.fetch_page.assert_not_called()  # never requested the disallowed URL

    def test_scrape_proceeds_on_allowed_url(self):
        from src.scrapers import TokopediaScraper

        config = {
            "robots": {"enabled": True, "fail_open": False, "snapshot_dir": SNAPSHOT_DIR},
            "delay": 0.0,
        }
        scraper = TokopediaScraper(config)  # _build_search_url now returns /find/gpu?page=1
        scraper.fetch_page = MagicMock(return_value=TOKOPEDIA_PRODUCTS_HTML)
        scraper.get_next_page_url = MagicMock(return_value=None)

        df = scraper.scrape("gpu", max_pages=1)
        scraper.fetch_page.assert_called_once()
        assert len(df) == 2
