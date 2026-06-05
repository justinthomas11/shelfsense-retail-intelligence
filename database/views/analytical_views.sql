-- View 1: Latest Daily Competitor Pricing Pivot
CREATE OR REPLACE VIEW vw_daily_competitor_pricing AS
WITH latest_date AS(
    SELECT MAX(price_date) as max_date
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
    JOIN dim_product p on f.product_id=p.product_id
    JOIN dim_category c ON p.category_id=c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    CROSS JOIN latest_date ld
    WHERE f.price_date = ld.max_date
)
SELECT product_name, brand, category_name, 
MAX(CASE WHEN retailer_name = 'BigBasket' THEN selling_price END) AS bigbasket_price,
    MAX(CASE WHEN retailer_name = 'Blinkit' THEN selling_price END) AS blinkit_price,
    MAX(CASE WHEN retailer_name = 'Zepto' THEN selling_price END) AS zepto_price,
    MAX(CASE WHEN retailer_name = 'JioMart' THEN selling_price END) AS jiomart_price,
    LEAST(
        MAX(CASE WHEN retailer_name = 'BigBasket' THEN selling_price END),
        MAX(CASE WHEN retailer_name = 'Blinkit' THEN selling_price END),
        MAX(CASE WHEN retailer_name = 'Zepto' THEN selling_price END),
        MAX(CASE WHEN retailer_name = 'JioMart' THEN selling_price END)
    ) AS lowest_market_price
FROM latest_prices
GROUP BY product_name, brand, category_name
ORDER BY category_name, product_name;




-- View 2: Weekly Average Discount Analysis
CREATE OR REPLACE VIEW vw_weekly_discount_analysis AS
WITH last_7_days AS(
    select price_date from fact_price_history group by price_date order by price_date desc limit 7),
    discount_data AS (SELECT 
        c.category_name,
        r.retailer_name,
        f.discount_pct,
        f.is_available
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE f.price_date IN (SELECT price_date FROM last_7_days)
      AND f.is_available = TRUE
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

