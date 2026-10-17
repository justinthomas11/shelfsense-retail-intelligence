"""
Pure pandas helpers for the dashboard (no Streamlit or DB imports),
kept separate so they can be unit-tested offline.
"""

from decimal import Decimal

import pandas as pd

RETAILERS = ["BigBasket", "Blinkit", "Zepto", "JioMart"]
PRICE_COLUMNS = {
    "BigBasket": "bigbasket_price",
    "Blinkit": "blinkit_price",
    "Zepto": "zepto_price",
    "JioMart": "jiomart_price",
}


def coerce_decimals(df):
    """PostgreSQL NUMERIC arrives as Decimal objects; convert those columns to floats."""
    df = df.copy()
    for col in df.columns[df.dtypes == object]:
        sample = df[col].dropna()
        if not sample.empty and sample.map(lambda v: isinstance(v, Decimal)).all():
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def apply_filters(df, categories=None, retailers=None):
    """Filter on whichever of category_name / retailer_name columns the frame has."""
    if categories and "category_name" in df.columns:
        df = df[df["category_name"].isin(categories)]
    if retailers and "retailer_name" in df.columns:
        df = df[df["retailer_name"].isin(retailers)]
    return df


def premium_matrix(pricing):
    """
    Median % premium of the row retailer over the column retailer, across
    products both stock, from the wide vw_daily_competitor_pricing frame.
    The diagonal (a retailer against itself) is NaN.
    """
    matrix = pd.DataFrame(float("nan"), index=RETAILERS, columns=RETAILERS)
    for a in RETAILERS:
        for b in RETAILERS:
            pair = pricing[[PRICE_COLUMNS[a], PRICE_COLUMNS[b]]].dropna()
            pair = pair[pair[PRICE_COLUMNS[b]] > 0]
            if a == b or pair.empty:
                continue
            premium = (pair[PRICE_COLUMNS[a]] / pair[PRICE_COLUMNS[b]] - 1) * 100
            matrix.loc[a, b] = round(premium.median(), 2)
    return matrix


def cheapest_share(wins):
    """Share (%) of product-days on which each retailer was cheapest."""
    totals = wins.groupby("retailer_name")["days_cheapest"].sum()
    share = (totals / totals.sum() * 100).round(1)
    return share.reindex(RETAILERS).fillna(0.0).sort_values(ascending=False)

