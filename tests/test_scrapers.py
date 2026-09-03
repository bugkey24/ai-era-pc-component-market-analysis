"""Tests for scraper parsing logic — offline, no network calls."""

import json
from unittest.mock import MagicMock

import pytest

from src.scrapers import (
    SCRAPER_REGISTRY,
    BaseScraper,
    BlibliScraper,
    ShopeeScraper,
    TokopediaScraper,
    get_scraper,
)


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
        # scrape() adds source/category; parse_product only parses
        scraper = TokopediaScraper(scraper_config)
        entity = {
            "id": 1,
            "name": "MSI RTX 5060",
            "url": "https://www.tokopedia.com/shop/x",
            "rating": "4.8",
            "price": {"number": 4_500_000, "original": "", "discountPercentage": 0},
            "shop": {"name": "Toko", "city": "Jakarta"},
            "meta": {"countReview": 5},
        }
        product = scraper.parse_product(entity)
        assert product["name"] == "MSI RTX 5060"


class TestTokopediaCacheParsing:
    """The live page embeds an Apollo cache — parsing targets that JSON."""

    @staticmethod
    def _cache_html(entities: dict) -> str:
        return f"<html><script>window.__cache = {json.dumps(entities)};</script></html>"

    @staticmethod
    def _entity(
        pid: int,
        name: str,
        breadcrumb: str,
        *,
        price=4_500_000,
        original="Rp4.800.000",
        rating="4.8",
        reviews=120,
    ) -> dict:
        """Build one product entity + its Apollo sub-entities as siblings.

        Mirrors the real cache layout: the product holds *references*
        (``{"type": "id", "id": ...}``) that resolve to sibling keys.
        """
        return {
            f"searchProductV5Product{pid}": {
                "id": pid,
                "name": name,
                "url": f"https://www.tokopedia.com/shop/item-{pid}?extParam=track",
                "rating": rating,
                "price": {"type": "id", "id": f"$searchProductV5Product{pid}.price"},
                "shop": {"type": "id", "id": f"SearchProductV5Shop{pid}"},
                "meta": {"type": "id", "id": f"$searchProductV5Product{pid}.meta"},
                "category": {"type": "id", "id": f"SearchProductV5Category{pid}"},
                "__typename": "searchProductV5Product",
            },
            f"$searchProductV5Product{pid}.price": {
                "number": price,
                "original": original,
                "discountPercentage": 6,
                "__typename": "SearchProductV5Price",
            },
            f"SearchProductV5Shop{pid}": {
                "name": f"Toko {pid}",
                "city": "Jakarta Pusat",
                "__typename": "SearchProductV5Shop",
            },
            f"$searchProductV5Product{pid}.meta": {
                "countReview": reviews,
                "__typename": "SearchProductV5ProductMeta",
            },
            f"SearchProductV5Category{pid}": {
                "name": "Komputer & Laptop",
                "breadcrumb": breadcrumb,
                "__typename": "SearchProductV5Category",
            },
        }

    @pytest.fixture
    def gpu_cache_html(self) -> str:
        entities: dict = {}
        entities.update(
            self._entity(
                1001, "MSI GeForce RTX 5060 8GB GDDR7", "komputer-laptop/komponen-komputer/vga-card"
            )
        )
        entities.update(
            self._entity(
                1002, "Laptop Lenovo Legion RTX 5060", "komputer-laptop/komponen-komputer/vga-card"
            )
        )
        entities.update(
            self._entity(
                1003, "GPU Holder Vertical Stand", "komputer-laptop/komponen-komputer/vga-card"
            )
        )
        entities.update(self._entity(1004, "Buku Novel Tentang GPU", "buku/buku-novel"))
        entities.update(
            self._entity(
                1001, "MSI GeForce RTX 5060 8GB GDDR7", "komputer-laptop/komponen-komputer/vga-card"
            )
        )  # dup id
        return self._cache_html(entities)

    def test_extracts_relevant_products_only(self, scraper_config, gpu_cache_html):
        scraper = TokopediaScraper(scraper_config)
        scraper._current_category = "gpu"  # scrape() sets this in real flow
        items = scraper._extract_items(gpu_cache_html)
        assert len(items) == 1  # laptop, accessory, book, and duplicate removed
        assert items[0]["name"] == "MSI GeForce RTX 5060 8GB GDDR7"

    def test_parse_product_maps_schema(self, scraper_config, gpu_cache_html):
        scraper = TokopediaScraper(scraper_config)
        scraper._current_category = "gpu"
        entity = scraper._extract_items(gpu_cache_html)[0]
        product = scraper.parse_product(entity)
        assert product["product_id"] == "1001"
        assert product["price"] == 4_500_000
        assert product["original_price"] == 4_800_000
        assert product["discount"] == 6
        assert product["rating"] == 4.8
        assert product["review_count"] == 120
        assert product["seller_name"] == "Toko 1001"
        assert product["location"] == "Jakarta Pusat"
        assert "extParam" not in product["url"]  # tracking params stripped

    def test_missing_cache_returns_empty(self, scraper_config):
        scraper = TokopediaScraper(scraper_config)
        assert scraper._extract_items("<html><body>no cache</body></html>") == []

    def test_malformed_cache_returns_empty(self, scraper_config):
        scraper = TokopediaScraper(scraper_config)
        assert scraper._extract_items("<script>window.__cache = {broken;</script>") == []

    @pytest.mark.parametrize(
        ("category", "segment"),
        [("gpu", "vga-card"), ("ram", "ram-komputer"), ("ssd", "media-penyimpanan-data/ssd")],
    )
    def test_category_segments_match_live_taxonomy(self, category, segment):
        # Verified against live pages 2026-09-03 (see docs/06 validation report)
        from src.scrapers.tokopedia_scraper import _CATEGORY_SEGMENTS

        assert _CATEGORY_SEGMENTS[category] == segment

    def test_live_noise_filtered(self, scraper_config):
        """Real noise observed on live /find/ddr5 and /find/nvme pages."""
        scraper = TokopediaScraper(scraper_config)
        noise = [
            (
                "Motherboard ASRock B760M Pro RS DDR5",
                "komputer-laptop/komponen-komputer/ram-komputer",
                "ram",
            ),
            (
                "Lexar E6 SSD Enclosure NVMe M.2",
                "komputer-laptop/media-penyimpanan-data/ssd",
                "ssd",
            ),
            ("SSD Cooler JONSBO M.2-6 Grey", "komputer-laptop/media-penyimpanan-data/ssd", "ssd"),
            ("Baut SSD M.2 SATA", "komputer-laptop/media-penyimpanan-data/ssd", "ssd"),
            ("Laptop Lenovo Legion RTX 5060", "komputer-laptop/komponen-komputer/vga-card", "gpu"),
        ]
        for name, bc, cat in noise:
            entity = {"name": name, "_category": {"breadcrumb": bc}}
            assert not scraper._is_relevant(entity, cat), f"should exclude: {name}"

    def test_build_search_url_uses_keyword_map(self, scraper_config):
        scraper = TokopediaScraper({**scraper_config, "search_keywords": {"gpu": "rtx"}})
        assert scraper._build_search_url("gpu").endswith("/find/rtx?page=1")

    def test_next_page_pagination(self, scraper_config):
        scraper = TokopediaScraper(scraper_config)
        first = scraper._build_search_url("gpu")
        second = scraper.get_next_page_url(first)
        assert second is not None and "page=2" in second
        third = scraper.get_next_page_url(second)
        assert third is not None and "page=3" in third

    def test_scrape_tags_source_and_category(self, scraper_config, gpu_cache_html):
        scraper = TokopediaScraper(scraper_config)
        scraper.fetch_page = MagicMock(return_value=gpu_cache_html)
        scraper.get_next_page_url = MagicMock(return_value=None)
        df = scraper.scrape("gpu", max_pages=1)
        assert len(df) == 1
        assert df.iloc[0]["source"] == "tokopedia"
        assert df.iloc[0]["category"] == "gpu"


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
