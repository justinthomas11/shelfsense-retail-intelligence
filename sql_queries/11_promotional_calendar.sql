/*
  11_promotional_calendar.sql

  Business Problem: "When did each promotion start and end, and how long did it run?"

  Description:
  Reconstructs contiguous promotional runs (discount > 15%) using the
  gap-and-island technique: date minus ROW_NUMBER() groups consecutive days.

  Technique: Gap-and-island detection
*/

CREATE OR REPLACE VIEW vw_promotional_calendar AS
WITH promo_flags AS (
    SELECT
        f.product_id,
        f.retailer_id,
        f.price_date,
        f.discount_pct,
        -- Flag days with aggressive discounts (>15%) as promotional
        CASE WHEN f.discount_pct > 15 THEN 1 ELSE 0 END AS is_promo_day
    FROM fact_price_history f
    WHERE f.is_available = TRUE
),
-- Assign island groups: subtract row_number from date to group consecutive promo days
islands AS (
    SELECT
        product_id,
        retailer_id,
        price_date,
        discount_pct,
        price_date - (ROW_NUMBER() OVER (
            PARTITION BY product_id, retailer_id
            ORDER BY price_date
        ))::INTEGER AS island_id
    FROM promo_flags
    WHERE is_promo_day = 1
)
SELECT
    p.product_name,
    p.brand,
    c.category_name,
    r.retailer_name,
    MIN(i.price_date) AS promo_start_date,
    MAX(i.price_date) AS promo_end_date,
    COUNT(*) AS promo_duration_days,
    ROUND(AVG(i.discount_pct), 2) AS avg_promo_discount,
    ROUND(MAX(i.discount_pct), 2) AS max_promo_discount
FROM islands i
JOIN dim_product p ON i.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON i.retailer_id = r.retailer_id
GROUP BY p.product_name, p.brand, c.category_name, r.retailer_name, i.island_id
HAVING COUNT(*) >= 2  -- At least 2 consecutive days to qualify as a promotion
ORDER BY promo_start_date DESC, promo_duration_days DESC;
