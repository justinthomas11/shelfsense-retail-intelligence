/*
  04_price_volatility.sql
  
  Business Problem: "Which products fluctuate in price the most?"
  
  Description: 
  Uses standard deviation over the last 30 days to measure the volatility 
  of selling prices, allowing buyers to identify items that need closer 
  price monitoring.
*/

CREATE OR REPLACE VIEW vw_price_volatility AS
WITH last_30_days AS (
    SELECT price_date 
    FROM fact_price_history
    GROUP BY price_date
    ORDER BY price_date DESC
    LIMIT 30
),
price_stats AS (
    SELECT 
        f.product_id,
        f.retailer_id,
        MIN(f.selling_price) AS min_price,
        MAX(f.selling_price) AS max_price,
        AVG(f.selling_price) AS avg_price,
        STDDEV_SAMP(f.selling_price) AS price_stddev
    FROM fact_price_history f
    WHERE f.price_date IN (SELECT price_date FROM last_30_days)
      AND f.is_available = TRUE
    GROUP BY f.product_id, f.retailer_id
)
SELECT 
    p.product_name,
    c.category_name,
    r.retailer_name,
    ROUND(s.min_price, 2) AS min_price_30d,
    ROUND(s.max_price, 2) AS max_price_30d,
    ROUND(s.avg_price, 2) AS avg_price_30d,
    -- Coefficient of Variation (CV) = (Standard Deviation / Mean) * 100
    -- This normalizes volatility so we can compare a Rs. 10 item to a Rs. 1000 item
    ROUND((s.price_stddev / s.avg_price) * 100, 2) AS volatility_index_pct
FROM price_stats s
JOIN dim_product p ON s.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON s.retailer_id = r.retailer_id
WHERE s.price_stddev IS NOT NULL
ORDER BY volatility_index_pct DESC;

-- Query to test the view:
-- SELECT * FROM vw_price_volatility LIMIT 20;
