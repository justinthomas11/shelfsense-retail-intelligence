"""
ShelfSense — Base Scraper
==========================
Shared plumbing for every retailer scraper:

  • ScrapedPrice — the normalized record every scraper emits
  • Polite HTTP fetching (rate limiting, retries with backoff, browser UA)
  • Optional Playwright rendering for JavaScript-heavy storefronts
  • Price-string parsing ("₹1,299.00" → 1299.0)
  • Fuzzy matching of search results back to the product catalog

Subclasses only declare their search URL, CSS selectors and (optionally)
whether the page must be rendered in a headless browser.

Retailer markup changes frequently, so selectors live in a single SELECTORS
dict per scraper to keep maintenance to a one-line edit.
"""

import logging
import re
import time
from abc import ABC
from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

PRICE_PATTERN = re.compile(r"(\d[\d,]*(?:\.\d+)?)")


@dataclass
class ScrapedPrice:
    """A single price observation, normalized across retailers."""
    retailer_name: str
    product_name: str
    selling_price: float
    mrp: float | None = None
    brand: str | None = None
    unit_size: str | None = None
    is_available: bool = True
    price_date: date = field(default_factory=date.today)

    @property
    def discount_pct(self):
        if not self.mrp or self.mrp <= 0 or self.selling_price > self.mrp:
            return 0.0
        return round((self.mrp - self.selling_price) / self.mrp * 100, 2)


def parse_price(text):
    """Extract a numeric price from strings like '₹1,299.00' or 'MRP: Rs 45'."""
    if text is None:
        return None
    match = PRICE_PATTERN.search(str(text))
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def similarity(a, b):
    """Case-insensitive string similarity in [0, 1]."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def best_match(target_name, candidates, threshold=0.6):
    """Return the ScrapedPrice whose name best matches target_name, or None."""
    scored = [(similarity(target_name, c.product_name), c) for c in candidates]
    scored = [s for s in scored if s[0] >= threshold]
    if not scored:
        return None
    return max(scored, key=lambda s: s[0])[1]


class BaseScraper(ABC):
    """Template for a retailer scraper. Subclasses fill in the class attributes."""

    RETAILER_NAME = ""
    SEARCH_URL = ""          # must contain a {query} placeholder
    REQUIRES_JS = False      # True → render with Playwright instead of requests
    SELECTORS = {
        "card": "",          # one element per product tile
        "name": "",
        "price": "",
        "mrp": "",
        "unit": "",
        "out_of_stock": "",  # present inside a card when the item is unavailable
    }

    def __init__(self, delay_seconds=2.0, max_retries=3, timeout=15):
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._last_request = 0.0

    # ── Fetching ────────────────────────────────────────────────────────
    def _throttle(self):
        wait = self.delay_seconds - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def fetch(self, url):
        """GET a page with rate limiting and exponential-backoff retries."""
        if self.REQUIRES_JS:
            return self._fetch_rendered(url)

        for attempt in range(1, self.max_retries + 1):
            self._throttle()
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as exc:
                logger.warning("%s attempt %d/%d failed: %s",
                               self.RETAILER_NAME, attempt, self.max_retries, exc)
                if attempt == self.max_retries:
                    raise
                time.sleep(2 ** attempt)

    def _fetch_rendered(self, url):
        """Render a JavaScript storefront in headless Chromium."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                f"{self.RETAILER_NAME} requires Playwright: "
                "pip install playwright && playwright install chromium"
            ) from exc

        self._throttle()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=DEFAULT_HEADERS["User-Agent"])
                page.goto(url, timeout=self.timeout * 1000, wait_until="networkidle")
                if self.SELECTORS["card"]:
                    page.wait_for_selector(self.SELECTORS["card"], timeout=self.timeout * 1000)
                return page.content()
            finally:
                browser.close()

    # ── Parsing ─────────────────────────────────────────────────────────
    def _text(self, node, selector):
        if not selector:
            return None
        found = node.select_one(selector)
        return found.get_text(" ", strip=True) if found else None

    def parse(self, html):
        """Turn a search-results page into a list of ScrapedPrice records."""
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for card in soup.select(self.SELECTORS["card"]):
            name = self._text(card, self.SELECTORS["name"])
            price = parse_price(self._text(card, self.SELECTORS["price"]))
            if not name or price is None:
                continue
            mrp = parse_price(self._text(card, self.SELECTORS["mrp"])) or price
            out_of_stock = bool(
                self.SELECTORS["out_of_stock"] and card.select_one(self.SELECTORS["out_of_stock"])
            )
            results.append(ScrapedPrice(
                retailer_name=self.RETAILER_NAME,
                product_name=name,
                selling_price=price,
                mrp=mrp,
                unit_size=self._text(card, self.SELECTORS["unit"]),
                is_available=not out_of_stock,
            ))
        return results

    # ── Public API ──────────────────────────────────────────────────────
    def search(self, query):
        url = self.SEARCH_URL.format(query=quote_plus(query))
        return self.parse(self.fetch(url))

    def scrape_catalog(self, catalog):
        """
        Search for each catalog product and keep the best-matching result.

        Failures on individual products are logged and skipped so one bad
        page never aborts the daily run.
        """
        observations = []
        for product in catalog:
            try:
                match = best_match(product["name"], self.search(product["name"]))
            except Exception as exc:
                logger.error("%s: failed to scrape '%s': %s",
                             self.RETAILER_NAME, product["name"], exc)
                continue
            if match is None:
                logger.info("%s: no match for '%s'", self.RETAILER_NAME, product["name"])
                continue
            # Report under the canonical catalog name so the loader can join on it
            match.product_name = product["name"]
            match.brand = product["brand"]
            observations.append(match)
        return observations
