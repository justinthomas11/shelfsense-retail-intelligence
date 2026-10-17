/*
  12_price_elasticity_estimate.sql

  Business Problem: "Which categories are most price-sensitive?"

  Description:
  Estimates a simplified elasticity as % change in availability (demand proxy)
  divided by % change in price, using LAG() over daily category averages.

  Technique: Regression via window functions (simplified elasticity)
*/

CREATE OR REPLACE VIEW vw_price_elasticity_estimate AS
WITH daily_category_stats AS (
    SELECT
        f.price_date,
        c.category_name,
        r.retailer_name,
        ROUND(AVG(f.selling_price), 2) AS avg_price,
        -- Use availability rate as a proxy for demand
        ROUND(
            SUM(CASE WHEN f.is_available THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100
        , 2) AS availability_rate
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    GROUP BY f.price_date, c.category_name, r.retailer_name
),
with_changes AS (
    SELECT
        *,
        LAG(avg_price) OVER (
            PARTITION BY category_name, retailer_name ORDER BY price_date
        ) AS prev_price,
        LAG(availability_rate) OVER (
            PARTITION BY category_name, retailer_name ORDER BY price_date
        ) AS prev_availability
    FROM daily_category_stats
)
SELECT
    category_name,
    retailer_name,
    COUNT(*) AS data_points,
    -- Simplified elasticity: % change in availability / % change in price
    ROUND(
        AVG(
            CASE
                WHEN prev_price > 0 AND prev_availability > 0
                     AND ABS(avg_price - prev_price) / prev_price > 0.01  -- filter noise
                THEN ((availability_rate - prev_availability) / prev_availability)
                     / ((avg_price - prev_price) / prev_price)
                ELSE NULL
            END
        )
    , 4) AS estimated_elasticity,
    -- Interpretation
    CASE
        WHEN AVG(
            CASE
                WHEN prev_price > 0 AND prev_availability > 0
                     AND ABS(avg_price - prev_price) / prev_price > 0.01
                THEN ((availability_rate - prev_availability) / prev_availability)
                     / ((avg_price - prev_price) / prev_price)
                ELSE NULL
            END
        ) < -1 THEN 'Elastic (price-sensitive)'
        WHEN AVG(
            CASE
                WHEN prev_price > 0 AND prev_availability > 0
                     AND ABS(avg_price - prev_price) / prev_price > 0.01
                THEN ((availability_rate - prev_availability) / prev_availability)
                     / ((avg_price - prev_price) / prev_price)
                ELSE NULL
            END
        ) BETWEEN -1 AND 0 THEN 'Inelastic (price-insensitive)'
        ELSE 'Positive/Anomalous'
    END AS elasticity_interpretation
FROM with_changes
WHERE prev_price IS NOT NULL
GROUP BY category_name, retailer_name
ORDER BY estimated_elasticity ASC;
