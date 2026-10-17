"""JioMart scraper — server-rendered search results (requests + BeautifulSoup)."""

from scrapers.base_scraper import BaseScraper


class JioMartScraper(BaseScraper):
    RETAILER_NAME = "JioMart"
    SEARCH_URL = "https://www.jiomart.com/search/{query}"
    REQUIRES_JS = False
    SELECTORS = {
        "card": "li.ais-InfiniteHits-item, div.plp-card-container",
        "name": "div.plp-card-details-name, span.clsgetname",
        "price": "span.jm-heading-xxs, span.final-price",
        "mrp": "span.line-through, strike",
        "unit": "div.plp-card-details-tag, span.weight",
        "out_of_stock": "div.out-of-stock, button.jm-btn[disabled]",
    }
