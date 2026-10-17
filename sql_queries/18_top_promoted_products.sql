/*
  18_top_promoted_products.sql

  Business Problem: "Which products are promoted most frequently?"

  Description:
  Counts heavy-promotion days (discount > 15%) over the last 30 days and
  ranks product/retailer pairs with PERCENT_RANK().

  Technique: Conditional aggregation + PERCENT_RANK
*/

CREATE OR REPLACE VIEW vw_top_promoted_products AS
WITH last_30_days AS (
    SELECT price_date
    FROM fact_price_history
    GROUP BY price_date
    ORDER BY price_date DESC
    LIMIT 30
),
promo_stats AS (
    SELECT
        f.product_id,
        f.retailer_id,
        COUNT(*) AS total_days,
        SUM(CASE WHEN f.discount_pct > 15 THEN 1 ELSE 0 END) AS heavy_promo_days,
        ROUND(AVG(f.discount_pct), 2) AS avg_discount,
        ROUND(MAX(f.discount_pct), 2) AS max_discount,
        ROUND(AVG(f.selling_price), 2) AS avg_selling_price
    FROM fact_price_history f
    WHERE f.price_date IN (SELECT price_date FROM last_30_days)
      AND f.is_available = TRUE
    GROUP BY f.product_id, f.retailer_id
)
SELECT
    p.product_name,
    p.brand,
    c.category_name,
    r.retailer_name,
    ps.total_days,
    ps.heavy_promo_days,
    ROUND(ps.heavy_promo_days::NUMERIC / ps.total_days * 100, 1) AS promo_frequency_pct,
    ps.avg_discount,
    ps.max_discount,
    ps.avg_selling_price,
    PERCENT_RANK() OVER (ORDER BY ps.heavy_promo_days::NUMERIC / ps.total_days) AS promo_percentile
FROM promo_stats ps
JOIN dim_product p ON ps.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON ps.retailer_id = r.retailer_id
WHERE ps.heavy_promo_days > 0
ORDER BY promo_frequency_pct DESC;
