from decimal import Decimal

import pandas as pd
import pytest

from dashboard.analytics import apply_filters, cheapest_share, coerce_decimals, premium_matrix


def test_coerce_decimals_converts_numeric_columns_only():
    df = pd.DataFrame({
        "price": [Decimal("10.50"), Decimal("3.25"), None],
        "name": ["a", "b", "c"],
    })
    out = coerce_decimals(df)
    assert out["price"].dtype == float
    assert out["price"].iloc[0] == 10.5
    assert not pd.api.types.is_numeric_dtype(out["name"])


def test_apply_filters_ignores_missing_columns():
    df = pd.DataFrame({"category_name": ["Milk", "Chocolates"], "x": [1, 2]})
    assert len(apply_filters(df, ["Milk"], ["Zepto"])) == 1
    assert len(apply_filters(df, [], [])) == 2


def test_premium_matrix_is_median_relative_premium():
    pricing = pd.DataFrame({
        "bigbasket_price": [110.0, 220.0, 50.0],
        "blinkit_price": [100.0, 200.0, None],   # out of stock on product 3
        "zepto_price": [100.0, 200.0, 50.0],
        "jiomart_price": [None, None, None],      # carries nothing today
    })
    m = premium_matrix(pricing)
    assert m.loc["BigBasket", "Blinkit"] == pytest.approx(10.0)
    assert m.loc["BigBasket", "Zepto"] == pytest.approx(10.0)  # median of 10, 10, 0
    assert m.loc["Blinkit", "BigBasket"] == pytest.approx(-9.09)
    assert pd.isna(m.loc["BigBasket", "BigBasket"])
    assert pd.isna(m.loc["JioMart", "Zepto"])


def test_cheapest_share_sums_to_100_and_includes_every_retailer():
    wins = pd.DataFrame({
        "retailer_name": ["JioMart", "JioMart", "Zepto"],
        "days_cheapest": [30, 30, 20],
    })
    share = cheapest_share(wins)
    assert list(share.index[:2]) == ["JioMart", "Zepto"]
    assert share["JioMart"] == 75.0
    assert share["BigBasket"] == 0.0
    assert share.sum() == pytest.approx(100.0)
