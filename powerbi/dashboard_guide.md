# Power BI Dashboard Guide

How to build the three ShelfSense dashboard views on top of the PostgreSQL analytical views.

## 1. Connect to the warehouse

1. Populate the database: `python scripts/setup_database.py --with-data`
2. Power BI Desktop → **Get Data → PostgreSQL database**
   - Server: `localhost:5432`
   - Database: `shelfsense`
   - Data connectivity mode: **Import** (the dataset is small; refresh daily after the pipeline runs)
3. In the Navigator, select the `vw_*` views listed below. Every view is pre-aggregated, so no Power Query transformations are needed beyond setting data types.

> Power BI needs the Npgsql provider for PostgreSQL. Recent versions of Power BI Desktop include it; older ones prompt you to install it.

## 2. Views per dashboard page

### Executive View — "Where do we stand in the market?"

| Visual | Source view | Fields |
|---|---|---|
| KPI cards: avg market discount, stockout rate, # promotions today | `vw_weekly_discount_analysis`, `vw_category_demand_proxy`, `vw_promotion_detection` | `market_avg_discount`, `stockout_rate_pct`, count of rows where `price_date` = latest |
| Cheapest-retailer share (donut) | `vw_cheapest_retailer_frequency` | Legend `retailer_name`, Values sum of `days_cheapest` |
| Price premium matrix (retailer A × retailer B) | `vw_competitive_price_gap` | Rows `retailer_a`, Columns `retailer_b`, Values avg of `pct_premium_a_over_b` |
| Inflation impact (clustered bar) | `vw_inflation_adjusted_pricing` | Axis `category_name`, Values `avg_discount` vs `yoy_inflation`, Tooltip `inflation_strategy` |
| Demand signal by category (table, conditional formatting) | `vw_category_demand_proxy` | `category_name`, `retailer_name`, `stockout_rate_pct`, `demand_signal` |

### Operational View — "What changed today?"

| Visual | Source view | Fields |
|---|---|---|
| Today's price comparison (table) | `vw_daily_competitor_pricing` | All columns; highlight the cell equal to `lowest_market_price` |
| Price-drop alerts (table, sorted by `pct_drop`) | `vw_promotion_detection` | Filter `price_date` = latest; `promotion_tier` as icon set |
| Stockout watchlist | `vw_30day_availability_tracker` | Top N by `out_of_stock_pct` |
| Most volatile SKUs | `vw_price_volatility` | Top 15 by `volatility_index_pct` |
| Slicers | — | `category_name`, `retailer_name`, `brand` |

### Trend View — "How are prices moving?"

| Visual | Source view | Fields |
|---|---|---|
| Category price index (line) | `vw_category_price_index` | Axis `price_date`, Values `price_index_7day_ma`, Legend `parent_category` |
| Monthly trend with MoM % (line + column) | `vw_monthly_price_trends` | `price_month`, `avg_price`, `mom_price_change_pct` |
| Week-over-week changes (heatmap matrix) | `vw_week_over_week_price_change` | Rows `category_name`, Columns `week_start`, Values avg `wow_price_change_pct` |
| Day-of-week discount pattern (heatmap) | `vw_discount_by_day_of_week` | Rows `retailer_name`, day columns as values |
| Promotion timeline (Gantt-style bar) | `vw_promotional_calendar` | `promo_start_date` → `promo_end_date` per `retailer_name` |

## 3. Useful DAX measures

```DAX
Avg Market Discount % =
AVERAGE ( vw_weekly_discount_analysis[market_avg_discount] )

Cheapest Share % =
DIVIDE (
    SUM ( vw_cheapest_retailer_frequency[days_cheapest] ),
    CALCULATE ( SUM ( vw_cheapest_retailer_frequency[days_cheapest] ), ALL ( vw_cheapest_retailer_frequency[retailer_name] ) )
)

Promotions Today =
CALCULATE (
    COUNTROWS ( vw_promotion_detection ),
    vw_promotion_detection[price_date] = MAX ( vw_promotion_detection[price_date] )
)

Real vs Nominal Gap % =
DIVIDE (
    AVERAGE ( vw_inflation_adjusted_pricing[nominal_price] )
        - AVERAGE ( vw_inflation_adjusted_pricing[real_price_adjusted] ),
    AVERAGE ( vw_inflation_adjusted_pricing[nominal_price] )
)
```

## 4. Theme

Use one consistent color per retailer across every page:

| Retailer | Hex |
|---|---|
| BigBasket | `#84C225` |
| Blinkit | `#F8CB46` |
| Zepto | `#5A1E96` |
| JioMart | `#0078AD` |

## 5. Refresh

The pipeline (`python pipeline/scheduler.py`) loads new prices every morning at 06:00 IST. Schedule the Power BI refresh after that, either manually in Desktop or through a gateway in Power BI Service. The views are computed at query time, so they need no separate refresh.

Save exported screenshots of each page to `powerbi/screenshots/`. `.pbix` files are gitignored.
