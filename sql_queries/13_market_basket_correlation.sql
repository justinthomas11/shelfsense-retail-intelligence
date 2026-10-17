/*
  13_market_basket_correlation.sql

  Business Problem: "Which categories move together in price and discounting?"

  Description:
  Computes Pearson correlation of daily category prices and discounts for
  every category pair via a self-join and the closed-form formula.

  Technique: Cross-category price correlation via self-join
*/

CREATE OR REPLACE VIEW vw_market_basket_correlation AS
WITH daily_category_avg AS (
    SELECT
        f.price_date,
        c.category_name,
        ROUND(AVG(f.selling_price), 2) AS avg_category_price,
        ROUND(AVG(f.discount_pct), 2) AS avg_category_discount
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    WHERE f.is_available = TRUE
    GROUP BY f.price_date, c.category_name
)
SELECT
    a.category_name AS category_a,
    b.category_name AS category_b,
    COUNT(*) AS shared_days,
    -- Pearson correlation coefficient for prices
    ROUND(
        (COUNT(*) * SUM(a.avg_category_price * b.avg_category_price)
         - SUM(a.avg_category_price) * SUM(b.avg_category_price))
        /
        NULLIF(
            SQRT(
                (COUNT(*) * SUM(a.avg_category_price ^ 2) - SUM(a.avg_category_price) ^ 2)
                * (COUNT(*) * SUM(b.avg_category_price ^ 2) - SUM(b.avg_category_price) ^ 2)
            )
        , 0)
    , 4) AS price_correlation,
    -- Discount co-movement
    ROUND(
        (COUNT(*) * SUM(a.avg_category_discount * b.avg_category_discount)
         - SUM(a.avg_category_discount) * SUM(b.avg_category_discount))
        /
        NULLIF(
            SQRT(
                (COUNT(*) * SUM(a.avg_category_discount ^ 2) - SUM(a.avg_category_discount) ^ 2)
                * (COUNT(*) * SUM(b.avg_category_discount ^ 2) - SUM(b.avg_category_discount) ^ 2)
            )
        , 0)
    , 4) AS discount_correlation
FROM daily_category_avg a
JOIN daily_category_avg b
    ON a.price_date = b.price_date
    AND a.category_name < b.category_name  -- avoid duplicates
GROUP BY a.category_name, b.category_name
HAVING COUNT(*) >= 30  -- need enough data points for meaningful correlation
ORDER BY price_correlation DESC;
