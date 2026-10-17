/*
  06_week_over_week_price_change.sql

  Business Problem: "How did prices move compared to last week?"

  Description:
  Averages prices per ISO week and compares each week to the previous one
  with LAG(), reporting both price change % and discount change in points.

  Technique: LAG() + DATE_TRUNC + PARTITION BY
*/

CREATE OR REPLACE VIEW vw_week_over_week_price_change AS
WITH weekly_avg AS (
    SELECT
        f.product_id,
        f.retailer_id,
        DATE_TRUNC('week', f.price_date)::DATE AS week_start,
        ROUND(AVG(f.selling_price), 2) AS avg_price,
        ROUND(AVG(f.discount_pct), 2) AS avg_discount
    FROM fact_price_history f
    WHERE f.is_available = TRUE
    GROUP BY f.product_id, f.retailer_id, DATE_TRUNC('week', f.price_date)
),
with_prev_week AS (
    SELECT
        w.*,
        LAG(w.avg_price) OVER (
            PARTITION BY w.product_id, w.retailer_id
            ORDER BY w.week_start
        ) AS prev_week_price,
        LAG(w.avg_discount) OVER (
            PARTITION BY w.product_id, w.retailer_id
            ORDER BY w.week_start
        ) AS prev_week_discount
    FROM weekly_avg w
)
SELECT
    p.product_name,
    c.category_name,
    r.retailer_name,
    pw.week_start,
    pw.prev_week_price,
    pw.avg_price AS current_week_price,
    ROUND((pw.avg_price - pw.prev_week_price) / pw.prev_week_price * 100, 2) AS wow_price_change_pct,
    pw.avg_discount AS current_week_discount,
    ROUND(pw.avg_discount - pw.prev_week_discount, 2) AS wow_discount_change_ppt
FROM with_prev_week pw
JOIN dim_product p ON pw.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON pw.retailer_id = r.retailer_id
WHERE pw.prev_week_price IS NOT NULL
ORDER BY pw.week_start DESC, wow_price_change_pct ASC;
