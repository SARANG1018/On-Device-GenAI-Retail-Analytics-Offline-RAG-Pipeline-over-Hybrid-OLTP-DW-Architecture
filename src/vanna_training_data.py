# Vanna.AI training data for SQL generation
VANNA_TRAINING_DATA = [
    # Basic dimension queries
    {
        "question": "Show all product categories",
        "sql": "SELECT DISTINCT category_name FROM fa25_ssc_dim_product ORDER BY category_name"
    },
    {
        "question": "What are the different regions?",
        "sql": "SELECT DISTINCT region FROM fa25_ssc_dim_customer ORDER BY region"
    },
    
    # ===== fa25_ssc_fact_sales QUERIES =====
    {
        "question": "What's the total sales by region?",
        "sql": """
SELECT 
    dc.region,
    SUM(fs.sales) as total_sales,
    COUNT(*) as transaction_count,
    AVG(fs.sales) as avg_transaction
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.region
ORDER BY total_sales DESC
        """
    },
    {
        "question": "Show me sales by product category",
        "sql": """
SELECT 
    dp.category_name,
    SUM(fs.sales) as total_sales,
    SUM(fs.quantity) as total_units,
    COUNT(*) as transaction_count
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.category_name
ORDER BY total_sales DESC
        """
    },
    {
        "question": "What's the profit margin by subcategory?",
        "sql": """
SELECT 
    dp.subcategory_name,
    SUM(fs.sales) as total_sales,
    SUM(fs.profit) as total_profit,
    ROUND(SUM(fs.profit) / SUM(fs.sales) * 100, 2) as profit_margin_pct
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.subcategory_name
ORDER BY profit_margin_pct DESC
        """
    },
    {
        "question": "Top 10 products by revenue",
        "sql": """
SELECT 
    dp.product_name,
    dp.category_name,
    SUM(fs.sales) as total_sales,
    SUM(fs.quantity) as units_sold,
    SUM(fs.profit) as total_profit
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.product_name, dp.category_name
ORDER BY total_sales DESC
LIMIT 10
        """
    },
    
    # ===== TIME-BASED QUERIES =====
    {
        "question": "What are the sales trends over time?",
        "sql": """
SELECT 
    dd.full_date,
    SUM(fs.sales) as daily_sales,
    COUNT(*) as transaction_count,
    SUM(fs.profit) as daily_profit
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
GROUP BY dd.full_date
ORDER BY dd.full_date DESC
        """
    },
    {
        "question": "Compare sales by month",
        "sql": """
SELECT 
    dd.year,
    dd.month,
    SUM(fs.sales) as monthly_sales,
    COUNT(*) as transaction_count,
    AVG(fs.sales) as avg_transaction
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
GROUP BY dd.year, dd.month
ORDER BY dd.year DESC, dd.month DESC
        """
    },
    {
        "question": "Which day of the week has the most sales?",
        "sql": """
SELECT 
    dd.day,
    COUNT(*) as transaction_count,
    SUM(fs.sales) as total_sales,
    AVG(fs.sales) as avg_transaction
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
GROUP BY dd.day
ORDER BY total_sales DESC
        """
    },
    
    # ===== fa25_ssc_fact_return QUERIES =====
    {
        "question": "What's the return rate by region?",
        "sql": """
SELECT 
    dc.region,
    COUNT(DISTINCT CASE WHEN fr.return_fact_key IS NOT NULL THEN fs.sales_key END) as total_returns,
    COUNT(DISTINCT fs.sales_key) as total_orders,
    ROUND(COUNT(DISTINCT CASE WHEN fr.return_fact_key IS NOT NULL THEN fs.sales_key END) * 100.0 / COUNT(DISTINCT fs.sales_key), 2) as return_rate_pct
FROM fa25_ssc_fact_sales fs
LEFT JOIN fa25_ssc_fact_return fr ON fs.sales_key = fr.order_key
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.region
ORDER BY return_rate_pct DESC
        """
    },
    {
        "question": "Show me returns by status",
        "sql": """
SELECT 
    fr.return_status,
    COUNT(DISTINCT fr.return_fact_key) as return_count,
    COUNT(DISTINCT fr.order_key) as related_orders,
    SUM(fs.sales) as returned_sales_value
FROM fa25_ssc_fact_return fr
JOIN fa25_ssc_fact_sales fs ON fr.order_key = fs.sales_key
GROUP BY fr.return_status
ORDER BY return_count DESC
        """
    },
    {
        "question": "Which products are being returned most often?",
        "sql": """
SELECT 
    dp.product_name,
    dp.category_name,
    COUNT(DISTINCT fr.return_fact_key) as return_count,
    COUNT(DISTINCT fr.order_key) as related_orders,
    SUM(fs.sales) as returned_sales_value
FROM fa25_ssc_fact_return fr
JOIN fa25_ssc_fact_sales fs ON fr.order_key = fs.sales_key
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.product_name, dp.category_name
ORDER BY return_count DESC
LIMIT 10
        """
    },
    {
        "question": "What's the return rate by product category?",
        "sql": """
SELECT 
    dp.category_name,
    COUNT(DISTINCT CASE WHEN fr.return_fact_key IS NOT NULL THEN fs.sales_key END) as return_count,
    COUNT(DISTINCT fs.sales_key) as total_orders,
    ROUND(COUNT(DISTINCT CASE WHEN fr.return_fact_key IS NOT NULL THEN fs.sales_key END) * 100.0 / COUNT(DISTINCT fs.sales_key), 2) as return_rate_pct
FROM fa25_ssc_fact_sales fs
LEFT JOIN fa25_ssc_fact_return fr ON fs.sales_key = fr.order_key
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.category_name
ORDER BY return_rate_pct DESC
        """
    },
    
    # ===== CUSTOMER ANALYTICS =====
    {
        "question": "Show me customer spending by region",
        "sql": """
SELECT 
    dc.region,
    COUNT(DISTINCT fs.customer_key) as unique_customers,
    SUM(fs.sales) as total_sales,
    AVG(fs.sales) as avg_transaction,
    SUM(fs.profit) as total_profit
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.region
ORDER BY total_sales DESC
        """
    },
    {
        "question": "Which region has the highest profit margin?",
        "sql": """
SELECT 
    dc.region,
    SUM(fs.sales) as total_sales,
    SUM(fs.profit) as total_profit,
    ROUND(SUM(fs.profit) / SUM(fs.sales) * 100, 2) as profit_margin_pct
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.region
ORDER BY profit_margin_pct DESC
        """
    },
    {
        "question": "Show geographic sales distribution by region",
        "sql": """
SELECT 
    dc.region,
    COUNT(DISTINCT fs.customer_key) as unique_customers,
    COUNT(*) as transaction_count,
    SUM(fs.sales) as total_sales
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.region
ORDER BY total_sales DESC
        """
    },
    
    # ===== DISCOUNT ANALYTICS =====
    {
        "question": "How do discounts impact profit?",
        "sql": """
SELECT 
    CASE 
        WHEN fs.discount = 0 THEN 'No Discount'
        WHEN fs.discount < 0.1 THEN '0-10%'
        WHEN fs.discount < 0.2 THEN '10-20%'
        ELSE '20%+'
    END as discount_range,
    COUNT(*) as order_count,
    AVG(fs.sales) as avg_sales,
    AVG(fs.profit) as avg_profit,
    ROUND(AVG(fs.profit) / AVG(fs.sales) * 100, 2) as profit_margin_pct
FROM fa25_ssc_fact_sales fs
GROUP BY discount_range
ORDER BY discount_range
        """
    },
    {
        "question": "What's the average shipping cost by region?",
        "sql": """
SELECT 
    dc.region,
    COUNT(*) as order_count,
    AVG(fs.shipping_cost) as avg_shipping_cost,
    SUM(fs.shipping_cost) as total_shipping_cost,
    AVG(fs.profit) as avg_profit
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.region
ORDER BY avg_shipping_cost DESC
        """
    },
    
    # ===== COMBINED ANALYSIS =====
    {
        "question": "Show me the top 5 most profitable products by region",
        "sql": """
SELECT 
    dc.region,
    dp.product_name,
    SUM(fs.profit) as total_profit,
    SUM(fs.sales) as total_sales,
    COUNT(*) as transaction_count
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dc.region, dp.product_name
ORDER BY dc.region, total_profit DESC
        """
    },
    {
        "question": "Compare profitability: Products vs Categories vs Regions",
        "sql": """
SELECT 
    dp.category_name,
    dp.product_name,
    dc.region,
    SUM(fs.sales) as total_sales,
    SUM(fs.profit) as total_profit,
    ROUND(SUM(fs.profit) / SUM(fs.sales) * 100, 2) as margin_pct
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dp.category_name, dp.product_name, dc.region
ORDER BY margin_pct DESC
LIMIT 20
        """
    },
    {
        "question": "Identify underperforming products (low sales, high returns)",
        "sql": """
SELECT 
    dp.product_name,
    dp.category_name,
    COUNT(DISTINCT fs.sales_key) as total_orders,
    SUM(fs.sales) as total_sales,
    COUNT(DISTINCT fr.return_fact_key) as return_count,
    ROUND(COUNT(DISTINCT CASE WHEN fr.return_fact_key IS NOT NULL THEN fs.sales_key END) * 100.0 / COUNT(DISTINCT fs.sales_key), 2) as return_rate_pct,
    SUM(fs.profit) as total_profit
FROM fa25_ssc_fact_sales fs
LEFT JOIN fa25_ssc_fact_return fr ON fs.sales_key = fr.order_key
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.product_name, dp.category_name
HAVING COUNT(DISTINCT fs.sales_key) > 0
ORDER BY return_rate_pct DESC, total_sales ASC
        """
    },
    
    # ===== ADDITIONAL COVERAGE: Customer & Geography =====
    {
        "question": "Show sales by customer country",
        "sql": """
SELECT 
    dc.country,
    COUNT(DISTINCT dc.customer_key) as unique_customers,
    COUNT(*) as transaction_count,
    SUM(fs.sales) as total_sales,
    SUM(fs.quantity) as units_sold,
    AVG(fs.sales) as avg_transaction_value
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.country
ORDER BY total_sales DESC
        """
    },
    {
        "question": "Analyze customer spending by city",
        "sql": """
SELECT 
    dc.city,
    dc.country,
    COUNT(DISTINCT dc.customer_key) as unique_customers,
    SUM(fs.sales) as total_sales,
    SUM(fs.profit) as total_profit,
    ROUND(AVG(fs.sales), 2) as avg_order_value
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
WHERE dc.city IS NOT NULL
GROUP BY dc.city, dc.country
ORDER BY total_sales DESC
LIMIT 20
        """
    },
    {
        "question": "Customer analysis by state and region",
        "sql": """
SELECT 
    dc.state,
    dc.region,
    COUNT(DISTINCT dc.customer_key) as unique_customers,
    SUM(fs.sales) as total_sales,
    SUM(fs.quantity) as total_units,
    ROUND(SUM(fs.profit) / SUM(fs.sales) * 100, 2) as profit_margin_pct
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.state, dc.region
ORDER BY total_sales DESC
        """
    },
    
    # ===== ADDITIONAL COVERAGE: Quantity & Profit Analysis =====
    {
        "question": "Show quantity sold by product category",
        "sql": """
SELECT 
    dp.category_name,
    SUM(fs.quantity) as total_units,
    COUNT(*) as transaction_count,
    AVG(fs.quantity) as avg_units_per_sale,
    SUM(fs.sales) as total_sales,
    ROUND(SUM(fs.sales) / SUM(fs.quantity), 2) as avg_price_per_unit
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.category_name
ORDER BY total_units DESC
        """
    },
    {
        "question": "Profit analysis by product and subcategory",
        "sql": """
SELECT 
    dp.category_name,
    dp.subcategory_name,
    COUNT(*) as order_count,
    SUM(fs.quantity) as units_sold,
    SUM(fs.sales) as revenue,
    SUM(fs.profit) as total_profit,
    ROUND(SUM(fs.profit) / SUM(fs.sales) * 100, 2) as profit_margin_pct,
    ROUND(AVG(fs.profit), 2) as avg_profit_per_order
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.category_name, dp.subcategory_name
ORDER BY total_profit DESC
        """
    },
    
    # ===== ADDITIONAL COVERAGE: Return Analysis with fa25_ssc_dim_return =====
    {
        "question": "Return analysis by return status and region",
        "sql": """
SELECT 
    fr.return_status,
    fr.return_region,
    COUNT(DISTINCT fr.return_fact_key) as return_count,
    COUNT(DISTINCT fr.customer_key) as affected_customers,
    SUM(fs.sales) as returned_sales_value,
    SUM(fs.profit) as lost_profit
FROM fa25_ssc_fact_return fr
JOIN fa25_ssc_fact_sales fs ON fr.order_key = fs.sales_key
GROUP BY fr.return_status, fr.return_region
ORDER BY return_count DESC
        """
    },
    {
        "question": "Which products have the highest return rate?",
        "sql": """
SELECT 
    dp.product_name,
    dp.category_name,
    COUNT(DISTINCT fs.sales_key) as total_sales,
    COUNT(DISTINCT fr.return_fact_key) as return_count,
    ROUND(COUNT(DISTINCT fr.return_fact_key) * 100.0 / COUNT(DISTINCT fs.sales_key), 2) as return_rate_pct,
    SUM(fs.sales) as revenue_at_risk
FROM fa25_ssc_fact_sales fs
LEFT JOIN fa25_ssc_fact_return fr ON fs.sales_key = fr.order_key
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.product_name, dp.category_name
HAVING COUNT(DISTINCT fr.return_fact_key) > 0
ORDER BY return_rate_pct DESC
        """
    },
    
    # ===== ADDITIONAL COVERAGE: Shipping Cost Analysis =====
    {
        "question": "Shipping cost impact on profitability by region",
        "sql": """
SELECT 
    dc.region,
    COUNT(*) as order_count,
    SUM(fs.sales) as total_sales,
    SUM(fs.shipping_cost) as total_shipping,
    ROUND(AVG(fs.shipping_cost), 2) as avg_shipping_cost,
    SUM(fs.profit) as net_profit,
    ROUND(SUM(fs.shipping_cost) * 100.0 / SUM(fs.sales), 2) as shipping_as_pct_of_sales,
    ROUND((SUM(fs.profit) - SUM(fs.shipping_cost)) / SUM(fs.sales) * 100, 2) as true_margin_pct
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.region
ORDER BY shipping_as_pct_of_sales DESC
        """
    },
    {
        "question": "Compare shipping costs across product categories",
        "sql": """
SELECT 
    dp.category_name,
    COUNT(*) as shipment_count,
    SUM(fs.shipping_cost) as total_shipping,
    ROUND(AVG(fs.shipping_cost), 2) as avg_shipping_per_order,
    SUM(fs.sales) as sales_value,
    SUM(fs.profit) as profit_before_shipping,
    ROUND((SUM(fs.profit) - SUM(fs.shipping_cost)), 2) as profit_after_shipping
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.category_name
ORDER BY avg_shipping_per_order DESC
        """
    },
    
    # ===== ADDITIONAL COVERAGE: Time Series with Month =====
    {
        "question": "Monthly sales and profit trends",
        "sql": """
SELECT 
    dd.year,
    dd.month,
    COUNT(DISTINCT fs.customer_key) as unique_customers,
    COUNT(*) as transaction_count,
    SUM(fs.sales) as monthly_sales,
    SUM(fs.quantity) as units_sold,
    SUM(fs.profit) as monthly_profit,
    ROUND(SUM(fs.profit) / SUM(fs.sales) * 100, 2) as profit_margin_pct,
    AVG(fs.sales) as avg_transaction_value
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
GROUP BY dd.year, dd.month
ORDER BY dd.year, dd.month
        """
    },
    {
        "question": "Sales performance by day of week across regions",
        "sql": """
SELECT 
    dd.day,
    dc.region,
    COUNT(*) as transaction_count,
    SUM(fs.sales) as daily_sales,
    SUM(fs.quantity) as units_sold,
    ROUND(AVG(fs.sales), 2) as avg_transaction,
    SUM(fs.profit) as daily_profit
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
GROUP BY dd.day, dc.region
ORDER BY dd.day, daily_sales DESC
        """
    },
    
    # ===== SIMPLE AGGREGATE QUERIES =====
    {
        "question": "What is our total revenue?",
        "sql": "SELECT SUM(sales) as total_revenue FROM fa25_ssc_fact_sales"
    },
    {
        "question": "What is the total number of orders?",
        "sql": "SELECT COUNT(DISTINCT sales_key) as total_orders FROM fa25_ssc_fact_sales"
    },
    {
        "question": "What is the average order value?",
        "sql": "SELECT AVG(sales) as average_order_value FROM fa25_ssc_fact_sales"
    },
    
    # ===== DATA AVAILABILITY QUERIES - IMPORTANT =====
    {
        "question": "What date range is our data from?",
        "sql": """
SELECT 
    MIN(full_date) as earliest_date,
    MAX(full_date) as latest_date,
    COUNT(DISTINCT date_key) as total_days_with_data
FROM fa25_ssc_dim_date
WHERE date_key IN (SELECT DISTINCT date_key FROM fa25_ssc_fact_sales)
        """
    },
    {
        "question": "What years are available in our database?",
        "sql": """
SELECT DISTINCT year as available_year FROM fa25_ssc_dim_date
WHERE date_key IN (SELECT DISTINCT date_key FROM fa25_ssc_fact_sales)
ORDER BY year DESC
        """
    },
    {
        "question": "What is the most recent date with sales data?",
        "sql": """
SELECT MAX(full_date) as most_recent_sales_date FROM fa25_ssc_fact_sales
JOIN fa25_ssc_dim_date USING (date_key)
        """
    },
    {
        "question": "What time period does our data cover?",
        "sql": """
SELECT 
    MIN(dd.full_date) as start_date,
    MAX(dd.full_date) as end_date,
    DATEDIFF(MAX(dd.full_date), MIN(dd.full_date)) as days_of_data
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
        """
    },
    {
        "question": "Show me all months with sales data",
        "sql": """
SELECT DISTINCT 
    year,
    month,
    COUNT(*) as transaction_count,
    SUM(sales) as monthly_revenue
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
GROUP BY year, month
ORDER BY year DESC, month DESC
        """
    },
    {
        "question": "What date range do we have 2025 data for?",
        "sql": """
SELECT 
    MIN(full_date) as start_date_2025,
    MAX(full_date) as end_date_2025
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
WHERE dd.year = 2025
        """
    },
    {
        "question": "Do we have 2014 data?",
        "sql": """
SELECT COUNT(*) as sales_count_2014 FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
WHERE dd.year = 2014
        """
    },
    {
        "question": "Do we have 2020 data?",
        "sql": """
SELECT COUNT(*) as sales_count_2020 FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
WHERE dd.year = 2020
        """
    },
    
    # ===== HELPFUL CONTEXT EXAMPLES =====
    {
        "question": "Can you show me sales from 2014?",
        "sql": """
SELECT COUNT(*) as record_count FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
WHERE dd.year = 2014
        """
    },
    {
        "question": "What's available in the system?",
        "sql": """
SELECT 
    'Date Range' as info_type,
    CONCAT(MIN(full_date), ' to ', MAX(full_date)) as info_value
FROM fa25_ssc_fact_sales fs
JOIN fa25_ssc_dim_date dd ON fs.date_key = dd.date_key
UNION ALL
SELECT 'Total Orders', COUNT(DISTINCT sales_key)
FROM fa25_ssc_fact_sales
UNION ALL
SELECT 'Total Customers', COUNT(DISTINCT customer_key)
FROM fa25_ssc_fact_sales
UNION ALL
SELECT 'Total Products', COUNT(DISTINCT product_key)
FROM fa25_ssc_fact_sales
        """
    },
    {
        "question": "Tell me about our current data in the system",
        "sql": """
SELECT 
    'Sales Records' as metric,
    COUNT(DISTINCT sales_key) as value
FROM fa25_ssc_fact_sales
UNION ALL
SELECT 'Return Records',
    COUNT(DISTINCT return_fact_key)
FROM fa25_ssc_fact_return
UNION ALL
SELECT 'Unique Customers',
    COUNT(DISTINCT customer_key)
FROM fa25_ssc_dim_customer
UNION ALL
SELECT 'Unique Products',
    COUNT(DISTINCT product_key)
FROM fa25_ssc_dim_product
UNION ALL
SELECT 'Date Range',
    CONCAT(MIN(full_date), ' to ', MAX(full_date))
FROM fa25_ssc_dim_date
WHERE date_key IN (SELECT DISTINCT date_key FROM fa25_ssc_fact_sales)
        """
    }
]

