/*
  20_category_price_index.sql

  Business Problem: "How have category prices moved relative to the start of the period?"

  Description:
  Normalizes each category's daily average price to 100 on day one using
  FIRST_VALUE(), with a 7-day moving average for smoothing.

  Technique: First-value normalization + window function
*/

CREATE OR REPLACE VIEW vw_category_price_index AS
WITH daily_category_price AS (
    SELECT
        f.price_date,
        c.category_name,
        c.parent_category,
        ROUND(AVG(f.selling_price), 2) AS avg_price
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    WHERE f.is_available = TRUE
    GROUP BY f.price_date, c.category_name, c.parent_category
),
with_base AS (
    SELECT
        *,
        FIRST_VALUE(avg_price) OVER (
            PARTITION BY category_name
            ORDER BY price_date ASC
        ) AS base_price
    FROM daily_category_price
)
SELECT
    price_date,
    parent_category,
    category_name,
    avg_price,
    base_price,
    -- Index: Day 1 = 100, subsequent days relative to that
    ROUND((avg_price / NULLIF(base_price, 0)) * 100, 2) AS price_index,
    -- Rolling 7-day average of the index for smoothing
    ROUND(AVG(avg_price / NULLIF(base_price, 0) * 100) OVER (
        PARTITION BY category_name
        ORDER BY price_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS price_index_7day_ma
FROM with_base
ORDER BY category_name, price_date;
