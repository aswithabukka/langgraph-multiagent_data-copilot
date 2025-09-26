# 🗄️ Enhanced Database Schema - LangGraph Data Analysis Copilot

## 📊 Database Overview

The database has been significantly enhanced with **7 interconnected tables** that support complex business analytics, joins, aggregations, and real-world scenarios.

### 🏗️ **Database Architecture**

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   regions   │    │ sales_reps   │    │ customers   │
│             │◄───┤              │    │             │
│ • id        │    │ • id         │    │ • id        │
│ • name      │    │ • first_name │    │ • first_name│
│ • country   │    │ • last_name  │    │ • last_name │
│ • timezone  │    │ • region_id  │◄───┤ • region_id │
└─────────────┘    │ • hire_date  │    │ • company   │
                   │ • commission │    │ • city      │
                   └──────────────┘    │ • state     │
                                       └─────────────┘
                                              │
┌─────────────┐    ┌──────────────┐          │
│ categories  │    │   products   │          │
│             │    │              │          │
│ • id        │◄───┤ • id         │          │
│ • name      │    │ • name       │          │
│ • margin_%  │    │ • sku        │          │
└─────────────┘    │ • category_id│          │
                   │ • unit_price │          │
                   │ • cost       │          │
                   │ • stock_qty  │          │
                   └──────────────┘          │
                          │                  │
                          │                  │
                   ┌──────────────┐    ┌─────────────┐
                   │ order_items  │    │   orders    │
                   │              │    │             │
                   │ • id         │    │ • id        │
                   │ • order_id   │◄───┤ • customer_id│◄──┘
                   │ • product_id │◄───┤ • sales_rep_id│
                   │ • quantity   │    │ • order_date│
                   │ • unit_price │    │ • status    │
                   │ • discount   │    │ • ship_date │
                   └──────────────┘    └─────────────┘
```

## 📋 **Table Details**

### 1. **regions** (4 records)
- **Purpose**: Geographic regions for sales territories
- **Key Fields**: `name`, `country`, `timezone`
- **Data**: North America East/West, Europe, Asia Pacific

### 2. **categories** (4 records)
- **Purpose**: Product categorization with margin data
- **Key Fields**: `name`, `description`, `margin_percentage`
- **Data**: Electronics (25%), Furniture (35%), Accessories (45%), Software (80%)

### 3. **sales_reps** (6 records)
- **Purpose**: Sales team information with performance data
- **Key Fields**: `first_name`, `last_name`, `region_id`, `commission_rate`, `hire_date`
- **Relationships**: → `regions`

### 4. **customers** (8 records)
- **Purpose**: Customer information with company details
- **Key Fields**: `first_name`, `last_name`, `company`, `city`, `state`, `credit_limit`
- **Relationships**: → `regions`

### 5. **products** (21 records)
- **Purpose**: Product catalog with pricing and inventory
- **Key Fields**: `name`, `sku`, `unit_price`, `cost`, `stock_quantity`
- **Categories**: Laptops, Monitors, Furniture, Accessories, Software
- **Relationships**: → `categories`

### 6. **orders** (27 records)
- **Purpose**: Order header information
- **Key Fields**: `order_date`, `status`, `shipping_cost`, `tax_amount`
- **Statuses**: delivered, shipped, pending
- **Relationships**: → `customers`, `sales_reps`

### 7. **order_items** (35+ records)
- **Purpose**: Individual line items within orders
- **Key Fields**: `quantity`, `unit_price`, `discount_percentage`
- **Relationships**: → `orders`, `products`

## 🎯 **Complex Query Examples**

Now you can ask sophisticated business questions:

### **Sales Analytics**
- "Show me total revenue by sales rep with their commission rates"
- "Which region has the highest average order value?"
- "What's the monthly sales trend by product category?"
- "Who are the top 3 customers by total purchase amount?"

### **Product Performance**
- "Which products have the highest profit margins?"
- "Show me products that are running low on stock"
- "What's the average discount given per product category?"
- "Which electronics products sell the most?"

### **Customer Analysis**
- "List customers with orders over $1000 and their companies"
- "Which customers haven't ordered in the last 3 months?"
- "Show me customer distribution by region and state"
- "What's the average credit limit by customer region?"

### **Complex Joins & Aggregations**
- "Show me total sales by region, including sales rep names and customer count"
- "Calculate profit margins by product category with total quantities sold"
- "List all pending orders with customer details and sales rep information"
- "Show me quarterly sales performance by sales rep with commission earned"

### **Time-Based Analysis**
- "Compare Q2 vs Q3 2024 sales performance"
- "Show me monthly order counts and average order values"
- "Which sales reps had the best performance in September 2024?"
- "What's the delivery time analysis by region?"

## 🔍 **Sample Complex Queries**

### Revenue by Sales Rep with Commissions
```sql
SELECT 
    sr.first_name || ' ' || sr.last_name as sales_rep,
    r.name as region,
    COUNT(o.id) as total_orders,
    SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percentage/100)) as total_revenue,
    SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percentage/100)) * sr.commission_rate as commission_earned
FROM sales_reps sr
JOIN regions r ON sr.region_id = r.id
LEFT JOIN orders o ON sr.id = o.sales_rep_id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY sr.id, sr.first_name, sr.last_name, r.name, sr.commission_rate
ORDER BY total_revenue DESC;
```

### Top Customers by Company
```sql
SELECT 
    c.company,
    c.first_name || ' ' || c.last_name as contact_name,
    c.city || ', ' || c.state as location,
    COUNT(o.id) as total_orders,
    SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percentage/100)) as total_spent,
    c.credit_limit
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY c.id, c.company, c.first_name, c.last_name, c.city, c.state, c.credit_limit
ORDER BY total_spent DESC;
```

## 🚀 **Enhanced Capabilities**

### **Multi-Table Joins**
- Customer → Orders → Order Items → Products → Categories
- Sales Reps → Regions and Orders
- Products → Categories with margin analysis

### **Business Intelligence**
- **Profitability Analysis**: Cost vs. selling price with margins
- **Sales Performance**: Rep performance with commission tracking
- **Customer Segmentation**: By region, company size, purchase history
- **Inventory Management**: Stock levels and reorder points
- **Geographic Analysis**: Regional performance and timezone considerations

### **Real-World Scenarios**
- **Order Fulfillment**: Track orders from pending → shipped → delivered
- **Commission Calculations**: Automatic commission computation
- **Discount Analysis**: Track discount effectiveness
- **Seasonal Trends**: Quarter-over-quarter comparisons
- **Customer Lifetime Value**: Historical purchase analysis

## 📈 **Business Metrics Available**

- **Revenue Metrics**: Total sales, average order value, monthly/quarterly trends
- **Product Metrics**: Best sellers, profit margins, inventory turnover
- **Customer Metrics**: Acquisition, retention, geographic distribution
- **Sales Rep Metrics**: Performance, commission earnings, territory analysis
- **Operational Metrics**: Order fulfillment times, shipping costs, tax analysis

---

**🎉 The database now supports enterprise-level analytics with realistic business relationships and comprehensive data for complex query scenarios!**