# Business rules and schema context for Vanna training
BUSINESS_RULES = """
DATABASE SCHEMA AND RULES:

=== FACT TABLES ===

1. fa25_ssc_fact_sales (Main transactional sales fact table):
   Keys:
   - sales_key: Sales transaction identifier (surrogate key)
   - customer_key: Foreign key to fa25_ssc_dim_customer
   - product_key: Foreign key to fa25_ssc_dim_product
   - date_key: Foreign key to fa25_ssc_dim_date
   - return_key: Foreign key to fa25_ssc_dim_return (nullable)
   
   Metrics:
   - sales: Dollar amount of sale
   - quantity: Number of units sold
   - discount: Discount percentage (0.0-1.0)
   - profit: Profit amount (sales - discount - costs)
   - shipping_cost: Shipping cost
   
   Timestamps:
   - created_at: When the record was loaded
   - updated_at: When the record was last updated

2. fa25_ssc_fact_return (Return transactions):
   Keys:
   - return_fact_key: Return fact identifier (surrogate key)
   - return_key: Foreign key to fa25_ssc_dim_return
   - order_key: Link to original order (sales_key)
   - customer_key: Foreign key to fa25_ssc_dim_customer
   - date_key: Foreign key to fa25_ssc_dim_date
   
   Attributes:
   - return_status: Pending, Approved, Rejected, Completed
   - return_region: Region where return was processed
   
   Timestamps:
   - created_at: When the record was loaded
   - updated_at: When the record was last updated

=== DIMENSION TABLES ===

3. fa25_ssc_dim_date (Time dimension):
   - date_key: Primary key (auto-increment)
   - full_date: Actual date
   - year, month, day: Time components

4. fa25_ssc_dim_customer (Customer dimension):
   - customer_key: Primary key (surrogate key)
   - customer_id: Customer identifier
   - customer_name: Customer name
   - country: Customer country
   - state: Customer state
   - city: Customer city
   - postal_code: Postal code
   - region: Central, East, South, West
   
   Timestamps:
   - created_at: When the record was loaded
   - updated_at: When the record was last updated

5. fa25_ssc_dim_product (Product dimension):
   - product_key: Primary key (surrogate key)
   - product_id: Product identifier
   - product_name: Product name
   - category_name: Technology, Furniture, Office Supplies
   - subcategory_name: Specific subcategory
   
   Timestamps:
   - created_at: When the record was loaded
   - updated_at: When the record was last updated

6. fa25_ssc_dim_return (Return dimension):
   - return_key: Primary key (surrogate key)
   - return_id: Return identifier
   - return_status: Status of return
   - return_region: Region where return was processed
   
   Timestamps:
   - created_at: When the record was loaded
   - updated_at: When the record was last updated

=== COMMON PATTERNS ===

Regional Analysis:
- Regional data: Central, East, South, West
- Use dc.region in queries

Product Analysis:
- 3 main categories: Technology, Furniture, Office Supplies
- Use category_name for broad analysis, subcategory_name for detail

Sales Metrics:
- For profit margin: (profit / sales) * 100
- For return rate: (count returns / count sales) * 100
- Always use date_key for date joins
- discount is a decimal 0.0-1.0

Return Analysis:
- Use fa25_ssc_fact_return table for detailed return info
- Link to fa25_ssc_fact_sales via order_key to get product/customer info
- return_status shows progression (Pending → Approved/Rejected → Completed)

Time-Based Analysis:
- Always JOIN fa25_ssc_fact_sales with fa25_ssc_dim_date on date_key
- Use day, month, year as needed
- For trends, GROUP BY full_date and ORDER BY full_date

Cross-dimensional:
- Combine region + product category for multi-dimensional analysis
- Use LEFT JOIN fa25_ssc_fact_return to preserve sales without returns
- For "top N" analysis, use ORDER BY DESC LIMIT N
"""

