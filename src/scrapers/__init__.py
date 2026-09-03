"""Scraping modules for Tokopedia, Shopee, and Blibli.

Two entity types, one registry each:
- Products: ``SCRAPER_REGISTRY`` / :func:`get_scraper`
- Reviews:  ``REVIEW_SCRAPER_REGISTRY`` / :func:`get_review_scraper`
"""

from .base_review_scraper import REVIEW_SCHEMA, BaseReviewScraper
from .base_scraper import BaseScraper
from .blibli_review_scraper import BlibliReviewScraper
from .blibli_scraper import BlibliScraper
from .robots_guard import RobotsGuard
from .shopee_review_scraper import ShopeeReviewScraper
from .shopee_scraper import ShopeeScraper
from .tokopedia_review_scraper import TokopediaReviewScraper
from .tokopedia_scraper import TokopediaScraper

# Registry — maps platform names to scraper classes for factory use
SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "tokopedia": TokopediaScraper,
    "shopee": ShopeeScraper,
    "blibli": BlibliScraper,
}

REVIEW_SCRAPER_REGISTRY: dict[str, type[BaseReviewScraper]] = {
    "tokopedia": TokopediaReviewScraper,
    "shopee": ShopeeReviewScraper,
    "blibli": BlibliReviewScraper,
}


def get_scraper(platform: str, config: dict) -> BaseScraper:
    """Factory: instantiate the correct product scraper by platform name."""
    cls = SCRAPER_REGISTRY.get(platform.lower())
    if cls is None:
        raise ValueError(
            f"Unknown platform '{platform}'. Available: {list(SCRAPER_REGISTRY.keys())}"
        )
    return cls(config)


def get_review_scraper(platform: str, config: dict) -> BaseReviewScraper:
    """Factory: instantiate the correct review scraper by platform name."""
    cls = REVIEW_SCRAPER_REGISTRY.get(platform.lower())
    if cls is None:
        raise ValueError(
            f"Unknown platform '{platform}'. Available: {list(REVIEW_SCRAPER_REGISTRY.keys())}"
        )
    return cls(config)


__all__ = [
    "BaseScraper",
    "BaseReviewScraper",
    "REVIEW_SCHEMA",
    "RobotsGuard",
    "TokopediaScraper",
    "ShopeeScraper",
    "BlibliScraper",
    "TokopediaReviewScraper",
    "ShopeeReviewScraper",
    "BlibliReviewScraper",
    "SCRAPER_REGISTRY",
    "REVIEW_SCRAPER_REGISTRY",
    "get_scraper",
    "get_review_scraper",
]
