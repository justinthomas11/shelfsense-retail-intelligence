/*
  07_discount_by_day_of_week.sql

  Business Problem: "On which days of the week does each retailer discount most?"

  Description:
  Pivots average discount by EXTRACT(DOW) using conditional aggregation,
  per retailer and category.

  Technique: EXTRACT(DOW) + conditional aggregation
*/

CREATE OR REPLACE VIEW vw_discount_by_day_of_week AS
SELECT
    r.retailer_name,
    c.category_name,
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) = 1 THEN f.discount_pct END), 2) AS monday_avg_disc,
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) = 2 THEN f.discount_pct END), 2) AS tuesday_avg_disc,
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) = 3 THEN f.discount_pct END), 2) AS wednesday_avg_disc,
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) = 4 THEN f.discount_pct END), 2) AS thursday_avg_disc,
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) = 5 THEN f.discount_pct END), 2) AS friday_avg_disc,
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) = 6 THEN f.discount_pct END), 2) AS saturday_avg_disc,
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) = 0 THEN f.discount_pct END), 2) AS sunday_avg_disc,
    ROUND(AVG(f.discount_pct), 2) AS overall_avg_disc
FROM fact_price_history f
JOIN dim_product p ON f.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON f.retailer_id = r.retailer_id
WHERE f.is_available = TRUE
GROUP BY r.retailer_name, c.category_name
ORDER BY r.retailer_name, c.category_name;
