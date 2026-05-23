-- =============================================================
-- RetailEdge Analytics Dashboard
-- queries.sql  |  Business Intelligence Queries
-- =============================================================

-- =============================================================
-- 1. TOTAL REVENUE, ORDERS & AVERAGE ORDER VALUE
-- =============================================================
SELECT
    COUNT(DISTINCT o.invoice_no)              AS total_orders,
    SUM(ol.line_total)                        AS total_revenue,
    ROUND(SUM(ol.line_total)
          / COUNT(DISTINCT o.invoice_no), 2)  AS avg_order_value,
    SUM(ol.line_total - ol.cost_price)        AS gross_profit,
    ROUND(
        (SUM(ol.line_total - ol.cost_price) / SUM(ol.line_total)) * 100
    , 2)                                      AS margin_pct
FROM orders o
JOIN order_lines ol ON o.invoice_no = ol.invoice_no;


-- =============================================================
-- 2. MONTHLY REVENUE TREND
-- =============================================================
SELECT
    EXTRACT(YEAR  FROM o.invoice_date)  AS year,
    EXTRACT(MONTH FROM o.invoice_date)  AS month,
    TO_CHAR(o.invoice_date, 'Mon')      AS month_name,
    COUNT(DISTINCT o.invoice_no)        AS orders,
    SUM(ol.line_total)                  AS revenue,
    SUM(ol.line_total - ol.cost_price)  AS gross_profit,
    ROUND(
        SUM(ol.line_total)
        / COUNT(DISTINCT o.invoice_no)
    , 2)                                AS avg_order_value
FROM orders o
JOIN order_lines ol ON o.invoice_no = ol.invoice_no
GROUP BY 1, 2, 3
ORDER BY 1, 2;


-- =============================================================
-- 3. QUARTERLY PERFORMANCE SUMMARY
-- =============================================================
SELECT
    EXTRACT(YEAR FROM o.invoice_date)                      AS year,
    CONCAT('Q', EXTRACT(QUARTER FROM o.invoice_date))      AS quarter,
    COUNT(DISTINCT o.invoice_no)                           AS total_orders,
    SUM(ol.quantity)                                       AS units_sold,
    ROUND(SUM(ol.line_total), 2)                           AS revenue,
    ROUND(SUM(ol.line_total - ol.cost_price), 2)           AS gross_profit,
    ROUND(
        (SUM(ol.line_total - ol.cost_price) / SUM(ol.line_total)) * 100
    , 2)                                                   AS margin_pct
FROM orders o
JOIN order_lines ol ON o.invoice_no = ol.invoice_no
GROUP BY 1, 2
ORDER BY 1, 2;


-- =============================================================
-- 4. TOP 10 CUSTOMERS BY REVENUE
-- =============================================================
SELECT
    c.customer_id,
    c.customer_name,
    COUNT(DISTINCT o.invoice_no)                  AS total_orders,
    SUM(ol.quantity)                              AS units_purchased,
    ROUND(SUM(ol.line_total), 2)                  AS total_revenue,
    ROUND(SUM(ol.line_total - ol.cost_price), 2)  AS gross_profit,
    ROUND(
        SUM(ol.line_total) / COUNT(DISTINCT o.invoice_no)
    , 2)                                          AS avg_order_value
FROM customers c
JOIN orders o       ON c.customer_id  = o.customer_id
JOIN order_lines ol ON o.invoice_no   = ol.invoice_no
WHERE c.is_guest = FALSE
GROUP BY 1, 2
ORDER BY total_revenue DESC
LIMIT 10;


-- =============================================================
-- 5. REVENUE BY COUNTRY (EXCLUDING UK)
-- =============================================================
SELECT
    co.country_name,
    co.region,
    COUNT(DISTINCT o.invoice_no)                  AS orders,
    SUM(ol.quantity)                              AS units_sold,
    ROUND(SUM(ol.line_total), 2)                  AS revenue,
    ROUND(SUM(ol.line_total - ol.cost_price), 2)  AS gross_profit,
    ROUND(
        (SUM(ol.line_total - ol.cost_price) / SUM(ol.line_total)) * 100
    , 2)                                          AS margin_pct
FROM countries co
JOIN orders o       ON co.country_id  = o.country_id
JOIN order_lines ol ON o.invoice_no   = ol.invoice_no
WHERE co.country_name != 'United Kingdom'
GROUP BY 1, 2
ORDER BY revenue DESC;


-- =============================================================
-- 6. TOP 10 PRODUCTS BY REVENUE
-- =============================================================
SELECT
    p.stock_code,
    p.description,
    p.category,
    SUM(ol.quantity)                              AS units_sold,
    ROUND(SUM(ol.line_total), 2)                  AS revenue,
    ROUND(SUM(ol.line_total - ol.cost_price), 2)  AS gross_profit,
    ROUND(
        (SUM(ol.line_total - ol.cost_price) / SUM(ol.line_total)) * 100
    , 2)                                          AS margin_pct
