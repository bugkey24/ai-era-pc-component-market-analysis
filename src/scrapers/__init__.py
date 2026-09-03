"""Scraping modules for Tokopedia, Shopee, and Blibli."""

from .base_scraper import BaseScraper
from .blibli_scraper import BlibliScraper
from .shopee_scraper import ShopeeScraper
from .tokopedia_scraper import TokopediaScraper

# Registry — maps platform names to scraper classes for factory use
SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "tokopedia": TokopediaScraper,
    "shopee": ShopeeScraper,
    "blibli": BlibliScraper,
}


def get_scraper(platform: str, config: dict) -> BaseScraper:
    """Factory: instantiate the correct scraper by platform name."""
    cls = SCRAPER_REGISTRY.get(platform.lower())
    if cls is None:
        raise ValueError(
            f"Unknown platform '{platform}'. "
            f"Available: {list(SCRAPER_REGISTRY.keys())}"
        )
    return cls(config)


__all__ = [
    "BaseScraper",
    "TokopediaScraper",
    "ShopeeScraper",
    "BlibliScraper",
    "SCRAPER_REGISTRY",
    "get_scraper",
]
