"""BigBasket scraper — server-rendered search results (requests + BeautifulSoup)."""

from scrapers.base_scraper import BaseScraper


class BigBasketScraper(BaseScraper):
    RETAILER_NAME = "BigBasket"
    SEARCH_URL = "https://www.bigbasket.com/ps/?q={query}"
    REQUIRES_JS = False
    SELECTORS = {
        "card": "li.PaginateItems___StyledLi-sc-1yrbjdr-0, div[qa='product']",
        "name": "h3, div[qa='product_name'] a",
        "price": "span.Pricing___StyledLabel-sc-pldi2d-1, span.discnt-price",
        "mrp": "span.Pricing___StyledLabel2-sc-pldi2d-2, span.mp-price",
        "unit": "span.PackSelector___StyledLabel-sc-1lmu4hv-0, span[ng-bind='vm.selectedProduct.w']",
        "out_of_stock": "button[disabled], .out-of-stock",
    }
