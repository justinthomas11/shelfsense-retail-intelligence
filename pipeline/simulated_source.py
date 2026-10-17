"""
ShelfSense — Simulated Daily Source
====================================
Produces one day of price observations using the same retailer strategies
and category volatility as data_simulator/simulate_prices.py. Used when
live scraping is unavailable, so the daily time series keeps growing.

Seeded by date, so re-running for the same day yields identical prices.
"""

import random
from datetime import date

from data_simulator.product_catalog import PRODUCT_CATALOG
from data_simulator.simulate_prices import (
    CATEGORY_VOLATILITY,
    RETAILER_STRATEGIES,
    START_DATE,
    round_price,
)
from scrapers.base_scraper import ScrapedPrice


def simulate_day(target_date=None, retailers=None, catalog=PRODUCT_CATALOG):
    """Generate ScrapedPrice records for every catalog product at each retailer."""
    target_date = target_date or date.today()
    retailers = retailers or list(RETAILER_STRATEGIES)
    rng = random.Random(target_date.toordinal())

    weeks_elapsed = (target_date - START_DATE).days / 7.0
    inflation_factor = 1 + 0.001 * weeks_elapsed
    is_weekend = target_date.weekday() in (5, 6)

    records = []
    for retailer_name in retailers:
        strategy = RETAILER_STRATEGIES[retailer_name]
        for product in catalog:
            volatility = CATEGORY_VOLATILITY.get(product["category"], 0.5)
            jitter = rng.gauss(0, 0.02 * volatility)
            mrp = round_price(product["base_mrp"] * (1 + strategy["bias"]) * inflation_factor * (1 + jitter))

            if rng.random() < strategy["stockout_prob"]:
                records.append(ScrapedPrice(
                    retailer_name=retailer_name, product_name=product["name"],
                    brand=product["brand"], unit_size=product["unit"],
                    selling_price=mrp, mrp=mrp, is_available=False, price_date=target_date,
                ))
                continue

            discount = rng.uniform(strategy["min_disc"], strategy["max_disc"])
            if is_weekend:
                discount += rng.uniform(2, 5)
            discount = min(discount, 45)

            records.append(ScrapedPrice(
                retailer_name=retailer_name, product_name=product["name"],
                brand=product["brand"], unit_size=product["unit"],
                selling_price=round_price(mrp * (1 - discount / 100)), mrp=mrp,
                is_available=True, price_date=target_date,
            ))
    return records
