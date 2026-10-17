/*
  09_category_demand_proxy.sql

  Business Problem: "Which categories show signs of strong demand?"

  Description:
  Uses stockout rate (with discount level) over the last 30 days as a
  demand signal, since sales volumes are not observable from the shelf.

  Technique: Availability signal aggregation + ranking
*/

CREATE OR REPLACE VIEW vw_category_demand_proxy AS
WITH last_30_days AS (
    SELECT price_date
    FROM fact_price_history
    GROUP BY price_date
    ORDER BY price_date DESC
    LIMIT 30
),
availability_stats AS (
    SELECT
        c.category_name,
        r.retailer_name,
        COUNT(*) AS total_observations,
        SUM(CASE WHEN f.is_available = FALSE THEN 1 ELSE 0 END) AS stockout_count,
        ROUND(AVG(f.discount_pct), 2) AS avg_discount,
        ROUND(AVG(f.selling_price), 2) AS avg_selling_price
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE f.price_date IN (SELECT price_date FROM last_30_days)
    GROUP BY c.category_name, r.retailer_name
)
SELECT
    category_name,
    retailer_name,
    total_observations,
    stockout_count,
    ROUND(stockout_count::NUMERIC / total_observations * 100, 2) AS stockout_rate_pct,
    avg_discount,
    avg_selling_price,
    -- High stockout + low discount = strong organic demand
    CASE
        WHEN stockout_count::NUMERIC / total_observations > 0.08 AND avg_discount < 10 THEN 'Very High Demand'
        WHEN stockout_count::NUMERIC / total_observations > 0.05 THEN 'High Demand'
        WHEN stockout_count::NUMERIC / total_observations > 0.02 THEN 'Moderate Demand'
        ELSE 'Normal'
    END AS demand_signal
FROM availability_stats
ORDER BY stockout_rate_pct DESC;
