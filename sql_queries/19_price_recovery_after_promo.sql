/*
  19_price_recovery_after_promo.sql

  Business Problem: "How quickly do prices bounce back after a promotion?"

  Description:
  Uses LEAD() to look 1-3 days past the start of each significant promotion
  and classifies recovery speed.

  Technique: LEAD() window function + promotion flag
*/

CREATE OR REPLACE VIEW vw_price_recovery_after_promo AS
WITH price_with_context AS (
    SELECT
        f.product_id,
        f.retailer_id,
        f.price_date,
        f.selling_price,
        f.discount_pct,
        -- Look at next 3 days' prices after each day
        LEAD(f.selling_price, 1) OVER w AS price_day_1,
        LEAD(f.selling_price, 2) OVER w AS price_day_2,
        LEAD(f.selling_price, 3) OVER w AS price_day_3,
        LEAD(f.discount_pct, 1) OVER w AS disc_day_1,
        LEAD(f.discount_pct, 2) OVER w AS disc_day_2,
        LEAD(f.discount_pct, 3) OVER w AS disc_day_3,
        -- Previous day price to detect promo start
        LAG(f.discount_pct) OVER w AS prev_discount
    FROM fact_price_history f
    WHERE f.is_available = TRUE
    WINDOW w AS (PARTITION BY f.product_id, f.retailer_id ORDER BY f.price_date)
)
SELECT
    p.product_name,
    c.category_name,
    r.retailer_name,
    pc.price_date AS promo_date,
    pc.selling_price AS promo_price,
    pc.discount_pct AS promo_discount,
    pc.price_day_1 AS day1_after_price,
    pc.price_day_2 AS day2_after_price,
    pc.price_day_3 AS day3_after_price,
    -- Recovery speed: how quickly does price go back up?
    CASE
        WHEN pc.disc_day_1 IS NOT NULL AND pc.disc_day_1 < pc.discount_pct - 5 THEN '1-Day Recovery'
        WHEN pc.disc_day_2 IS NOT NULL AND pc.disc_day_2 < pc.discount_pct - 5 THEN '2-Day Recovery'
        WHEN pc.disc_day_3 IS NOT NULL AND pc.disc_day_3 < pc.discount_pct - 5 THEN '3-Day Recovery'
        ELSE 'Slow/No Recovery'
    END AS recovery_speed,
    ROUND(
        CASE WHEN pc.price_day_3 IS NOT NULL
            THEN (pc.price_day_3 - pc.selling_price) / NULLIF(pc.selling_price, 0) * 100
            ELSE NULL
        END
    , 2) AS pct_recovery_3day
FROM price_with_context pc
JOIN dim_product p ON pc.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON pc.retailer_id = r.retailer_id
WHERE pc.discount_pct > 20                          -- was a significant promo
  AND (pc.prev_discount IS NULL OR pc.prev_discount < 15)  -- promo just started
ORDER BY pc.price_date DESC, pc.discount_pct DESC;
