"""Blinkit scraper — React storefront, rendered with Playwright."""

from scrapers.base_scraper import BaseScraper


class BlinkitScraper(BaseScraper):
    RETAILER_NAME = "Blinkit"
    SEARCH_URL = "https://blinkit.com/s/?q={query}"
    REQUIRES_JS = True
    SELECTORS = {
        "card": "div[data-test-id='plp-product'], div[role='button'][id]",
        "name": "div.tw-text-300.tw-font-semibold, div[class*='Product__ProductName']",
        "price": "div.tw-text-200.tw-font-semibold, div[class*='ProductPrice']",
        "mrp": "div.tw-line-through, div[class*='ProductMrp']",
        "unit": "div.tw-text-200.tw-font-medium, div[class*='ProductVariant']",
        "out_of_stock": "div[class*='OutOfStock'], div.tw-text-050",
    }
