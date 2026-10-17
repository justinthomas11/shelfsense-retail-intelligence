/*
  10_inflation_adjusted_pricing.sql

  Business Problem: "Are retailers absorbing inflation or passing it on to consumers?"

  Description:
  Joins monthly category prices to government CPI data to compute real
  (CPI-deflated) prices and compare discount depth with YoY inflation.

  Technique: CPI join + real price calculation
*/

CREATE OR REPLACE VIEW vw_inflation_adjusted_pricing AS
WITH monthly_prices AS (
    SELECT
        DATE_TRUNC('month', f.price_date)::DATE AS price_month,
        c.category_name,
        ROUND(AVG(f.selling_price), 2) AS avg_selling_price,
        ROUND(AVG(f.mrp), 2) AS avg_mrp,
        ROUND(AVG(f.discount_pct), 2) AS avg_discount
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    WHERE f.is_available = TRUE
    GROUP BY DATE_TRUNC('month', f.price_date), c.category_name
)
SELECT
    mp.price_month,
    mp.category_name,
    mp.avg_selling_price AS nominal_price,
    mp.avg_mrp,
    mp.avg_discount,
    cpi.cpi_index,
    cpi.yoy_inflation,
    -- Real price = (Nominal Price / CPI Index) * 100
    CASE
        WHEN cpi.cpi_index IS NOT NULL AND cpi.cpi_index > 0
        THEN ROUND((mp.avg_selling_price / cpi.cpi_index) * 100, 2)
        ELSE NULL
    END AS real_price_adjusted,
    -- Are retailers absorbing inflation or passing it on?
    CASE
        WHEN cpi.yoy_inflation IS NOT NULL THEN
            CASE
                WHEN mp.avg_discount > cpi.yoy_inflation THEN 'Absorbing Inflation'
                ELSE 'Passing to Consumer'
            END
        ELSE 'No CPI Data'
    END AS inflation_strategy
FROM monthly_prices mp
LEFT JOIN fact_macro_cpi cpi
    ON mp.price_month = cpi.report_month
    AND mp.category_name = cpi.category_name
ORDER BY mp.price_month DESC, mp.category_name;
