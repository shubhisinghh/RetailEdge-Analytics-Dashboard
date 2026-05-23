-- =============================================================
-- RetailEdge Analytics Dashboard
-- views.sql  |  Reusable Database Views for Reporting
-- =============================================================

-- =============================================================
-- VIEW 1: vw_order_summary
-- One row per invoice with totals and margin
-- =============================================================
CREATE OR REPLACE VIEW vw_order_summary AS
SELECT
    o.invoice_no,
    o.invoice_date,
    EXTRACT(YEAR  FROM o.invoice_date)              AS year,
    EXTRACT(MONTH FROM o.invoice_date)              AS month,
    TO_CHAR(o.invoice_date, 'Mon')                  AS month_name,
    CONCAT('Q', EXTRACT(QUARTER FROM o.invoice_date)) AS quarter,
    TO_CHAR(o.invoice_date, 'Day')                  AS day_of_week,
    c.customer_id,
    c.customer_name,
    c.is_guest,
    co.country_name,
    co.region,
    COUNT(ol.line_id)                               AS line_items,
    SUM(ol.quantity)                                AS total_units,
    ROUND(SUM(ol.line_total), 2)                    AS order_revenue,
    ROUND(SUM(ol.line_total - ol.cost_price), 2)    AS order_profit,
    ROUND(
        (SUM(ol.line_total - ol.cost_price) / SUM(ol.line_total)) * 100
    , 2)                                            AS margin_pct
FROM orders o
JOIN order_lines ol ON o.invoice_no   = ol.invoice_no
JOIN customers   c  ON o.customer_id  = c.customer_id
JOIN countries   co ON o.country_id   = co.country_id
GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12;


-- =============================================================
-- VIEW 2: vw_monthly_kpis
-- Pre-aggregated monthly KPIs for the dashboard
-- =============================================================
CREATE OR REPLACE VIEW vw_monthly_kpis AS
SELECT
    year,
    month,
    month_name,
    COUNT(DISTINCT invoice_no)          AS total_orders,
    SUM(total_units)                    AS total_units_sold,
    ROUND(SUM(order_revenue), 2)        AS total_revenue,
    ROUND(SUM(order_profit), 2)         AS total_profit,
    ROUND(AVG(order_revenue), 2)        AS avg_order_value,
    ROUND(AVG(margin_pct), 2)           AS avg_margin_pct,
    COUNT(DISTINCT customer_id)
        FILTER (WHERE is_guest = FALSE) AS unique_customers
FROM vw_order_summary
GROUP BY 1, 2, 3
ORDER BY 1, 2;


-- =============================================================
-- VIEW 3: vw_product_performance
-- Product-level revenue and profitability
-- =============================================================
CREATE OR REPLACE VIEW vw_product_performance AS
SELECT
    p.stock_code,
    p.description,
    p.category,
    p.unit_price                                    AS list_price,
    SUM(ol.quantity)                                AS units_sold,
    ROUND(SUM(ol.line_total), 2)                    AS net_revenue,
    ROUND(SUM(ol.line_total - ol.cost_price), 2)    AS gross_profit,
    ROUND(
        (SUM(ol.line_total - ol.cost_price) / SUM(ol.line_total)) * 100
    , 2)                                            AS margin_pct,
    ROUND(SUM(ol.discount * ol.line_total) /
          NULLIF(SUM(ol.line_total), 0) * 100, 2)   AS avg_discount_pct,
    COUNT(DISTINCT ol.invoice_no)                   AS order_count
FROM products p
JOIN order_lines ol ON p.stock_code = ol.stock_code
GROUP BY 1, 2, 3, 4;


-- =============================================================
-- VIEW 4: vw_customer_ltv
-- Customer lifetime value and segment data
-- =============================================================
CREATE OR REPLACE VIEW vw_customer_ltv AS
SELECT
    c.customer_id,
    c.customer_name,
    co.country_name,
    COUNT(DISTINCT o.invoice_no)                    AS total_orders,
    MIN(o.invoice_date)                             AS first_order_date,
    MAX(o.invoice_date)                             AS last_order_date,
    CURRENT_DATE - MAX(o.invoice_date)              AS days_since_last_order,
    ROUND(SUM(ol.line_total), 2)                    AS lifetime_revenue,
    ROUND(SUM(ol.line_total - ol.cost_price), 2)    AS lifetime_profit,
    ROUND(SUM(ol.line_total)
          / COUNT(DISTINCT o.invoice_no), 2)        AS avg_order_value
FROM customers c
JOIN orders o       ON c.customer_id  = o.customer_id
JOIN order_lines ol ON o.invoice_no   = ol.invoice_no
JOIN countries   co ON o.country_id   = co.country_id
WHERE c.is_guest = FALSE
GROUP BY 1, 2, 3;
