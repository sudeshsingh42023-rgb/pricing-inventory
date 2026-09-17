-- =====================================================================
-- Project 1: Used-Car Pricing & Inventory Turnover Analysis
-- Run against spinny_inventory.db (table: used_cars)
-- =====================================================================

-- 1. Average days-to-sell by brand (sold listings only)
SELECT
    brand,
    COUNT(*) AS units_sold,
    ROUND(AVG(days_in_inventory), 1) AS avg_days_to_sell,
    ROUND(AVG(sale_price), 0) AS avg_sale_price
FROM used_cars
WHERE sold_flag = 1
GROUP BY brand
ORDER BY avg_days_to_sell DESC;

-- 2. Average days-to-sell by city (demand proxy)
SELECT
    city,
    COUNT(*) AS units_sold,
    ROUND(AVG(days_in_inventory), 1) AS avg_days_to_sell
FROM used_cars
WHERE sold_flag = 1
GROUP BY city
ORDER BY avg_days_to_sell ASC;

-- 3. Inventory aging buckets for CURRENTLY UNSOLD stock
--    (this is the "money tied up" view for ops/finance stakeholders)
SELECT
    CASE
        WHEN days_in_inventory BETWEEN 0 AND 15 THEN '0-15 days'
        WHEN days_in_inventory BETWEEN 16 AND 30 THEN '16-30 days'
        WHEN days_in_inventory BETWEEN 31 AND 60 THEN '31-60 days'
        ELSE '60+ days (at risk)'
    END AS aging_bucket,
    COUNT(*) AS num_units,
    ROUND(SUM(listing_price), 0) AS capital_tied_up
FROM used_cars
WHERE sold_flag = 0
GROUP BY aging_bucket
ORDER BY MIN(days_in_inventory);

-- 4. Mispricing check: listings priced >10% above fair value estimate
--    that are still unsold (candidates for markdown)
SELECT
    listing_id, brand, model, city, listing_price, fair_value_est,
    ROUND((listing_price - fair_value_est) * 100.0 / fair_value_est, 1) AS pct_overpriced,
    days_in_inventory
FROM used_cars
WHERE sold_flag = 0
  AND (listing_price - fair_value_est) * 1.0 / fair_value_est > 0.10
ORDER BY pct_overpriced DESC
LIMIT 50;

-- 5. Turnover rate by condition grade (does condition affect speed of sale?)
SELECT
    condition_grade,
    COUNT(*) AS units_sold,
    ROUND(AVG(days_in_inventory), 1) AS avg_days_to_sell,
    ROUND(AVG((sale_price - fair_value_est) * 100.0 / fair_value_est), 1) AS avg_pct_vs_fair_value
FROM used_cars
WHERE sold_flag = 1
GROUP BY condition_grade;

-- 6. Segment matrix: brand x city avg days-to-sell (for a pivot-style heatmap in Excel)
SELECT
    brand,
    city,
    COUNT(*) AS units_sold,
    ROUND(AVG(days_in_inventory), 1) AS avg_days_to_sell
FROM used_cars
WHERE sold_flag = 1
GROUP BY brand, city
ORDER BY brand, avg_days_to_sell;
