"""Zepto scraper — Next.js storefront, rendered with Playwright."""

from scrapers.base_scraper import BaseScraper


class ZeptoScraper(BaseScraper):
    RETAILER_NAME = "Zepto"
    SEARCH_URL = "https://www.zeptonow.com/search?query={query}"
    REQUIRES_JS = True
    SELECTORS = {
        "card": "a[data-testid='product-card']",
        "name": "[data-testid='product-card-name'], h5",
        "price": "[data-testid='product-card-price']",
        "mrp": "[data-testid='product-card-mrp'], p.line-through",
        "unit": "[data-testid='product-card-quantity']",
        "out_of_stock": "[data-testid='out-of-stock'], [data-testid='notify-me']",
    }
