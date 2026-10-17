import pytest
import requests

from conftest import element_for
from scrapers import SCRAPERS
from scrapers.base_scraper import ScrapedPrice, best_match, parse_price


@pytest.mark.parametrize("text, expected", [
    ("₹1,299.00", 1299.0),
    ("MRP: Rs 45", 45.0),
    ("₹ 72.5", 72.5),
    ("12,34,567", 1234567.0),
    ("Out of stock", None),
    (None, None),
])
def test_parse_price(text, expected):
    assert parse_price(text) == expected


def test_discount_pct():
    assert ScrapedPrice("Zepto", "x", selling_price=80, mrp=100).discount_pct == 20.0
    assert ScrapedPrice("Zepto", "x", selling_price=100, mrp=None).discount_pct == 0.0
    assert ScrapedPrice("Zepto", "x", selling_price=110, mrp=100).discount_pct == 0.0


def test_best_match_picks_closest_name():
    candidates = [
        ScrapedPrice("Zepto", "Amul Butter Pasteurised 100 g", 56),
        ScrapedPrice("Zepto", "Amul Butter", 270),
        ScrapedPrice("Zepto", "Mother Dairy Cow Ghee", 599),
    ]
    assert best_match("Amul Butter", candidates).selling_price == 270


def test_best_match_returns_none_below_threshold():
    assert best_match("Amul Butter", [ScrapedPrice("Zepto", "Surf Excel Matic", 500)]) is None


def build_results_page(scraper_cls, products):
    sel = scraper_cls.SELECTORS
    cards = []
    for name, price, mrp, in_stock in products:
        inner = (
            element_for(sel["name"], name)
            + element_for(sel["price"], f"₹{price}")
            + element_for(sel["mrp"], f"₹{mrp}")
            + element_for(sel["unit"], "1 kg")
            + ("" if in_stock else element_for(sel["out_of_stock"], "Notify me"))
        )
        cards.append(element_for(sel["card"], inner))
    return "<html><body>" + "".join(cards) + "</body></html>"


@pytest.mark.parametrize("retailer", list(SCRAPERS))
def test_each_scraper_parses_its_own_markup(retailer):
    scraper_cls = SCRAPERS[retailer]
    html = build_results_page(scraper_cls, [
        ("Tata Sampann Toor Dal", "1,169.00", "1,285", True),
        ("Amul Butter", "270", "285", False),
    ])
    results = scraper_cls(delay_seconds=0).parse(html)

    assert [r.product_name for r in results] == ["Tata Sampann Toor Dal", "Amul Butter"]
    assert results[0].selling_price == 1169.0
    assert results[0].mrp == 1285.0
    assert results[0].is_available is True
    assert results[1].is_available is False
    assert all(r.retailer_name == retailer for r in results)


def test_parse_skips_cards_without_price():
    scraper_cls = SCRAPERS["JioMart"]
    sel = scraper_cls.SELECTORS
    html = element_for(sel["card"], element_for(sel["name"], "Mystery item"))
    assert scraper_cls(delay_seconds=0).parse(html) == []


def test_scrape_catalog_maps_to_canonical_names(monkeypatch):
    scraper = SCRAPERS["BigBasket"](delay_seconds=0)
    pages = {
        "Amul Butter": [ScrapedPrice("BigBasket", "Amul Butter 500 g", 270, 285)],
        "Exo Dishwash Bar": [],
    }
    monkeypatch.setattr(scraper, "search", lambda q: pages[q])
    catalog = [
        {"name": "Amul Butter", "brand": "Amul"},
        {"name": "Exo Dishwash Bar", "brand": "Exo"},
    ]
    results = scraper.scrape_catalog(catalog)

    assert len(results) == 1
    assert results[0].product_name == "Amul Butter"
    assert results[0].brand == "Amul"


def test_scrape_catalog_survives_individual_failures(monkeypatch):
    scraper = SCRAPERS["BigBasket"](delay_seconds=0)

    def flaky(query):
        if query == "Bad":
            raise requests.ConnectionError("boom")
        return [ScrapedPrice("BigBasket", query, 10)]

    monkeypatch.setattr(scraper, "search", flaky)
    results = scraper.scrape_catalog([{"name": "Bad", "brand": "x"}, {"name": "Good", "brand": "y"}])
    assert [r.product_name for r in results] == ["Good"]


def test_fetch_retries_then_succeeds(monkeypatch):
    scraper = SCRAPERS["BigBasket"](delay_seconds=0, max_retries=3)
    monkeypatch.setattr("scrapers.base_scraper.time.sleep", lambda s: None)
    calls = {"n": 0}

    class Response:
        text = "<html>ok</html>"

        def raise_for_status(self):
            pass

    def get(url, timeout):
        calls["n"] += 1
        if calls["n"] < 3:
            raise requests.Timeout("slow")
        return Response()

    monkeypatch.setattr(scraper.session, "get", get)
    assert scraper.fetch("https://example.com") == "<html>ok</html>"
    assert calls["n"] == 3
