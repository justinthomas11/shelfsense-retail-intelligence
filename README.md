<div align="center">

# ShelfSense

### Competitive Retail Price Intelligence for Indian Grocery & Quick-Commerce

**Daily price tracking · Promotion detection · Inflation-adjusted analytics · Interactive dashboards**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![CI](https://img.shields.io/github/actions/workflow/status/justinthomas11/shelfsense-retail-intelligence/ci.yml?branch=main&style=for-the-badge&label=CI)](https://github.com/justinthomas11/shelfsense-retail-intelligence/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## Overview

Pricing is one of the biggest levers a retailer has on revenue and margin. Large retailers run dedicated teams to monitor competitor prices, spot promotions, and judge whether price moves are driven by strategy or by inflation.

**ShelfSense is an end-to-end version of that workflow** for four Indian retailers: **BigBasket, Blinkit, Zepto and JioMart**. It covers:

- **Ingestion**: modular scrapers plus a scheduled pipeline that validates, deduplicates and loads prices daily
- **Warehouse**: a PostgreSQL star schema holding price history and CPI inflation data
- **Analytics**: 20 SQL views built with window functions, CTEs, and gap-and-island detection
- **Presentation**: a three-page Streamlit dashboard, an EDA notebook and a Power BI build guide
- **Quality**: 63 tests and a CI pipeline that builds the full stack on every push

> **About the data:** retailer sites change markup often and some block automated traffic, so the bundled dataset comes from a simulator. It covers 75 SKUs × 4 retailers × 90 days (27,000 rows) and models each retailer's discount strategy, weekend and sale-event promotions, stockouts and inflation. The CPI series is also simulated. The findings below describe this dataset, not real retailer behaviour.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                         │
│  BigBasket · Blinkit · Zepto · JioMart  │  CPI series        │
│  (scrapers, or simulator as fallback)   │  (simulated)       │
└──────────────────────────────┬───────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                      INGESTION PIPELINE                      │
│  Extract → Validate → Deduplicate → Upsert                   │
│  APScheduler daily run · per-retailer fallback · run logs    │
└──────────────────────────────┬───────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  POSTGRESQL STAR SCHEMA                      │
│  dim_retailer · dim_product · dim_category                   │
│  fact_price_history (daily) · fact_macro_cpi (monthly)       │
└──────────────────────────────┬───────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  ANALYTICAL SQL LAYER (20 views)             │
│  Promotions · Price gaps · Volatility · Elasticity           │
│  Demand proxies · Inflation pass-through · Price indices     │
└──────────────────────────────┬───────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                        PRESENTATION                          │
│  Streamlit dashboard · Jupyter EDA · Power BI guide          │
└──────────────────────────────────────────────────────────────┘
```

---

## Dashboard

A Streamlit + Plotly app with three pages. Category and retailer filters are shared across all of them.

| Page | Answers | Contents |
|---|---|---|
| **Executive** | *Where do we stand in the market?* | KPI row, cheapest-retailer share, retailer price-premium matrix, discount vs CPI inflation, demand signals |
| **Operational** | *What changed today?* | Searchable price board with the lowest price highlighted, per-product price history, price-drop alerts, stockout watchlist, most volatile SKUs |
| **Trends** | *How are prices moving?* | Category price index, weekly discount by retailer, week-over-week and day-of-week heatmaps, promotional calendar timeline |

```bash
streamlit run dashboard/app.py
```

---

## Sample Findings

These come from the bundled simulated dataset and show the kind of output the platform produces:

- **JioMart wins on price:** it had the lowest in-stock price on **66%** of product-days, against Blinkit 17%, Zepto 11% and BigBasket 6%.
- **The gap is about 11–12%:** the median basket at BigBasket, Blinkit or Zepto costs 11–12% more than at JioMart. The other three retailers sit within about 2% of each other.
- **Discount depth separates the strategies:** average discounts are JioMart 21.9%, Blinkit 17.6%, Zepto 15.2% and BigBasket 12.9%.
- **Weekends are promotional:** all four retailers discount deepest on Saturday and Sunday. For example, JioMart goes from 19% on Monday to 25.7% on Saturday.
- **Availability is high:** 3.3% of retailer-product-days were out of stock over the last 30 days.

---

## SQL Analytics

All 20 views live in [`database/views/analytical_views.sql`](database/views/analytical_views.sql). Each one is also a standalone, documented file in [`sql_queries/`](sql_queries/) that states the business question it answers.

| Analysis | Technique |
|---|---|
| Promotion detection (>15% day-over-day drop) | `LAG()` window function |
| Week-over-week price change | `LAG()` + `DATE_TRUNC` |
| Competitive price gap between retailers | Self-join + CTEs |
| Promotional calendar reconstruction | Gap-and-island detection |
| Cheapest-retailer frequency | `RANK()` + conditional counting |
| Inflation-adjusted pricing | CPI join + real-price calculation |
| Price elasticity estimate by category | `LAG()` over daily aggregates |
| Cross-category price correlation | Closed-form Pearson via self-join |
| Weekend vs weekday discounting | `EXTRACT(DOW)` + `CASE WHEN` |
| Category price index (day 1 = 100) | `FIRST_VALUE()` + 7-day moving average |

<details>
<summary><b>Example: promotion detection</b></summary>

```sql
WITH price_changes AS (
    SELECT
        p.product_name,
        r.retailer_name,
        f.price_date,
        f.selling_price,
        LAG(f.selling_price) OVER (
            PARTITION BY f.product_id, f.retailer_id
            ORDER BY f.price_date
        ) AS prev_day_price
    FROM fact_price_history f
    JOIN dim_product p  ON f.product_id = p.product_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE f.is_available
)
SELECT
    product_name,
    retailer_name,
    price_date,
    prev_day_price,
    selling_price,
    ROUND((prev_day_price - selling_price) / prev_day_price * 100, 2) AS pct_drop
FROM price_changes
WHERE prev_day_price IS NOT NULL
  AND (prev_day_price - selling_price) / prev_day_price > 0.15
ORDER BY price_date DESC, pct_drop DESC;
```

</details>

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 16 (local install or Docker)

### Setup

```bash
git clone https://github.com/justinthomas11/shelfsense-retail-intelligence.git
cd shelfsense-retail-intelligence

python -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Database connection
cp config/db_config.example.py config/db_config.py
cp .env.example .env              # edit credentials if needed

# Start PostgreSQL (skip if installed locally)
docker compose up -d

# Create tables, load 90 days of simulated data, build all 20 views
python scripts/setup_database.py --with-data

# Launch the dashboard
streamlit run dashboard/app.py
```

### Daily pipeline

```bash
python pipeline/scheduler.py --once --source simulate      # offline run
python pipeline/scheduler.py --once --fallback-simulate    # live scrapers, simulate blocked retailers
python pipeline/scheduler.py --hour 6 --minute 0           # run every day at 06:00 IST
```

Live scraping of Blinkit and Zepto also needs `playwright install chromium`. Run logs go to `logs/pipeline.log`.

### Tests

```bash
pytest
```

Unit tests run offline. Integration tests check that every view returns rows, plus data-quality rules; they run when a database is reachable and are skipped otherwise. CI runs the whole stack on every push: it builds the warehouse on PostgreSQL 16, runs the pipeline, then runs all tests.

---

## Project Structure

```
shelfsense-retail-intelligence/
├── config/              # DB connection template (reads .env)
├── database/
│   ├── schema/          # DDL + dimension seed data
│   └── views/           # 20 analytical views
├── scrapers/            # BaseScraper + one module per retailer
├── data_simulator/      # product catalog, price simulator, CPI loader
├── pipeline/            # scheduler, validation, loader, simulated source
├── sql_queries/         # 20 standalone, documented queries
├── dashboard/           # Streamlit app (Executive / Operational / Trends)
├── notebooks/           # Jupyter EDA
├── powerbi/             # Power BI build guide
├── scripts/             # one-command database setup
├── tests/               # unit + integration tests
└── .github/workflows/   # CI
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Database | PostgreSQL 16 (star schema) |
| Ingestion | requests, BeautifulSoup, Playwright, APScheduler |
| Processing | pandas, NumPy |
| DB access | SQLAlchemy, psycopg2 |
| Dashboard | Streamlit, Plotly |
| Testing & CI | pytest, GitHub Actions |
| BI | Power BI (build guide) |

---

## Roadmap

- [ ] Validate scraper selectors against the live storefronts
- [ ] Load real CPI data from MoSPI / data.gov.in
- [ ] Deploy the dashboard publicly (Streamlit Community Cloud + hosted Postgres)
- [ ] Build the Power BI report from [`powerbi/dashboard_guide.md`](powerbi/dashboard_guide.md)

---

## License

MIT. See [LICENSE](LICENSE).