SCHEMA_DOCUMENTATION = """
COMPLETE OLAP STAR SCHEMA (6 Tables):

fa25_ssc_fact_sales TABLE:
├── Primary Key
│   └── sales_key (INT, auto_increment)
├── Foreign Keys
│   ├── customer_key → fa25_ssc_dim_customer.customer_key
│   ├── product_key → fa25_ssc_dim_product.product_key
│   ├── date_key → fa25_ssc_dim_date.date_key
│   └── return_key → fa25_ssc_dim_return.return_key (NULLABLE)
├── Measures
│   ├── sales (DECIMAL 10,2) - Revenue
│   ├── quantity (INT) - Units sold
│   ├── discount (DECIMAL 5,2) - Discount percentage
│   ├── profit (DECIMAL 10,2) - Profit
│   └── shipping_cost (DECIMAL 10,2) - Shipping
├── Timestamps
│   ├── created_at (TIMESTAMP) - Load timestamp
│   └── updated_at (TIMESTAMP) - Update timestamp
└── Total Columns: 12

fa25_ssc_fact_return TABLE:
├── Primary Key
│   └── return_fact_key (INT, auto_increment)
├── Foreign Keys
│   ├── return_key → fa25_ssc_dim_return.return_key
│   ├── order_key → fa25_ssc_fact_sales.sales_key
│   ├── customer_key → fa25_ssc_dim_customer.customer_key
│   └── date_key → fa25_ssc_dim_date.date_key
├── Attributes
│   ├── return_status (VARCHAR 50) - Pending, Approved, Rejected, Completed
│   └── return_region (VARCHAR 50) - Region
├── Timestamps
│   ├── created_at (TIMESTAMP) - Load timestamp
│   └── updated_at (TIMESTAMP) - Update timestamp
└── Total Columns: 9

fa25_ssc_dim_date TABLE:
├── Primary Key
│   └── date_key (INT, auto_increment)
├── Date Components
│   ├── full_date (DATE) - Actual calendar date
│   ├── year (INT) - Calendar year
│   ├── month (INT) - 1-12
│   └── day (INT) - Day of month
├── Timestamps
│   ├── created_at (TIMESTAMP) - Load timestamp
│   └── updated_at (TIMESTAMP) - Update timestamp
└── Total Columns: 7

fa25_ssc_dim_customer TABLE:
├── Primary Key
│   └── customer_key (INT, auto_increment)
├── Customer Identifiers
│   ├── customer_id (INT) - Natural key from OLTP
│   └── customer_name (VARCHAR 100)
├── Geography
│   ├── country (VARCHAR 50)
│   ├── state (VARCHAR 50)
│   ├── city (VARCHAR 50)
│   ├── postal_code (VARCHAR 10, NULLABLE)
│   └── region (VARCHAR 50) - Central, East, South, West
├── Timestamps
│   ├── created_at (TIMESTAMP) - Load timestamp
│   └── updated_at (TIMESTAMP) - Update timestamp
└── Total Columns: 10

fa25_ssc_dim_product TABLE:
├── Primary Key
│   └── product_key (INT, auto_increment)
├── Product Identifiers
│   ├── product_id (INT) - Natural key from OLTP
│   └── product_name (VARCHAR 100, NULLABLE)
├── Classification
│   ├── category_name (VARCHAR 100, NULLABLE) - Technology, Furniture, Office Supplies
│   └── subcategory_name (VARCHAR 100, NULLABLE)
├── Timestamps
│   ├── created_at (TIMESTAMP) - Load timestamp
│   └── updated_at (TIMESTAMP) - Update timestamp
└── Total Columns: 7

fa25_ssc_dim_return TABLE:
├── Primary Key
│   └── return_key (INT, auto_increment)
├── Return Identifiers
│   ├── return_id (INT) - Natural key from OLTP
│   └── return_status (VARCHAR 50) - Pending, Approved, Rejected, Completed
├── Return Details
│   └── return_region (VARCHAR 50) - Central, East, South, West
├── Timestamps
│   ├── created_at (TIMESTAMP) - Load timestamp
│   └── updated_at (TIMESTAMP) - Update timestamp
└── Total Columns: 6

TOTAL SCHEMA: 49 COLUMNS ACROSS 6 TABLES

=== FACT TABLE RELATIONSHIPS ===

fa25_ssc_fact_sales Joins:
- fa25_ssc_fact_sales.customer_key = fa25_ssc_dim_customer.customer_key
- fa25_ssc_fact_sales.product_key = fa25_ssc_dim_product.product_key
- fa25_ssc_fact_sales.date_key = fa25_ssc_dim_date.date_key
- fa25_ssc_fact_sales.return_key = fa25_ssc_dim_return.return_key (LEFT JOIN, nullable)

fa25_ssc_fact_return Joins:
- fa25_ssc_fact_return.customer_key = fa25_ssc_dim_customer.customer_key
- fa25_ssc_fact_return.return_key = fa25_ssc_dim_return.return_key
- fa25_ssc_fact_return.date_key = fa25_ssc_dim_date.date_key
- fa25_ssc_fact_return.order_key = fa25_ssc_fact_sales.sales_key (for cross-fact joins)

=== KEY STATISTICS ===

fa25_ssc_dim_date: Date range dependent (typically thousands of rows)
fa25_ssc_dim_customer: ~1000-10000 rows
fa25_ssc_dim_product: ~100-500 rows
fa25_ssc_dim_return: ~100-1000 rows
fa25_ssc_fact_sales: ~100000+ rows (transactional)
fa25_ssc_fact_return: ~1000-10000 rows (returns subset)

=== COMMON QUERIES ===

1. Sales by Region:
   SELECT region, SUM(sales) FROM fa25_ssc_fact_sales 
   JOIN fa25_ssc_dim_customer USING (customer_key) GROUP BY region

2. Product Performance:
   SELECT product_name, SUM(sales), SUM(profit), SUM(quantity)
   FROM fa25_ssc_fact_sales JOIN fa25_ssc_dim_product USING (product_key) GROUP BY product_name

3. Monthly Sales Trend:
   SELECT month, SUM(sales) FROM fa25_ssc_fact_sales
   JOIN fa25_ssc_dim_date USING (date_key) GROUP BY month ORDER BY month

4. Return Rate Analysis:
   SELECT category_name, 
   COUNT(DISTINCT CASE WHEN return_key IS NOT NULL THEN sales_key END) / COUNT(*) * 100
   FROM fa25_ssc_fact_sales JOIN fa25_ssc_dim_product USING (product_key) GROUP BY category_name

5. Regional Performance:
   SELECT region, SUM(sales), COUNT(*), AVG(profit) FROM fa25_ssc_fact_sales
   JOIN fa25_ssc_dim_customer USING (customer_key) GROUP BY region
"""


def get_vanna_training_data():
    """
    Get all training examples for Vanna.AI
    
    Returns:
        List of {question, sql} dictionaries
    """
    return VANNA_TRAINING_DATA


def get_business_rules():
    """
    Get business rules and schema context
    
    Returns:
        String with business rules documentation
    """
    return BUSINESS_RULES


def get_schema_documentation():
    """
    Get detailed schema documentation
    
    Returns:
        String with schema details
    """
    return SCHEMA_DOCUMENTATION




