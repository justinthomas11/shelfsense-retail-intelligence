/*
  01_daily_competitor_pricing.sql
  
  Business Problem: "Are we cheaper than our competitors today?"
  
  Description: 
  Creates a view that looks at the most recent date in the dataset
  and pivots the selling prices so that each row is a product and 
  each column is a retailer's price.
*/

CREATE OR REPLACE VIEW vw_daily_competitor_pricing AS
WITH latest_date AS (
    SELECT MAX(price_date) AS max_date 
    FROM fact_price_history
),
latest_prices AS (
    SELECT 
        f.product_id,
        p.product_name,
        p.brand,
        c.category_name,
        r.retailer_name,
        f.selling_price,
        f.is_available
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    CROSS JOIN latest_date ld
    WHERE f.price_date = ld.max_date
)
SELECT 
    product_name,
    brand,
    category_name,
    MAX(CASE WHEN retailer_name = 'BigBasket' THEN selling_price END) AS bigbasket_price,
    MAX(CASE WHEN retailer_name = 'Blinkit' THEN selling_price END) AS blinkit_price,
    MAX(CASE WHEN retailer_name = 'Zepto' THEN selling_price END) AS zepto_price,
    MAX(CASE WHEN retailer_name = 'JioMart' THEN selling_price END) AS jiomart_price,
    -- Calculate the lowest price across all retailers for this item
    LEAST(
        MAX(CASE WHEN retailer_name = 'BigBasket' THEN selling_price END),
        MAX(CASE WHEN retailer_name = 'Blinkit' THEN selling_price END),
        MAX(CASE WHEN retailer_name = 'Zepto' THEN selling_price END),
        MAX(CASE WHEN retailer_name = 'JioMart' THEN selling_price END)
    ) AS lowest_market_price
FROM latest_prices
GROUP BY product_name, brand, category_name
ORDER BY category_name, product_name;

-- Query to test the view:
-- SELECT * FROM vw_daily_competitor_pricing LIMIT 20;
