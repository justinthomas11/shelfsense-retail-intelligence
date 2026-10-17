/*
  17_monthly_price_trends.sql

  Business Problem: "How are category prices trending month over month?"

  Description:
  Aggregates prices by month with DATE_TRUNC and computes MoM % change
  with LAG().

  Technique: DATE_TRUNC + month-over-month with LAG
*/

CREATE OR REPLACE VIEW vw_monthly_price_trends AS
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', f.price_date)::DATE AS price_month,
        c.category_name,
        c.parent_category,
        ROUND(AVG(f.selling_price), 2) AS avg_price,
        ROUND(AVG(f.mrp), 2) AS avg_mrp,
        ROUND(AVG(f.discount_pct), 2) AS avg_discount,
        COUNT(*) AS observations
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    WHERE f.is_available = TRUE
    GROUP BY DATE_TRUNC('month', f.price_date), c.category_name, c.parent_category
)
SELECT
    price_month,
    parent_category,
    category_name,
    avg_price,
    avg_mrp,
    avg_discount,
    observations,
    LAG(avg_price) OVER (PARTITION BY category_name ORDER BY price_month) AS prev_month_price,
    ROUND(
        (avg_price - LAG(avg_price) OVER (PARTITION BY category_name ORDER BY price_month))
        / NULLIF(LAG(avg_price) OVER (PARTITION BY category_name ORDER BY price_month), 0) * 100
    , 2) AS mom_price_change_pct
FROM monthly
ORDER BY price_month DESC, parent_category, category_name;
