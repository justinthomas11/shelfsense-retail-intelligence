-- View 1: Latest Daily Competitor Pricing Pivot
CREATE OR REPLACE VIEW vw_daily_competitor_pricing AS
WITH latest_date AS(
    SELECT MAX(price_date) as max_date
    FROM fact_price_history
),
latest_prices AS (
    SELECT
        f.product_id,
        p.product_name,
        p.brand,
        c.category_name,
        r.retailer_name,
        f.selling_price,
        f.is_available
    FROM fact_price_history f
    JOIN dim_product p on f.product_id=p.product_id
    JOIN dim_category c ON p.category_id=c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    CROSS JOIN latest_date ld
    WHERE f.price_date = ld.max_date
)
SELECT product_name, brand, category_name, 
MAX(CASE WHEN retailer_name = 'BigBasket' AND is_available THEN selling_price END) AS bigbasket_price,
    MAX(CASE WHEN retailer_name = 'Blinkit' AND is_available THEN selling_price END) AS blinkit_price,
    MAX(CASE WHEN retailer_name = 'Zepto' AND is_available THEN selling_price END) AS zepto_price,
    MAX(CASE WHEN retailer_name = 'JioMart' AND is_available THEN selling_price END) AS jiomart_price,
    LEAST(
        MAX(CASE WHEN retailer_name = 'BigBasket' AND is_available THEN selling_price END),
        MAX(CASE WHEN retailer_name = 'Blinkit' AND is_available THEN selling_price END),
        MAX(CASE WHEN retailer_name = 'Zepto' AND is_available THEN selling_price END),
        MAX(CASE WHEN retailer_name = 'JioMart' AND is_available THEN selling_price END)
    ) AS lowest_market_price
FROM latest_prices
GROUP BY product_name, brand, category_name
ORDER BY category_name, product_name;




-- View 2: Weekly Average Discount Analysis
CREATE OR REPLACE VIEW vw_weekly_discount_analysis AS
WITH last_7_days AS(
    select price_date from fact_price_history group by price_date order by price_date desc limit 7),
    discount_data AS (SELECT 
        c.category_name,
        r.retailer_name,
        f.discount_pct,
        f.is_available
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE f.price_date IN (SELECT price_date FROM last_7_days)
      AND f.is_available = TRUE
)
SELECT 
    category_name,
    ROUND(AVG(CASE WHEN retailer_name = 'BigBasket' THEN discount_pct END), 2) AS bigbasket_avg_discount,
    ROUND(AVG(CASE WHEN retailer_name = 'Blinkit' THEN discount_pct END), 2) AS blinkit_avg_discount,
    ROUND(AVG(CASE WHEN retailer_name = 'Zepto' THEN discount_pct END), 2) AS zepto_avg_discount,
    ROUND(AVG(CASE WHEN retailer_name = 'JioMart' THEN discount_pct END), 2) AS jiomart_avg_discount,
    ROUND(AVG(discount_pct), 2) AS market_avg_discount
FROM discount_data
GROUP BY category_name
ORDER BY market_avg_discount DESC;


