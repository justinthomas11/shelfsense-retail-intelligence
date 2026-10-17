/*
  08_competitive_price_gap.sql

  Business Problem: "How much more expensive is retailer A than retailer B, product by product?"

  Description:
  Self-joins today's prices to produce every retailer pair for each product
  with absolute and percentage price gaps.

  Technique: Self-join + CTEs
*/

CREATE OR REPLACE VIEW vw_competitive_price_gap AS
WITH latest_date AS (
    SELECT MAX(price_date) AS max_date FROM fact_price_history
),
retailer_prices AS (
    SELECT
        f.product_id,
        p.product_name,
        p.brand,
        c.category_name,
        r.retailer_name,
        f.selling_price
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    CROSS JOIN latest_date ld
    WHERE f.price_date = ld.max_date
      AND f.is_available = TRUE
)
SELECT
    a.product_name,
    a.brand,
    a.category_name,
    a.retailer_name AS retailer_a,
    b.retailer_name AS retailer_b,
    a.selling_price AS price_a,
    b.selling_price AS price_b,
    ROUND(a.selling_price - b.selling_price, 2) AS price_diff,
    ROUND((a.selling_price - b.selling_price) / b.selling_price * 100, 2) AS pct_premium_a_over_b
FROM retailer_prices a
JOIN retailer_prices b
    ON a.product_id = b.product_id
    AND a.retailer_name < b.retailer_name  -- avoid duplicates and self-join
ORDER BY ABS(a.selling_price - b.selling_price) DESC;
