"""Executive View — where do we stand in the market?"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.analytics import cheapest_share, premium_matrix
from dashboard.charts import diverging_scale, retailer_colors, show, single_color
from dashboard.data import filtered, query, view

cats, rets = st.session_state["filters"]

st.title("Executive View")
st.caption("Market position, promotional intensity and inflation pass-through at a glance.")

# ── KPI row ─────────────────────────────────────────────────────────────
kpis = query("""
    WITH f AS (
        SELECT f.price_date, f.discount_pct, f.is_available
        FROM fact_price_history f
        JOIN dim_product p  ON f.product_id = p.product_id
        JOIN dim_category c ON p.category_id = c.category_id
        JOIN dim_retailer r ON f.retailer_id = r.retailer_id
        WHERE (cardinality(CAST(:cats AS text[])) = 0 OR c.category_name = ANY(CAST(:cats AS text[])))
          AND (cardinality(CAST(:rets AS text[])) = 0 OR r.retailer_name = ANY(CAST(:rets AS text[])))
    ),
    d AS (SELECT MAX(price_date) AS m FROM f)
    SELECT
        AVG(discount_pct) FILTER (WHERE is_available AND price_date > m - 7)                       AS disc_7d,
        AVG(discount_pct) FILTER (WHERE is_available AND price_date <= m - 7 AND price_date > m - 14) AS disc_prev_7d,
        100 * AVG((NOT is_available)::INT) FILTER (WHERE price_date > m - 30)                        AS oos_30d,
        100 * AVG((NOT is_available)::INT) FILTER (WHERE price_date <= m - 30 AND price_date > m - 60) AS oos_prev_30d
    FROM f, d
""", {"cats": list(cats), "rets": list(rets)}).iloc[0]

promos = filtered("vw_promotion_detection", cats, rets)
promos_today = promos[promos["price_date"] == promos["price_date"].max()] if not promos.empty else promos
# Market-wide question: compare against every retailer, so ignore the retailer filter
share = cheapest_share(filtered("vw_cheapest_retailer_frequency", cats, None))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Avg discount · last 7 days", f"{kpis.disc_7d:.1f}%",
          delta=f"{kpis.disc_7d - kpis.disc_prev_7d:+.1f} pts vs prior week",
          delta_color="off", border=True)
c2.metric("Stockout rate · last 30 days", f"{kpis.oos_30d:.1f}%",
          delta=f"{kpis.oos_30d - kpis.oos_prev_30d:+.1f} pts vs prior 30 days",
          delta_color="inverse", border=True)
c3.metric("Promotions detected today", f"{len(promos_today):,}",
          help="Day-over-day selling price drops greater than 15%", border=True)
leader = share[share > 0]
c4.metric("Most often cheapest", leader.index[0] if not leader.empty else "—",
          delta=f"{leader.iloc[0]:.0f}% of product-days" if not leader.empty else None,
          delta_color="off", border=True)

# ── Price position ──────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Who wins on price?")
    st.caption("Share of product-days on which each retailer had the lowest in-stock price.")
    colors = retailer_colors()
    shown = share[share > 0].sort_values()
    fig = go.Figure(go.Bar(
        x=shown.values, y=shown.index, orientation="h",
        marker_color=[colors[r] for r in shown.index],
        text=[f"{v:.1f}%" for v in shown.values], textposition="outside",
        hovertemplate="%{y}: %{x:.1f}% of product-days<extra></extra>",
    ))
    fig.update_xaxes(title="Share of product-days cheapest (%)", range=[0, max(shown.max() * 1.2, 1)])
    show(fig, legend=False)

with right:
    st.subheader("Price premium matrix")
    st.caption("Median % that the **row** retailer charges over the **column** retailer today, "
               "across products both stock. Red = row is pricier, blue = row is cheaper.")
    pricing = view("vw_daily_competitor_pricing")
    if cats:
        pricing = pricing[pricing["category_name"].isin(cats)]
    matrix = premium_matrix(pricing)
    bound = max(abs(matrix.min().min()), abs(matrix.max().max()), 1)
    fig = go.Figure(go.Heatmap(
        z=matrix.values, x=matrix.columns, y=matrix.index,
        colorscale=diverging_scale(), zmin=-bound, zmax=bound, zmid=0,
        text=[["—" if pd.isna(v) else f"{v:+.1f}%" for v in row] for row in matrix.values], texttemplate="%{text}",
        hovertemplate="%{y} vs %{x}: %{z:+.1f}%<extra></extra>",
        colorbar=dict(title="%", thickness=10), xgap=2, ygap=2,
    ))
    fig.update_yaxes(autorange="reversed")
    show(fig, legend=False)

# ── Inflation & demand ──────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Discount depth vs inflation")
    infl = filtered("vw_inflation_adjusted_pricing", cats, rets).dropna(subset=["yoy_inflation"])
    if infl.empty:
        st.info("No CPI data for the selected period.")
    else:
        month = infl["price_month"].max()
        latest = infl[infl["price_month"] == month].sort_values("avg_discount")
        st.caption(f"{month:%B %Y}. Where the discount exceeds YoY inflation, retailers are "
                   "absorbing price increases rather than passing them on.")
        fig = go.Figure([
            go.Bar(name="Avg discount", y=latest["category_name"], x=latest["avg_discount"],
                   orientation="h", marker_color=single_color(),
                   hovertemplate="%{y}<br>Avg discount: %{x:.1f}%<extra></extra>"),
            go.Bar(name="YoY CPI inflation", y=latest["category_name"], x=latest["yoy_inflation"],
                   orientation="h", marker_color="#8a8984",
                   hovertemplate="%{y}<br>YoY inflation: %{x:.1f}%<extra></extra>"),
        ])
        fig.update_layout(barmode="group", bargroupgap=0.1)
        fig.update_xaxes(title="%")
        show(fig, height=560)

with right:
    st.subheader("Demand signals")
    st.caption("Stockout rate over the last 30 days as a demand proxy. "
               "High stockouts with shallow discounts suggest strong organic demand.")
    demand = filtered("vw_category_demand_proxy", cats, rets)
    icons = {"Very High Demand": "🔴 Very high", "High Demand": "🟠 High",
             "Moderate Demand": "🟡 Moderate", "Normal": "⚪ Normal"}
    demand = demand.assign(signal=demand["demand_signal"].map(icons))
    st.dataframe(
        demand[["category_name", "retailer_name", "stockout_rate_pct", "avg_discount", "signal"]],
        hide_index=True, width="stretch", height=560,
        column_config={
            "category_name": "Category",
            "retailer_name": "Retailer",
            "stockout_rate_pct": st.column_config.ProgressColumn(
                "Stockout rate", format="%.1f%%", min_value=0,
                max_value=float(max(demand["stockout_rate_pct"].max(), 1))),
            "avg_discount": st.column_config.NumberColumn("Avg discount", format="%.1f%%"),
            "signal": "Demand signal",
        },
    )
