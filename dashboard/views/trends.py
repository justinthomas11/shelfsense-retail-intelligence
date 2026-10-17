"""Trend View — how are prices and promotions moving over time?"""

from datetime import timedelta

import plotly.graph_objects as go
import streamlit as st

from dashboard.analytics import RETAILERS
from dashboard.charts import (MAX_SERIES, SEQUENTIAL_BLUE, categorical_colors,
                              diverging_scale, retailer_colors, show)
from dashboard.data import filtered, query

cats, rets = st.session_state["filters"]
shown_retailers = rets or RETAILERS

st.title("Trend View")
st.caption("Price indices, discount trends and the promotional calendar over the last 90 days.")

# ── Price index ─────────────────────────────────────────────────────────
st.subheader("Price index (day 1 = 100)")
idx = filtered("vw_category_price_index", cats, None)
if cats:
    series_col, series = "category_name", cats[:MAX_SERIES]
    if len(cats) > MAX_SERIES:
        st.warning(f"Showing the first {MAX_SERIES} selected categories.")
    st.caption("7-day moving average per selected category.")
else:
    series_col = "parent_category"
    series = sorted(idx["parent_category"].unique())
    st.caption("7-day moving average, averaged by parent category. Pick categories in the sidebar to drill in.")
idx = idx.groupby(["price_date", series_col], as_index=False)["price_index_7day_ma"].mean()

colors = categorical_colors(series)
fig = go.Figure()
for name in series:
    s = idx[idx[series_col] == name]
    fig.add_trace(go.Scatter(x=s["price_date"], y=s["price_index_7day_ma"], name=name, mode="lines",
                             line=dict(color=colors[name]),
                             hovertemplate=f"{name}: %{{y:.1f}}<extra></extra>"))
fig.add_hline(y=100, line_width=1, line_dash="dot", line_color="#8a8984")
fig.update_layout(hovermode="x unified")
fig.update_yaxes(title="Index")
show(fig, height=380)

# ── Discount trend by retailer ──────────────────────────────────────────
st.subheader("Weekly average discount by retailer")
weekly = query("""
    SELECT DATE_TRUNC('week', f.price_date)::DATE AS week_start, r.retailer_name,
           AVG(f.discount_pct) AS avg_discount
    FROM fact_price_history f
    JOIN dim_product p  ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE f.is_available
      AND (cardinality(CAST(:cats AS text[])) = 0 OR c.category_name = ANY(CAST(:cats AS text[])))
    GROUP BY 1, 2
    ORDER BY 1
""", {"cats": list(cats)})
colors = retailer_colors()
fig = go.Figure()
for retailer in shown_retailers:
    w = weekly[weekly["retailer_name"] == retailer]
    fig.add_trace(go.Scatter(x=w["week_start"], y=w["avg_discount"], name=retailer, mode="lines+markers",
                             line=dict(color=colors[retailer]), marker=dict(size=8),
                             hovertemplate=f"{retailer}: %{{y:.1f}}%<extra></extra>"))
fig.update_layout(hovermode="x unified")
fig.update_xaxes(title="Week starting")
fig.update_yaxes(title="Avg discount (%)", ticksuffix="%")
show(fig, height=360)

# ── Heatmaps ────────────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Week-over-week price change")
    st.caption("Average % change in selling price vs the previous week. Blue = cheaper, red = pricier.")
    wow = filtered("vw_week_over_week_price_change", cats, rets)
    grid = wow.pivot_table(index="category_name", columns="week_start",
                           values="wow_price_change_pct", aggfunc="mean")
    bound = max(abs(grid.min().min()), abs(grid.max().max()), 0.5)
    fig = go.Figure(go.Heatmap(
        z=grid.values, x=[d.strftime("%d %b") for d in grid.columns], y=grid.index,
        colorscale=diverging_scale(), zmin=-bound, zmax=bound, zmid=0, xgap=2, ygap=2,
        hovertemplate="%{y}, week of %{x}: %{z:+.2f}%<extra></extra>",
        colorbar=dict(title="%", thickness=10),
    ))
    fig.update_yaxes(autorange="reversed")
    show(fig, height=560, legend=False)

with right:
    st.subheader("Discount by day of week")
    st.caption("Average discount per retailer and weekday. Darker = deeper discounts.")
    dow = filtered("vw_discount_by_day_of_week", cats, rets)
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    grid = dow.groupby("retailer_name")[[f"{d}_avg_disc" for d in days]].mean()
    grid = grid.reindex([r for r in RETAILERS if r in grid.index])
    fig = go.Figure(go.Heatmap(
        z=grid.values, x=[d[:3].title() for d in days], y=grid.index,
        colorscale=[[i / (len(SEQUENTIAL_BLUE) - 1), c] for i, c in enumerate(SEQUENTIAL_BLUE)],
        text=grid.round(1).values, texttemplate="%{text}%", xgap=2, ygap=2,
        hovertemplate="%{y}, %{x}: %{z:.1f}%<extra></extra>",
        colorbar=dict(title="%", thickness=10),
    ))
    fig.update_yaxes(autorange="reversed")
    show(fig, height=560, legend=False)

# ── Promotional calendar ────────────────────────────────────────────────
st.subheader("Promotional calendar · last 30 days")
st.caption("Runs of 2+ consecutive days with discounts above 15%, reconstructed with gap-and-island "
           "detection. Showing the 30 longest.")
promos = filtered("vw_promotional_calendar", cats, rets)
if promos.empty:
    st.info("No promotions for the current filters.")
else:
    cutoff = promos["promo_end_date"].max() - timedelta(days=30)
    promos = (promos[promos["promo_end_date"] >= cutoff]
              .sort_values(["promo_duration_days", "avg_promo_discount"], ascending=False)
              .head(30)
              .sort_values("promo_start_date"))
    promos["label"] = promos["product_name"] + " · " + promos["retailer_name"]
    fig = go.Figure()
    for retailer in shown_retailers:
        p = promos[promos["retailer_name"] == retailer]
        if p.empty:
            continue
        fig.add_trace(go.Bar(
            base=p["promo_start_date"],
            x=[timedelta(days=int(d)).total_seconds() * 1000 for d in p["promo_duration_days"]],
            y=p["label"], orientation="h", name=retailer, marker_color=colors[retailer],
            customdata=p[["promo_start_date", "promo_end_date", "promo_duration_days", "avg_promo_discount"]],
            hovertemplate="%{y}<br>%{customdata[0]|%d %b} – %{customdata[1]|%d %b} "
                          "(%{customdata[2]} days)<br>Avg discount %{customdata[3]:.1f}%<extra></extra>",
        ))
    fig.update_xaxes(type="date")
    fig.update_yaxes(autorange="reversed", title=None)
    show(fig, height=max(360, 22 * len(promos) + 80))
