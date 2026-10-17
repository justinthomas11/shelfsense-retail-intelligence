/*
  14_weekend_vs_weekday_discounts.sql

  Business Problem: "Do retailers discount harder on weekends?"

  Description:
  Segments discounts into weekday vs weekend with EXTRACT(DOW) + CASE WHEN
  and classifies each retailer/category's promotional strategy.

  Technique: EXTRACT(DOW) + CASE WHEN segmentation
*/

CREATE OR REPLACE VIEW vw_weekend_vs_weekday_discounts AS
SELECT
    r.retailer_name,
    c.category_name,
    -- Weekday metrics (Mon–Fri)
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) BETWEEN 1 AND 5
        THEN f.discount_pct END), 2) AS weekday_avg_discount,
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) BETWEEN 1 AND 5
        THEN f.selling_price END), 2) AS weekday_avg_price,
    -- Weekend metrics (Sat–Sun)
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) IN (0, 6)
        THEN f.discount_pct END), 2) AS weekend_avg_discount,
    ROUND(AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) IN (0, 6)
        THEN f.selling_price END), 2) AS weekend_avg_price,
    -- Gap analysis
    ROUND(
        AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) IN (0, 6) THEN f.discount_pct END)
      - AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) BETWEEN 1 AND 5 THEN f.discount_pct END)
    , 2) AS weekend_discount_lift_ppt,
    -- Strategy classification
    CASE
        WHEN AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) IN (0, 6) THEN f.discount_pct END)
           - AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) BETWEEN 1 AND 5 THEN f.discount_pct END) > 3
        THEN 'Weekend-Heavy Promoter'
        WHEN AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) IN (0, 6) THEN f.discount_pct END)
           - AVG(CASE WHEN EXTRACT(DOW FROM f.price_date) BETWEEN 1 AND 5 THEN f.discount_pct END) < -1
        THEN 'Weekday-Heavy Promoter'
        ELSE 'Consistent Pricing'
    END AS pricing_strategy
FROM fact_price_history f
JOIN dim_product p ON f.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON f.retailer_id = r.retailer_id
WHERE f.is_available = TRUE
GROUP BY r.retailer_name, c.category_name
ORDER BY weekend_discount_lift_ppt DESC;
