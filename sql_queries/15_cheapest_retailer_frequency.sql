/*
  15_cheapest_retailer_frequency.sql

  Business Problem: "Who wins on price most often?"

  Description:
  Ranks retailers per product per day with RANK() and counts how often
  each retailer is the cheapest.

  Technique: RANK() window function + conditional counting
*/

CREATE OR REPLACE VIEW vw_cheapest_retailer_frequency AS
WITH daily_prices AS (
    SELECT
        f.price_date,
        f.product_id,
        r.retailer_name,
        f.selling_price,
        RANK() OVER (
            PARTITION BY f.price_date, f.product_id
            ORDER BY f.selling_price ASC
        ) AS price_rank
    FROM fact_price_history f
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE f.is_available = TRUE
),
wins AS (
    SELECT
        product_id,
        retailer_name,
        COUNT(*) AS days_cheapest
    FROM daily_prices
    WHERE price_rank = 1
    GROUP BY product_id, retailer_name
)
SELECT
    p.product_name,
    p.brand,
    c.category_name,
    w.retailer_name,
    w.days_cheapest,
    ROUND(w.days_cheapest::NUMERIC / SUM(w.days_cheapest) OVER (PARTITION BY w.product_id) * 100, 1)
        AS pct_days_cheapest
FROM wins w
JOIN dim_product p ON w.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
ORDER BY c.category_name, p.product_name, pct_days_cheapest DESC;
