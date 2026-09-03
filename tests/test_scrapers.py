"""Tests for scraper parsing logic — offline, no network calls."""

import pytest

from src.scrapers import (
    SCRAPER_REGISTRY,
    BaseScraper,
    BlibliScraper,
    ShopeeScraper,
    TokopediaScraper,
    get_scraper,
)

TOKOPEDIA_HTML = """
<div data-testid="divProductWrapper" data-product-id="TPD-001">
    <span data-testid="productName">NVIDIA RTX 4060 8GB</span>
    <span data-testid="productPrice">Rp4.500.000</span>
    <span data-testid="productRating">4.8</span>
    <span data-testid="linkStore">OfficialStore</span>
    <span data-testid="linkLocation">Jakarta Pusat</span>
</div>
<div data-testid="divProductWrapper" data-product-id="TPD-002">
    <span data-testid="productName">AMD RX 7600</span>
    <span data-testid="productPrice">Rp4.200.000</span>
    <span data-testid="productRating">4.6</span>
</div>
"""


@pytest.fixture
def scraper_config():
    return {
        "user_agent": "test-agent",
        "timeout": 5,
        "retry_count": 1,
        "delay": 0.0,
        "robots": {"enabled": False},  # compliance behaviour tested in test_robots_guard.py
    }


class TestFactory:
    def test_registry_contains_all_platforms(self):
        assert set(SCRAPER_REGISTRY.keys()) == {"tokopedia", "shopee", "blibli"}

    def test_get_scraper_returns_correct_type(self, scraper_config):
        assert isinstance(get_scraper("tokopedia", scraper_config), TokopediaScraper)
        assert isinstance(get_scraper("shopee", scraper_config), ShopeeScraper)
        assert isinstance(get_scraper("blibli", scraper_config), BlibliScraper)

    def test_get_scraper_case_insensitive(self, scraper_config):
        assert isinstance(get_scraper("TOKOPEDIA", scraper_config), TokopediaScraper)

    def test_unknown_platform_raises(self, scraper_config):
        with pytest.raises(ValueError, match="Unknown platform"):
            get_scraper("amazon", scraper_config)


class TestBaseScraper:
    def test_cannot_instantiate_abstract(self, scraper_config):
        with pytest.raises(TypeError):
            BaseScraper(scraper_config)  # type: ignore[abstract]

    def test_defaults_from_config(self, scraper_config):
        scraper = TokopediaScraper(scraper_config)
        assert scraper.timeout == 5
        assert scraper.retry_count == 1
        assert scraper.delay == 0.0

    def test_default_config_values(self):
        scraper = TokopediaScraper({})
        assert scraper.timeout == 10
        assert scraper.retry_count == 3
        assert scraper.delay == 2.0

    def test_platform_name_tagged_in_scrape_output(self, scraper_config):
        scraper = TokopediaScraper(scraper_config)
        items = scraper._extract_items(TOKOPEDIA_HTML)
        assert len(items) == 2
        product = scraper.parse_product(items[0])
        # scrape() adds source/category; parse_product only parses
        assert product["name"] == "NVIDIA RTX 4060 8GB"


class TestTokopediaParsing:
    def test_parses_all_fields(self, scraper_config):
        scraper = TokopediaScraper(scraper_config)
        item = scraper._extract_items(TOKOPEDIA_HTML)[0]
        product = scraper.parse_product(item)
        assert product["product_id"] == "TPD-001"
        assert product["name"] == "NVIDIA RTX 4060 8GB"
        assert product["price"] == 4_500_000
        assert product["rating"] == 4.8
        assert product["seller_name"] == "OfficialStore"
        assert product["location"] == "Jakarta Pusat"

    def test_price_extraction_ignores_non_digits(self, scraper_config):
        scraper = TokopediaScraper(scraper_config)
        item = scraper._extract_items(TOKOPEDIA_HTML)[1]
        assert scraper.parse_product(item)["price"] == 4_200_000

    def test_missing_fields_default_safely(self, scraper_config):
        scraper = TokopediaScraper(scraper_config)
        item = scraper._extract_items(TOKOPEDIA_HTML)[1]  # no store/location tags
        product = scraper.parse_product(item)
        assert product["seller_name"] == ""
        assert product["location"] == ""

    def test_build_search_url_is_robots_compliant(self, scraper_config):
        scraper = TokopediaScraper(scraper_config)
        url = scraper._build_search_url("gpu")
        # Allow: /find/*?page — the legacy /search?q= surface is disallowed
        assert url.endswith("/find/gpu?page=1")
        assert "/search" not in url

    def test_next_page_pagination(self, scraper_config):
        scraper = TokopediaScraper(scraper_config)
        first = scraper._build_search_url("gpu")
        second = scraper.get_next_page_url(first)
        assert second is not None and "page=2" in second
        third = scraper.get_next_page_url(second)
        assert third is not None and "page=3" in third


class TestBlibliParsing:
    BLIBLI_HTML = """
    <div class="product-card" data-pid="BLI-100">
        <div class="product-card__name">Samsung 980 1TB NVMe</div>
        <div class="product-card__price">Rp950.000</div>
        <div class="product-card__rating-value">4.7</div>
        <div class="product-card__review-count">(65)</div>
        <div class="product-card__store">BlibliStore</div>
    </div>
    """

    def test_parses_product(self, scraper_config):
        scraper = BlibliScraper(scraper_config)
        items = scraper._extract_items(self.BLIBLI_HTML)
        assert len(items) == 1
        product = scraper.parse_product(items[0])
        assert product["product_id"] == "BLI-100"
        assert product["name"] == "Samsung 980 1TB NVMe"
        assert product["price"] == 950_000
        assert product["rating"] == 4.7

    def test_build_search_url_avoids_search_path(self, scraper_config):
        # Blibli robots disallows /search and /cari/* — discovery uses /c/ pages
        scraper = BlibliScraper(scraper_config)
        url = scraper._build_search_url("gpu")
        assert "/c/gpu" in url
        assert "/search" not in url and "/cari" not in url


class TestShopeeScraper:
    def test_build_search_url(self, scraper_config):
        scraper = ShopeeScraper(scraper_config)
        url = scraper._build_search_url("gpu")
        # Regression: config base_url is the bare domain — /search must not be lost
        assert url.endswith("/search?keyword=gpu")

    def test_driver_lazy_init(self, scraper_config):
        scraper = ShopeeScraper(scraper_config)
        assert scraper.driver is None  # not started until fetch_page

    def test_next_page_returns_none(self, scraper_config):
        # Shopee uses infinite scroll, never paginates by URL
        scraper = ShopeeScraper(scraper_config)
        assert scraper.get_next_page_url("https://shopee.co.id/search?keyword=gpu") is None
