-- Comprehensive E-commerce Database Schema for LangGraph Data Analysis Copilot
-- This provides realistic business data with proper relationships for complex queries

-- Drop existing tables (in correct order due to foreign keys)
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS sales_reps;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS regions;

-- Create lookup tables first
CREATE TABLE regions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    country TEXT NOT NULL,
    timezone TEXT NOT NULL
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    margin_percentage DECIMAL(5, 2) DEFAULT 20.0
);

CREATE TABLE sales_reps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    region_id INTEGER NOT NULL,
    hire_date DATE NOT NULL,
    commission_rate DECIMAL(5, 4) DEFAULT 0.05,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (region_id) REFERENCES regions(id)
);

CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    company TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    country TEXT DEFAULT 'USA',
    region_id INTEGER NOT NULL,
    customer_since DATE NOT NULL,
    credit_limit DECIMAL(10, 2) DEFAULT 5000.00,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (region_id) REFERENCES regions(id)
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    category_id INTEGER NOT NULL,
    description TEXT,
    unit_price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    weight_kg DECIMAL(8, 3),
    dimensions TEXT,
    stock_quantity INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT 1,
    created_date DATE NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    sales_rep_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    ship_date DATE,
    delivery_date DATE,
    status TEXT NOT NULL DEFAULT 'pending',
    shipping_cost DECIMAL(10, 2) DEFAULT 0.00,
    tax_amount DECIMAL(10, 2) DEFAULT 0.00,
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    notes TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (sales_rep_id) REFERENCES sales_reps(id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount_percentage DECIMAL(5, 2) DEFAULT 0.00,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Insert lookup data
INSERT INTO regions (name, country, timezone) VALUES
('North America East', 'USA', 'EST'),
('North America West', 'USA', 'PST'),
('Europe', 'Various', 'CET'),
('Asia Pacific', 'Various', 'JST');

INSERT INTO categories (name, description, margin_percentage) VALUES
('Electronics', 'Computers, phones, and electronic devices', 25.0),
('Furniture', 'Office and home furniture', 35.0),
('Accessories', 'Small items and add-ons', 45.0),
('Software', 'Digital products and licenses', 80.0);

INSERT INTO sales_reps (first_name, last_name, email, phone, region_id, hire_date, commission_rate) VALUES
('Alice', 'Johnson', 'alice.johnson@company.com', '555-0101', 1, '2022-01-15', 0.06),
('Bob', 'Smith', 'bob.smith@company.com', '555-0102', 1, '2022-03-20', 0.05),
('Carol', 'Davis', 'carol.davis@company.com', '555-0103', 2, '2021-11-10', 0.07),
('David', 'Wilson', 'david.wilson@company.com', '555-0104', 2, '2023-02-01', 0.05),
('Emma', 'Brown', 'emma.brown@company.com', '555-0105', 3, '2022-08-15', 0.06),
('Frank', 'Miller', 'frank.miller@company.com', '555-0106', 4, '2023-01-10', 0.05);

INSERT INTO customers (first_name, last_name, email, phone, company, city, state, region_id, customer_since, credit_limit) VALUES
('John', 'Doe', 'john.doe@email.com', '555-1001', 'Tech Corp', 'New York', 'NY', 1, '2023-01-15', 10000.00),
('Jane', 'Smith', 'jane.smith@email.com', '555-1002', 'Design Studio', 'Boston', 'MA', 1, '2023-02-20', 7500.00),
('Mike', 'Johnson', 'mike.johnson@email.com', '555-1003', 'StartupXYZ', 'San Francisco', 'CA', 2, '2023-03-10', 15000.00),
('Sarah', 'Williams', 'sarah.williams@email.com', '555-1004', 'Consulting Inc', 'Los Angeles', 'CA', 2, '2023-01-25', 12000.00),
('Tom', 'Brown', 'tom.brown@email.com', '555-1005', 'Manufacturing Co', 'Chicago', 'IL', 1, '2022-12-01', 20000.00),
('Lisa', 'Davis', 'lisa.davis@email.com', '555-1006', 'Retail Chain', 'Miami', 'FL', 1, '2023-04-15', 8000.00),
('Chris', 'Wilson', 'chris.wilson@email.com', '555-1007', 'Agency Pro', 'Seattle', 'WA', 2, '2023-02-28', 9500.00),
('Amy', 'Taylor', 'amy.taylor@email.com', '555-1008', 'E-commerce Ltd', 'Austin', 'TX', 2, '2023-03-20', 11000.00);

INSERT INTO products (name, sku, category_id, description, unit_price, cost, weight_kg, stock_quantity, created_date) VALUES
-- Electronics
('Laptop Pro 15"', 'LAP-PRO-15', 1, 'High-performance laptop with 15" display', 1299.99, 850.00, 2.1, 25, '2023-01-01'),
('Laptop Air 13"', 'LAP-AIR-13', 1, 'Lightweight laptop with 13" display', 999.99, 650.00, 1.4, 30, '2023-01-01'),
('Gaming Laptop 17"', 'LAP-GAM-17', 1, 'Gaming laptop with 17" display and RTX graphics', 1899.99, 1200.00, 3.2, 15, '2023-01-01'),
('Monitor 27" 4K', 'MON-27-4K', 1, '27-inch 4K monitor with USB-C', 349.99, 220.00, 6.8, 40, '2023-01-01'),
('Tablet 10"', 'TAB-10', 1, '10-inch tablet with stylus support', 329.99, 200.00, 0.5, 35, '2023-01-01'),
('Webcam HD', 'WEB-HD', 1, '1080p webcam with auto-focus', 59.99, 25.00, 0.2, 60, '2023-01-01'),
('Printer Laser', 'PRT-LAS', 1, 'Monochrome laser printer', 299.99, 180.00, 12.5, 20, '2023-01-01'),

-- Furniture
('Executive Chair', 'CHR-EXEC', 2, 'Leather executive office chair', 449.99, 250.00, 25.0, 18, '2023-01-01'),
('Office Chair', 'CHR-OFF', 2, 'Ergonomic office chair with lumbar support', 249.50, 140.00, 18.5, 45, '2023-01-01'),
('Standing Desk', 'DSK-STND', 2, 'Height-adjustable standing desk', 599.00, 320.00, 35.0, 22, '2023-01-01'),
('Conference Table', 'TBL-CONF', 2, '8-person conference table', 899.99, 480.00, 65.0, 8, '2023-01-01'),
('Bookshelf', 'SHF-BOOK', 2, '5-tier wooden bookshelf', 199.99, 110.00, 28.0, 25, '2023-01-01'),
('Filing Cabinet', 'CAB-FILE', 2, '4-drawer filing cabinet', 189.99, 105.00, 32.0, 15, '2023-01-01'),

-- Accessories
('Wireless Mouse', 'MOU-WIR', 3, 'Ergonomic wireless mouse', 29.99, 12.00, 0.1, 100, '2023-01-01'),
('Gaming Mouse', 'MOU-GAM', 3, 'RGB gaming mouse with programmable buttons', 69.99, 28.00, 0.15, 75, '2023-01-01'),
('Mechanical Keyboard', 'KEY-MECH', 3, 'RGB mechanical keyboard', 89.99, 45.00, 1.2, 50, '2023-01-01'),
('Bluetooth Speakers', 'SPK-BT', 3, 'Portable Bluetooth speakers', 119.99, 55.00, 0.8, 40, '2023-01-01'),
('USB Hub', 'HUB-USB', 3, '7-port USB 3.0 hub', 24.99, 8.00, 0.3, 80, '2023-01-01'),
('Phone Holder', 'HLD-PHN', 3, 'Adjustable phone holder', 19.99, 6.00, 0.2, 120, '2023-01-01'),

-- Software
('Office Suite Pro', 'SW-OFF-PRO', 4, 'Professional office software suite', 199.99, 20.00, 0.0, 999, '2023-01-01'),
('Design Software', 'SW-DES', 4, 'Professional design and graphics software', 299.99, 30.00, 0.0, 999, '2023-01-01'),
('Antivirus Premium', 'SW-AV-PREM', 4, 'Premium antivirus with advanced protection', 79.99, 8.00, 0.0, 999, '2023-01-01');

-- Insert orders with realistic data
INSERT INTO orders (customer_id, sales_rep_id, order_date, ship_date, delivery_date, status, shipping_cost, tax_amount) VALUES
-- Q1 2024 orders
(1, 1, '2024-01-15', '2024-01-16', '2024-01-18', 'delivered', 15.99, 104.00),
(2, 1, '2024-01-20', '2024-01-21', '2024-01-23', 'delivered', 5.99, 2.40),
(3, 2, '2024-02-10', '2024-02-11', '2024-02-14', 'delivered', 25.99, 19.96),
(4, 3, '2024-02-15', '2024-02-16', '2024-02-20', 'delivered', 45.99, 47.92),
(5, 1, '2024-03-01', '2024-03-02', '2024-03-05', 'delivered', 20.99, 28.00),
(6, 2, '2024-03-10', '2024-03-11', '2024-03-13', 'delivered', 8.99, 7.20),
(7, 2, '2024-03-20', '2024-03-21', '2024-03-25', 'delivered', 30.99, 32.00),
(8, 4, '2024-03-25', '2024-03-26', '2024-03-28', 'delivered', 12.99, 6.40),

-- Q2 2024 orders
(3, 3, '2024-04-05', '2024-04-06', '2024-04-09', 'delivered', 18.99, 80.00),
(4, 4, '2024-04-12', '2024-04-13', '2024-04-15', 'delivered', 7.99, 4.80),
(5, 1, '2024-04-18', '2024-04-19', '2024-04-22', 'delivered', 15.99, 8.40),
(6, 2, '2024-05-02', '2024-05-03', '2024-05-06', 'delivered', 12.99, 7.36),
(7, 3, '2024-05-15', '2024-05-16', '2024-05-18', 'delivered', 16.99, 26.40),
(8, 4, '2024-05-22', '2024-05-23', '2024-05-25', 'delivered', 10.99, 9.60),
(1, 1, '2024-06-08', '2024-06-09', '2024-06-12', 'delivered', 22.99, 15.20),
(2, 2, '2024-06-15', '2024-06-16', '2024-06-18', 'delivered', 8.99, 6.40),

-- Q3 2024 orders
(3, 3, '2024-07-03', '2024-07-04', '2024-07-08', 'delivered', 35.99, 151.99),
(4, 4, '2024-07-10', '2024-07-11', '2024-07-13', 'delivered', 9.99, 5.60),
(5, 1, '2024-07-18', '2024-07-19', '2024-07-22', 'delivered', 28.99, 36.00),
(6, 2, '2024-08-05', '2024-08-06', '2024-08-09', 'delivered', 55.99, 71.99),
(7, 3, '2024-08-12', '2024-08-13', '2024-08-16', 'delivered', 25.99, 24.00),
(8, 4, '2024-08-20', '2024-08-21', '2024-08-23', 'delivered', 18.99, 10.40),
(1, 1, '2024-09-02', '2024-09-03', '2024-09-05', 'delivered', 20.99, 12.80),
(2, 2, '2024-09-15', '2024-09-16', '2024-09-19', 'delivered', 45.99, 55.99),

-- Recent orders (some pending/shipped)
(3, 3, '2024-09-25', '2024-09-26', NULL, 'shipped', 25.99, 104.00),
(4, 4, '2024-09-28', NULL, NULL, 'pending', 0.00, 0.00),
(5, 1, '2024-09-30', NULL, NULL, 'pending', 0.00, 0.00);

-- Insert order items (products in each order)
INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_percentage) VALUES
-- Order 1: Laptop Pro
(1, 1, 1, 1299.99, 0.00),
-- Order 2: Wireless Mouse
(2, 14, 2, 29.99, 0.00),
-- Order 3: Office Chair + Bookshelf
(3, 9, 1, 249.50, 0.00),
(3, 12, 1, 199.99, 10.00),
-- Order 4: Standing Desk
(4, 10, 1, 599.00, 0.00),
-- Order 5: Monitor
(5, 4, 1, 349.99, 0.00),
-- Order 6: Mechanical Keyboard
(6, 16, 1, 89.99, 0.00),
-- Order 7: Bookshelf (2 units) + USB Hub
(7, 12, 2, 199.99, 5.00),
(7, 18, 1, 24.99, 0.00),
-- Order 8: Phone Holder
(8, 19, 1, 19.99, 0.00),

