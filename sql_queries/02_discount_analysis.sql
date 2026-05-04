/*
  02_discount_analysis.sql
  
  Business Problem: "Who is running the most aggressive promotions this week?"
  
  Description: 
  Aggregates the average discount percentage over the last 7 days 
  grouped by Category and Retailer to identify promotional trends.
*/

CREATE OR REPLACE VIEW vw_weekly_discount_analysis AS
WITH last_7_days AS (
    SELECT price_date 
    FROM fact_price_history
    GROUP BY price_date
    ORDER BY price_date DESC
    LIMIT 7
),
discount_data AS (
    SELECT 
        c.category_name,
        r.retailer_name,
        f.discount_pct,
        f.is_available
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE f.price_date IN (SELECT price_date FROM last_7_days)
      AND f.is_available = TRUE -- Only count discounts if the item is in stock
)
SELECT 
    category_name,
    ROUND(AVG(CASE WHEN retailer_name = 'BigBasket' THEN discount_pct END), 2) AS bigbasket_avg_discount,
    ROUND(AVG(CASE WHEN retailer_name = 'Blinkit' THEN discount_pct END), 2) AS blinkit_avg_discount,
    ROUND(AVG(CASE WHEN retailer_name = 'Zepto' THEN discount_pct END), 2) AS zepto_avg_discount,
    ROUND(AVG(CASE WHEN retailer_name = 'JioMart' THEN discount_pct END), 2) AS jiomart_avg_discount,
    ROUND(AVG(discount_pct), 2) AS market_avg_discount
FROM discount_data
GROUP BY category_name
ORDER BY market_avg_discount DESC;

-- Query to test the view:
-- SELECT * FROM vw_weekly_discount_analysis;
