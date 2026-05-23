-- =============================================================
-- RetailEdge Analytics Dashboard
-- schema.sql  |  Database Schema Definition
-- =============================================================
-- Compatible with: PostgreSQL 14+ / MySQL 8+ / SQLite 3
-- =============================================================

-- Drop tables if rebuilding from scratch
DROP TABLE IF EXISTS order_lines;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS countries;

-- -------------------------------------------------------------
-- 1. COUNTRIES
-- -------------------------------------------------------------
CREATE TABLE countries (
    country_id   SERIAL PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    region       VARCHAR(60),
    currency     CHAR(3)  DEFAULT 'GBP'
);

-- -------------------------------------------------------------
-- 2. CUSTOMERS
-- -------------------------------------------------------------
CREATE TABLE customers (
    customer_id   VARCHAR(10)  PRIMARY KEY,
    customer_name VARCHAR(120) NOT NULL,
    country_id    INT REFERENCES countries(country_id),
    is_guest      BOOLEAN      DEFAULT FALSE,
    created_at    DATE
);

-- -------------------------------------------------------------
-- 3. PRODUCTS
-- -------------------------------------------------------------
CREATE TABLE products (
    stock_code   VARCHAR(20)  PRIMARY KEY,
    description  VARCHAR(200) NOT NULL,
    category     VARCHAR(60),
    unit_cost    NUMERIC(10,2) NOT NULL CHECK (unit_cost > 0),
    unit_price   NUMERIC(10,2) NOT NULL CHECK (unit_price > 0)
);

-- -------------------------------------------------------------
-- 4. ORDERS  (invoice header)
-- -------------------------------------------------------------
CREATE TABLE orders (
    invoice_no    VARCHAR(20) PRIMARY KEY,
    invoice_date  DATE        NOT NULL,
    customer_id   VARCHAR(10) REFERENCES customers(customer_id),
    country_id    INT         REFERENCES countries(country_id)
);

-- Index for date-range queries
CREATE INDEX idx_orders_date ON orders(invoice_date);

-- -------------------------------------------------------------
-- 5. ORDER_LINES  (invoice detail)
-- -------------------------------------------------------------
CREATE TABLE order_lines (
    line_id      SERIAL       PRIMARY KEY,
    invoice_no   VARCHAR(20)  NOT NULL REFERENCES orders(invoice_no),
    stock_code   VARCHAR(20)  NOT NULL REFERENCES products(stock_code),
    quantity     INT          NOT NULL CHECK (quantity > 0),
    unit_price   NUMERIC(10,2) NOT NULL CHECK (unit_price > 0),
    discount     NUMERIC(5,2)  DEFAULT 0.00 CHECK (discount >= 0 AND discount < 1),
    line_total   NUMERIC(12,2) GENERATED ALWAYS AS
                     (ROUND(quantity * unit_price * (1 - discount), 2)) STORED,
    cost_price   NUMERIC(12,2)
);

-- Index to speed up product-level aggregations
CREATE INDEX idx_lines_stock ON order_lines(stock_code);
CREATE INDEX idx_lines_invoice ON order_lines(invoice_no);
