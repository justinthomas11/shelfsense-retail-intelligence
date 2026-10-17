from datetime import date
from statistics import mean

from data_simulator.product_catalog import PRODUCT_CATALOG
from data_simulator.simulate_prices import RETAILER_STRATEGIES
from pipeline.simulated_source import simulate_day
from pipeline.validation import validate_records

SATURDAY = date(2026, 10, 17)
WEDNESDAY = date(2026, 10, 14)


def test_covers_every_product_at_every_retailer():
    records = simulate_day(WEDNESDAY)
    assert len(records) == len(PRODUCT_CATALOG) * len(RETAILER_STRATEGIES)
    assert {r.price_date for r in records} == {WEDNESDAY}


def test_same_date_is_reproducible():
    assert simulate_day(WEDNESDAY) == simulate_day(WEDNESDAY)
    assert simulate_day(WEDNESDAY) != simulate_day(SATURDAY)


def test_retailer_filter():
    records = simulate_day(WEDNESDAY, retailers=["Zepto"])
    assert {r.retailer_name for r in records} == {"Zepto"}


def test_all_records_pass_validation():
    records = simulate_day(WEDNESDAY)
    _, rejected = validate_records(records)
    assert rejected == []


def test_discounts_respect_strategy_bounds_and_cap():
    for r in simulate_day(WEDNESDAY):
        if not r.is_available:
            assert r.selling_price == r.mrp
            continue
        strategy = RETAILER_STRATEGIES[r.retailer_name]
        # 0.01 tolerance for rounding of prices to paise
        assert strategy["min_disc"] - 0.01 <= r.discount_pct <= strategy["max_disc"] + 0.01


def test_weekends_are_discounted_more():
    def avg_discount(day):
        return mean(r.discount_pct for r in simulate_day(day) if r.is_available)
    assert avg_discount(SATURDAY) > avg_discount(WEDNESDAY)
    assert max(r.discount_pct for r in simulate_day(SATURDAY)) <= 45.01