-- View 3: 30-Day Stockout & Availability Tracker
CREATE OR REPLACE VIEW vw_30day_availability_tracker AS
WITH last_30_days AS (
    SELECT price_date 
    FROM fact_price_history
    GROUP BY price_date
    ORDER BY price_date DESC
    LIMIT 30
)
SELECT 
    p.product_name,
    p.brand,
    c.category_name,
    r.retailer_name,
    COUNT(*) AS total_days_checked,
    SUM(CASE WHEN f.is_available = FALSE THEN 1 ELSE 0 END) AS days_out_of_stock,
    ROUND(
        (SUM(CASE WHEN f.is_available = FALSE THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100, 
        2
    ) AS out_of_stock_pct
FROM fact_price_history f
JOIN dim_product p ON f.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON f.retailer_id = r.retailer_id
WHERE f.price_date IN (SELECT price_date FROM last_30_days)
GROUP BY 
    p.product_name,
    p.brand,
    c.category_name,
    r.retailer_name
HAVING SUM(CASE WHEN f.is_available = FALSE THEN 1 ELSE 0 END) > 0
ORDER BY out_of_stock_pct DESC;




-- View 4: 30-Day Selling Price Volatility Index
CREATE OR REPLACE VIEW vw_price_volatility AS
WITH last_30_days AS (
    SELECT price_date 
    FROM fact_price_history
    GROUP BY price_date
    ORDER BY price_date DESC
    LIMIT 30
),
price_stats AS (
    SELECT 
        f.product_id,
        f.retailer_id,
        MIN(f.selling_price) AS min_price,
        MAX(f.selling_price) AS max_price,
        AVG(f.selling_price) AS avg_price,
        STDDEV_SAMP(f.selling_price) AS price_stddev
    FROM fact_price_history f
    WHERE f.price_date IN (SELECT price_date FROM last_30_days)
      AND f.is_available = TRUE
    GROUP BY f.product_id, f.retailer_id
)
SELECT 
    p.product_name,
    c.category_name,
    r.retailer_name,
    ROUND(s.min_price, 2) AS min_price_30d,
    ROUND(s.max_price, 2) AS max_price_30d,
    ROUND(s.avg_price, 2) AS avg_price_30d,
    ROUND((s.price_stddev / s.avg_price) * 100, 2) AS volatility_index_pct
FROM price_stats s
JOIN dim_product p ON s.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON s.retailer_id = r.retailer_id
WHERE s.price_stddev IS NOT NULL
ORDER BY volatility_index_pct DESC;



-- =====================================================================
-- View 5: Promotion Detection (>15% Price Drop from Previous Day)
-- Technique: LAG() window function
-- =====================================================================
CREATE OR REPLACE VIEW vw_promotion_detection AS
WITH price_changes AS (
    SELECT
        f.product_id,
        f.retailer_id,
        p.product_name,
        p.brand,
        c.category_name,
        r.retailer_name,
        f.price_date,
        f.selling_price,
        LAG(f.selling_price) OVER (
            PARTITION BY f.product_id, f.retailer_id
            ORDER BY f.price_date
        ) AS prev_day_price
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE f.is_available = TRUE
)
SELECT
    product_name,
    brand,
    category_name,
    retailer_name,
    price_date,
    prev_day_price,
    selling_price,
    ROUND((prev_day_price - selling_price) / prev_day_price * 100, 2) AS pct_drop,
    CASE
        WHEN (prev_day_price - selling_price) / prev_day_price > 0.25 THEN 'Deep Promotion'
        WHEN (prev_day_price - selling_price) / prev_day_price > 0.15 THEN 'Promotion'
    END AS promotion_tier
FROM price_changes
WHERE prev_day_price IS NOT NULL
  AND (prev_day_price - selling_price) / prev_day_price > 0.15
ORDER BY price_date DESC, pct_drop DESC;



-- =====================================================================
-- View 6: Week-over-Week Price Change
-- Technique: LAG() + DATE_TRUNC + PARTITION BY
-- =====================================================================
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



-- =====================================================================
-- View 7: Retailer Discount Frequency by Day of Week
-- Technique: EXTRACT(DOW) + conditional aggregation
-- =====================================================================
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



-- =====================================================================
-- View 8: Competitive Price Gap (Pairwise Retailer Comparison)
-- Technique: Self-join + CTEs
-- =====================================================================
CREATE OR REPLACE VIEW vw_competitive_price_gap AS
WITH latest_date AS (
    SELECT MAX(price_date) AS max_date FROM fact_price_history
),
retailer_prices AS (
    SELECT
        f.product_id,
        p.product_name,
        p.brand,
        c.category_name,
        r.retailer_name,
        f.selling_price
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    CROSS JOIN latest_date ld
    WHERE f.price_date = ld.max_date
      AND f.is_available = TRUE
)
SELECT
    a.product_name,
    a.brand,
    a.category_name,
    a.retailer_name AS retailer_a,
    b.retailer_name AS retailer_b,
    a.selling_price AS price_a,
    b.selling_price AS price_b,
    ROUND(a.selling_price - b.selling_price, 2) AS price_diff,
    ROUND((a.selling_price - b.selling_price) / b.selling_price * 100, 2) AS pct_premium_a_over_b
FROM retailer_prices a
JOIN retailer_prices b
    ON a.product_id = b.product_id
    AND a.retailer_name < b.retailer_name  -- avoid duplicates and self-join
ORDER BY ABS(a.selling_price - b.selling_price) DESC;



-- =====================================================================
-- View 9: Category-Level Demand Proxy (Stockout = High Demand Signal)
-- Technique: Availability signal aggregation + ranking
-- =====================================================================
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



-- =====================================================================
-- View 10: Inflation-Adjusted Pricing Trends
-- Technique: CPI join + real price calculation
-- =====================================================================
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



-- =====================================================================
-- View 11: Promotional Calendar Reconstruction
-- Technique: Gap-and-island detection
-- =====================================================================
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



-- =====================================================================
-- View 12: Price Elasticity Estimation by Category
-- Technique: Regression via window functions (simplified elasticity)
-- =====================================================================
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



-- =====================================================================
-- View 13: Market Basket Correlation (Cross-Category Co-movement)
-- Technique: Cross-category price correlation via self-join
-- =====================================================================
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



-- =====================================================================
-- View 14: Weekend vs Weekday Discount Patterns
-- Technique: EXTRACT(DOW) + CASE WHEN segmentation
-- =====================================================================
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



-- =====================================================================
-- View 15: Cheapest Retailer Frequency (Who Wins on Price?)
-- Technique: RANK() window function + conditional counting
-- =====================================================================
CREATE OR REPLACE VIEW vw_cheapest_retailer_frequency AS
WITH daily_prices AS (
    SELECT
        f.price_date,
        f.product_id,
        r.retailer_name,
        f.selling_price,
        RANK() OVER (
            PARTITION BY f.price_date, f.product_id
            ORDER BY f.selling_price ASC
        ) AS price_rank
    FROM fact_price_history f
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    WHERE f.is_available = TRUE
),
wins AS (
    SELECT
        product_id,
        retailer_name,
        COUNT(*) AS days_cheapest
    FROM daily_prices
    WHERE price_rank = 1
    GROUP BY product_id, retailer_name
)
SELECT
    p.product_name,
    p.brand,
    c.category_name,
    w.retailer_name,
    w.days_cheapest,
    ROUND(w.days_cheapest::NUMERIC / SUM(w.days_cheapest) OVER (PARTITION BY w.product_id) * 100, 1)
        AS pct_days_cheapest
FROM wins w
JOIN dim_product p ON w.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
ORDER BY c.category_name, p.product_name, pct_days_cheapest DESC;



-- =====================================================================
-- View 16: Brand Price Consistency Across Retailers
-- Technique: Aggregation with spread analysis
-- =====================================================================
CREATE OR REPLACE VIEW vw_brand_price_consistency AS
WITH latest_date AS (
    SELECT MAX(price_date) AS max_date FROM fact_price_history
),
brand_prices AS (
    SELECT
        p.brand,
        c.category_name,
        r.retailer_name,
        ROUND(AVG(f.selling_price), 2) AS avg_price,
        COUNT(DISTINCT p.product_id) AS num_products
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    CROSS JOIN latest_date ld
    WHERE f.price_date >= ld.max_date - INTERVAL '7 days'
      AND f.is_available = TRUE
    GROUP BY p.brand, c.category_name, r.retailer_name
)
SELECT
    brand,
    category_name,
    COUNT(DISTINCT retailer_name) AS retailers_carrying,
    ROUND(MIN(avg_price), 2) AS cheapest_avg,
    ROUND(MAX(avg_price), 2) AS priciest_avg,
    ROUND(MAX(avg_price) - MIN(avg_price), 2) AS price_spread,
    ROUND((MAX(avg_price) - MIN(avg_price)) / NULLIF(MIN(avg_price), 0) * 100, 2) AS spread_pct,
    -- Which retailer is cheapest / priciest for this brand
    (SELECT bp2.retailer_name FROM brand_prices bp2
     WHERE bp2.brand = bp.brand AND bp2.category_name = bp.category_name
     ORDER BY bp2.avg_price ASC LIMIT 1) AS cheapest_at,
    (SELECT bp3.retailer_name FROM brand_prices bp3
     WHERE bp3.brand = bp.brand AND bp3.category_name = bp.category_name
     ORDER BY bp3.avg_price DESC LIMIT 1) AS priciest_at
FROM brand_prices bp
GROUP BY brand, category_name
HAVING COUNT(DISTINCT retailer_name) >= 2  -- compare only if available at 2+ retailers
ORDER BY spread_pct DESC;



-- =====================================================================
-- View 17: Monthly Price Trend Summary
-- Technique: DATE_TRUNC + month-over-month with LAG
-- =====================================================================
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



-- =====================================================================
-- View 18: Top Promoted Products (Highest Discount Frequency in 30 Days)
-- Technique: Conditional aggregation + PERCENT_RANK
-- =====================================================================
CREATE OR REPLACE VIEW vw_top_promoted_products AS
WITH last_30_days AS (
    SELECT price_date
    FROM fact_price_history
    GROUP BY price_date
    ORDER BY price_date DESC
    LIMIT 30
),
promo_stats AS (
    SELECT
        f.product_id,
        f.retailer_id,
        COUNT(*) AS total_days,
        SUM(CASE WHEN f.discount_pct > 15 THEN 1 ELSE 0 END) AS heavy_promo_days,
        ROUND(AVG(f.discount_pct), 2) AS avg_discount,
        ROUND(MAX(f.discount_pct), 2) AS max_discount,
        ROUND(AVG(f.selling_price), 2) AS avg_selling_price
    FROM fact_price_history f
    WHERE f.price_date IN (SELECT price_date FROM last_30_days)
      AND f.is_available = TRUE
    GROUP BY f.product_id, f.retailer_id
)
SELECT
    p.product_name,
    p.brand,
    c.category_name,
    r.retailer_name,
    ps.total_days,
    ps.heavy_promo_days,
    ROUND(ps.heavy_promo_days::NUMERIC / ps.total_days * 100, 1) AS promo_frequency_pct,
    ps.avg_discount,
    ps.max_discount,
    ps.avg_selling_price,
    PERCENT_RANK() OVER (ORDER BY ps.heavy_promo_days::NUMERIC / ps.total_days) AS promo_percentile
FROM promo_stats ps
JOIN dim_product p ON ps.product_id = p.product_id
JOIN dim_category c ON p.category_id = c.category_id
JOIN dim_retailer r ON ps.retailer_id = r.retailer_id
WHERE ps.heavy_promo_days > 0
ORDER BY promo_frequency_pct DESC;



-- =====================================================================
-- View 19: Price Recovery After Promotion
-- Technique: LEAD() window function + promotion flag
-- =====================================================================
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



-- =====================================================================
-- View 20: Category Price Index (Normalized Index Over Time)
-- Technique: First-value normalization + window function
-- =====================================================================
CREATE OR REPLACE VIEW vw_category_price_index AS
WITH daily_category_price AS (
    SELECT
        f.price_date,
        c.category_name,
        c.parent_category,
        ROUND(AVG(f.selling_price), 2) AS avg_price
    FROM fact_price_history f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    WHERE f.is_available = TRUE
    GROUP BY f.price_date, c.category_name, c.parent_category
),
with_base AS (
    SELECT
        *,
        FIRST_VALUE(avg_price) OVER (
            PARTITION BY category_name
            ORDER BY price_date ASC
        ) AS base_price
    FROM daily_category_price
)
SELECT
    price_date,
    parent_category,
    category_name,
    avg_price,
    base_price,
    -- Index: Day 1 = 100, subsequent days relative to that
    ROUND((avg_price / NULLIF(base_price, 0)) * 100, 2) AS price_index,
    -- Rolling 7-day average of the index for smoothing
    ROUND(AVG(avg_price / NULLIF(base_price, 0) * 100) OVER (
        PARTITION BY category_name
        ORDER BY price_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS price_index_7day_ma
FROM with_base
ORDER BY category_name, price_date;