-- Q2 orders
(9, 2, 1, 999.99, 0.00),
(10, 6, 1, 59.99, 0.00),
(11, 18, 3, 24.99, 0.00),
(11, 19, 2, 19.99, 0.00),
(12, 18, 2, 24.99, 0.00),
(12, 19, 1, 19.99, 0.00),
(13, 5, 1, 329.99, 0.00),
(14, 17, 1, 119.99, 0.00),
(15, 13, 1, 189.99, 0.00),
(16, 19, 2, 19.99, 0.00),
(16, 18, 1, 24.99, 0.00),

-- Q3 orders
(17, 3, 1, 1899.99, 0.00),
(18, 15, 1, 69.99, 0.00),
(19, 8, 1, 449.99, 0.00),
(20, 11, 1, 899.99, 0.00),
(21, 7, 1, 299.99, 0.00),
(22, 7, 1, 299.99, 5.00),
(22, 16, 1, 89.99, 0.00),
(23, 12, 1, 199.99, 0.00),
(24, 7, 1, 299.99, 0.00),
(24, 17, 1, 119.99, 0.00),
(24, 20, 2, 199.99, 0.00),

-- Recent orders
(25, 1, 1, 1299.99, 0.00),
(26, 4, 2, 349.99, 0.00),
(27, 10, 1, 599.00, 0.00);

-- Create comprehensive indexes for performance
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
CREATE INDEX idx_orders_sales_rep_date ON orders(sales_rep_id, order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_customers_region ON customers(region_id);
CREATE INDEX idx_customers_company ON customers(company);
CREATE INDEX idx_sales_reps_region ON sales_reps(region_id);
