/*
  03_availability_tracker.sql
  
  Business Problem: "What items are we losing sales on due to stockouts?"
  
  Description: 
  Calculates the Out-of-Stock (OOS) percentage over the last 30 days 
  for every product/retailer combination.
*/

CREATE OR REPLACE VIEW vw_30day_availability_tracker AS
WITH last_30_days AS (
    SELECT price_date 
    FROM fact_price_history
    GROUP BY price_date
    ORDER BY price_date DESC
    LIMIT 30
)
SELECT 
    p.product_name,
    p.brand,
    c.category_name,
    r.retailer_name,
    COUNT(*) AS total_days_checked,
    SUM(CASE WHEN f.is_available = FALSE THEN 1 ELSE 0 END) AS days_out_of_stock,
    ROUND(
        (SUM(CASE WHEN f.is_available = FALSE THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100, 
    2) AS out_of_stock_pct
FROM fact_price_history f
JOIN dim_product p ON f.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON f.retailer_id = r.retailer_id
WHERE f.price_date IN (SELECT price_date FROM last_30_days)
GROUP BY 
    p.product_name,
    p.brand,
    c.category_name,
    r.retailer_name
HAVING SUM(CASE WHEN f.is_available = FALSE THEN 1 ELSE 0 END) > 0
ORDER BY out_of_stock_pct DESC;

-- Query to test the view:
-- SELECT * FROM vw_30day_availability_tracker LIMIT 20;