FROM products p
JOIN order_lines ol ON p.stock_code = ol.stock_code
GROUP BY 1, 2, 3
ORDER BY revenue DESC
LIMIT 10;


-- =============================================================
-- 7. REVENUE BY PRODUCT CATEGORY
-- =============================================================
SELECT
    p.category,
    COUNT(DISTINCT ol.invoice_no)                 AS orders,
    SUM(ol.quantity)                              AS units_sold,
    ROUND(SUM(ol.line_total), 2)                  AS revenue,
    ROUND(SUM(ol.line_total - ol.cost_price), 2)  AS gross_profit,
    ROUND(
        (SUM(ol.line_total - ol.cost_price) / SUM(ol.line_total)) * 100
    , 2)                                          AS margin_pct,
    ROUND(
        (SUM(ol.line_total) / (SELECT SUM(line_total) FROM order_lines)) * 100
    , 2)                                          AS revenue_share_pct
FROM products p
JOIN order_lines ol ON p.stock_code = ol.stock_code
GROUP BY 1
ORDER BY revenue DESC;


-- =============================================================
-- 8. REVENUE BY DAY OF WEEK
-- =============================================================
SELECT
    TO_CHAR(o.invoice_date, 'Day')  AS day_of_week,
    EXTRACT(DOW FROM o.invoice_date) AS day_num,
    COUNT(DISTINCT o.invoice_no)    AS orders,
    ROUND(SUM(ol.line_total), 2)    AS revenue
FROM orders o
JOIN order_lines ol ON o.invoice_no = ol.invoice_no
GROUP BY 1, 2
ORDER BY 2;


-- =============================================================
-- 9. RFM SEGMENTATION
-- =============================================================
WITH rfm_base AS (
    SELECT
        c.customer_id,
        c.customer_name,
        MAX(o.invoice_date)                          AS last_purchase,
        COUNT(DISTINCT o.invoice_no)                 AS frequency,
        ROUND(SUM(ol.line_total), 2)                 AS monetary
    FROM customers c
    JOIN orders o       ON c.customer_id  = o.customer_id
    JOIN order_lines ol ON o.invoice_no   = ol.invoice_no
    WHERE c.is_guest = FALSE
    GROUP BY 1, 2
),
rfm_scores AS (
    SELECT *,
        CURRENT_DATE - last_purchase AS recency_days,
        NTILE(4) OVER (ORDER BY (CURRENT_DATE - last_purchase) DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency  ASC)                      AS f_score,
        NTILE(4) OVER (ORDER BY monetary   ASC)                      AS m_score
    FROM rfm_base
)
SELECT
    customer_id,
    customer_name,
    recency_days,
    frequency,
    monetary,
    r_score, f_score, m_score,
    (r_score + f_score + m_score) AS rfm_total,
    CASE
        WHEN (r_score + f_score + m_score) >= 10 THEN 'Champions'
        WHEN (r_score + f_score + m_score) >= 8  THEN 'Loyal Customers'
        WHEN (r_score + f_score + m_score) >= 6  THEN 'Potential Loyalists'
        WHEN (r_score + f_score + m_score) >= 4  THEN 'At Risk'
        ELSE 'Lost'
    END AS customer_segment
FROM rfm_scores
ORDER BY rfm_total DESC;


-- =============================================================
-- 10. WEEK-OVER-WEEK REVENUE GROWTH
-- =============================================================
WITH weekly AS (
    SELECT
        DATE_TRUNC('week', o.invoice_date) AS week_start,
        ROUND(SUM(ol.line_total), 2)       AS weekly_revenue
    FROM orders o
    JOIN order_lines ol ON o.invoice_no = ol.invoice_no
    GROUP BY 1
)
SELECT
    week_start,
    weekly_revenue,
    LAG(weekly_revenue) OVER (ORDER BY week_start) AS prev_week_revenue,
    ROUND(
        ((weekly_revenue - LAG(weekly_revenue) OVER (ORDER BY week_start))
         / LAG(weekly_revenue) OVER (ORDER BY week_start)) * 100
    , 2) AS wow_growth_pct
FROM weekly
ORDER BY week_start;


-- =============================================================
-- 11. DISCOUNT IMPACT ANALYSIS
-- =============================================================
SELECT
    CASE
        WHEN ol.discount = 0    THEN 'No Discount'
        WHEN ol.discount <= 0.05 THEN '1-5%'
        WHEN ol.discount <= 0.10 THEN '6-10%'
        WHEN ol.discount <= 0.15 THEN '11-15%'
        ELSE '16%+'
    END                                        AS discount_band,
    COUNT(DISTINCT ol.invoice_no)              AS orders,
    SUM(ol.quantity)                           AS units_sold,
    ROUND(SUM(ol.line_total), 2)               AS net_revenue,
    ROUND(SUM(ol.line_total - ol.cost_price), 2) AS gross_profit,
    ROUND(
        (SUM(ol.line_total - ol.cost_price) / SUM(ol.line_total)) * 100
    , 2)                                       AS margin_pct
FROM order_lines ol
GROUP BY 1
ORDER BY MIN(ol.discount);
