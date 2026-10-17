"""Operational View — what changed today, and what needs attention?"""

from datetime import timedelta

import plotly.graph_objects as go
import streamlit as st

from dashboard.analytics import PRICE_COLUMNS, RETAILERS
from dashboard.charts import retailer_colors, show
from dashboard.data import filtered, query, view

cats, rets = st.session_state["filters"]
shown_retailers = rets or RETAILERS

st.title("Operational View")
st.caption("Today's shelf prices, fresh price drops, stockouts and the SKUs that need watching.")

# ── Today's price board ─────────────────────────────────────────────────
st.subheader("Today's price board")
board = view("vw_daily_competitor_pricing")
if cats:
    board = board[board["category_name"].isin(cats)]
search = st.text_input("Search products or brands", placeholder="e.g. Amul, basmati, detergent")
if search:
    mask = (board["product_name"].str.contains(search, case=False)
            | board["brand"].str.contains(search, case=False))
    board = board[mask]

price_cols = [PRICE_COLUMNS[r] for r in shown_retailers]
board = board[["product_name", "brand", "category_name", *price_cols, "lowest_market_price"]]
st.caption("Lowest in-stock price per product is highlighted. *None* = out of stock today.")
st.dataframe(
    board.style.highlight_min(subset=price_cols, axis=1, props="background-color: #cde2fb; color: #0b0b0b; font-weight: 600")
         .format("₹{:,.2f}", subset=[*price_cols, "lowest_market_price"], na_rep=""),
    hide_index=True, width="stretch", height=380,
    column_config={
        "product_name": "Product", "brand": "Brand", "category_name": "Category",
        **{PRICE_COLUMNS[r]: r for r in shown_retailers},
        "lowest_market_price": "Lowest",
    },
)

# ── Price history drill-down ────────────────────────────────────────────
st.subheader("Price history")
products = board["product_name"].tolist() or view("vw_daily_competitor_pricing")["product_name"].tolist()
product = st.selectbox("Product", products)
history = query("""
    SELECT f.price_date, r.retailer_name,
           CASE WHEN f.is_available THEN f.selling_price END AS selling_price,
           f.mrp, f.discount_pct, f.is_available
    FROM fact_price_history f
    JOIN dim_product p  ON f.product_id = p.product_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE p.product_name = :product
    ORDER BY f.price_date
""", {"product": product})
history = history[history["retailer_name"].isin(shown_retailers)]

colors = retailer_colors()
fig = go.Figure()
for retailer in shown_retailers:
    h = history[history["retailer_name"] == retailer]
    fig.add_trace(go.Scatter(
        x=h["price_date"], y=h["selling_price"], name=retailer, mode="lines",
        line=dict(color=colors[retailer]), connectgaps=False,
        customdata=h[["mrp", "discount_pct"]],
        hovertemplate=f"{retailer}: ₹%{{y:,.2f}} (MRP ₹%{{customdata[0]:,.2f}}, "
                      f"%{{customdata[1]:.1f}}% off)<extra></extra>",
    ))
fig.update_layout(hovermode="x unified")
fig.update_yaxes(title="Selling price (₹)", tickprefix="₹")
st.caption("Gaps mark days the product was out of stock at that retailer.")
show(fig, height=360)

# ── Alerts ──────────────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Price-drop alerts · last 7 days")
    drops = filtered("vw_promotion_detection", cats, rets)
    if not drops.empty:
        drops = drops[drops["price_date"] > drops["price_date"].max() - timedelta(days=7)]
    tiers = {"Deep Promotion": "🔻 Deep", "Promotion": "▼ Promo"}
    st.dataframe(
        drops.assign(tier=drops["promotion_tier"].map(tiers))[
            ["price_date", "product_name", "retailer_name", "selling_price", "pct_drop", "tier"]],
        hide_index=True, width="stretch", height=420,
        column_config={
            "price_date": st.column_config.DateColumn("Date", format="DD MMM"),
            "product_name": "Product", "retailer_name": "Retailer",
            "selling_price": st.column_config.NumberColumn("Now", format="₹%.2f"),
            "pct_drop": st.column_config.NumberColumn("Drop", format="%.1f%%"),
            "tier": st.column_config.TextColumn("Tier", help="Deep: >25% drop · Promo: >15% drop"),
        },
    )

with right:
    st.subheader("Stockout watchlist · last 30 days")
    oos = filtered("vw_30day_availability_tracker", cats, rets).head(25)
    st.dataframe(
        oos[["product_name", "retailer_name", "days_out_of_stock", "out_of_stock_pct"]],
        hide_index=True, width="stretch", height=420,
        column_config={
            "product_name": "Product", "retailer_name": "Retailer",
            "days_out_of_stock": st.column_config.NumberColumn("Days OOS"),
            "out_of_stock_pct": st.column_config.ProgressColumn(
                "Out of stock", format="%.1f%%", min_value=0,
                max_value=float(max(oos["out_of_stock_pct"].max(), 1)) if not oos.empty else 100.0),
        },
    )

st.subheader("Most volatile SKUs · last 30 days")
st.caption("Coefficient of variation of the selling price. These SKUs need the closest monitoring.")
vol = filtered("vw_price_volatility", cats, rets).head(20)
st.dataframe(
    vol[["product_name", "category_name", "retailer_name", "min_price_30d", "max_price_30d", "volatility_index_pct"]],
    hide_index=True, width="stretch",
    column_config={
        "product_name": "Product", "category_name": "Category", "retailer_name": "Retailer",
        "min_price_30d": st.column_config.NumberColumn("Min", format="₹%.2f"),
        "max_price_30d": st.column_config.NumberColumn("Max", format="₹%.2f"),
        "volatility_index_pct": st.column_config.ProgressColumn(
            "Volatility (CV)", format="%.2f%%", min_value=0,
            max_value=float(max(vol["volatility_index_pct"].max(), 1)) if not vol.empty else 10.0),
    },
)
