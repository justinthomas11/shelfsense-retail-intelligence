# Retailer scrapers package
from scrapers.base_scraper import BaseScraper, ScrapedPrice
from scrapers.bigbasket_scraper import BigBasketScraper
from scrapers.blinkit_scraper import BlinkitScraper
from scrapers.jiomart_scraper import JioMartScraper
from scrapers.zepto_scraper import ZeptoScraper

SCRAPERS = {
    cls.RETAILER_NAME: cls
    for cls in (BigBasketScraper, BlinkitScraper, ZeptoScraper, JioMartScraper)
}

__all__ = ["BaseScraper", "ScrapedPrice", "SCRAPERS"]
