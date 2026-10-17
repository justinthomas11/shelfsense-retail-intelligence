/*
  16_brand_price_consistency.sql

  Business Problem: "Is a brand priced consistently across retailers?"

  Description:
  Measures the spread between the cheapest and priciest retailer for each
  brand over the last week and names both retailers.

  Technique: Aggregation with spread analysis
*/

CREATE OR REPLACE VIEW vw_brand_price_consistency AS
WITH latest_date AS (
    SELECT MAX(price_date) AS max_date FROM fact_price_history
),
brand_prices AS (
    SELECT
        p.brand,
        c.category_name,
        r.retailer_name,
        ROUND(AVG(f.selling_price), 2) AS avg_price,
        COUNT(DISTINCT p.product_id) AS num_products
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    CROSS JOIN latest_date ld
    WHERE f.price_date >= ld.max_date - INTERVAL '7 days'
      AND f.is_available = TRUE
    GROUP BY p.brand, c.category_name, r.retailer_name
)
SELECT
    brand,
    category_name,
    COUNT(DISTINCT retailer_name) AS retailers_carrying,
    ROUND(MIN(avg_price), 2) AS cheapest_avg,
    ROUND(MAX(avg_price), 2) AS priciest_avg,
    ROUND(MAX(avg_price) - MIN(avg_price), 2) AS price_spread,
    ROUND((MAX(avg_price) - MIN(avg_price)) / NULLIF(MIN(avg_price), 0) * 100, 2) AS spread_pct,
    -- Which retailer is cheapest / priciest for this brand
    (SELECT bp2.retailer_name FROM brand_prices bp2
     WHERE bp2.brand = bp.brand AND bp2.category_name = bp.category_name
     ORDER BY bp2.avg_price ASC LIMIT 1) AS cheapest_at,
    (SELECT bp3.retailer_name FROM brand_prices bp3
     WHERE bp3.brand = bp.brand AND bp3.category_name = bp.category_name
     ORDER BY bp3.avg_price DESC LIMIT 1) AS priciest_at
FROM brand_prices bp
GROUP BY brand, category_name
HAVING COUNT(DISTINCT retailer_name) >= 2  -- compare only if available at 2+ retailers
ORDER BY spread_pct DESC;
