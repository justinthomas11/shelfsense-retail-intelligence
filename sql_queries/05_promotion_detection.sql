/*
  05_promotion_detection.sql

  Business Problem: "Which products just went on promotion?"

  Description:
  Flags day-over-day selling price drops greater than 15% using LAG(),
  tiering them into 'Promotion' and 'Deep Promotion'.

  Technique: LAG() window function
*/

CREATE OR REPLACE VIEW vw_promotion_detection AS
WITH price_changes AS (
    SELECT
        f.product_id,
        f.retailer_id,
        p.product_name,
        p.brand,
        c.category_name,
        r.retailer_name,
        f.price_date,
        f.selling_price,
        LAG(f.selling_price) OVER (
            PARTITION BY f.product_id, f.retailer_id
            ORDER BY f.price_date
        ) AS prev_day_price
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE f.is_available = TRUE
)
SELECT
    product_name,
    brand,
    category_name,
    retailer_name,
    price_date,
    prev_day_price,
    selling_price,
    ROUND((prev_day_price - selling_price) / prev_day_price * 100, 2) AS pct_drop,
    CASE
        WHEN (prev_day_price - selling_price) / prev_day_price > 0.25 THEN 'Deep Promotion'
        WHEN (prev_day_price - selling_price) / prev_day_price > 0.15 THEN 'Promotion'
    END AS promotion_tier
FROM price_changes
WHERE prev_day_price IS NOT NULL
  AND (prev_day_price - selling_price) / prev_day_price > 0.15
ORDER BY price_date DESC, pct_drop DESC;
