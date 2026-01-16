# Complete End-to-End Workflow: Awesome Inc. Analytics System

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND (Port 8501)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐          ┌──────────────────┐             │
│  │  USER 1: Sales   │          │  USER 2: Store   │             │
│  │  Associate/      │          │  Manager         │             │
│  │  Customer        │          │  (Analytics)     │             │
│  │                  │          │                  │             │
│  │ • Order Entry    │          │ • AI Chat        │             │
│  │ • Product Entry  │          │ • Query Builder  │             │
│  │ • Return Entry   │          │ • Dashboards     │             │
│  └──────────────────┘          └──────────────────┘             │
│           │                              │                      │
└───────────┼──────────────────────────────┼──────────────────────┘
            │                              │
            │ INSERT Data                  │ SELECT Queries
            │                              │
    ┌───────▼──────────┐         ┌────────▼────────┐
    │   POSTGRESQL     │         │      MYSQL      │
    │   (OLTP)         │         │    (OLAP/DW)    │
    │ awesome_oltp     │         │  awesome_olap   │
    │                  │         │                 │
    │ ┌──────────────┐ │         │ ┌────────────┐  │
    │ │ TBL_ORDERS   │ │         │ │ DIM_DATE   │  │
    │ │ TBL_PRODUCTS │ │ ◄─ETL──►│ │ DIM_CUST   │  │
    │ │ TBL_CUSTOMER │ │         │ │ DIM_PROD   │  │
    │ │ TBL_RETURNS  │ │         │ │ FACT_SALES │  │
    │ │ ORDER_PRODUCT│ │         │ │ FACT_RETURN│  │
    │ └──────────────┘ │         │ └────────────┘  │
    └──────────────────┘         └─────────────────┘
         ▲                               ▲
         │                               │
         │ CDC Tracking                  │
         │ (TBL_LAST_DT)                 │
         │                               │
    ┌────┴───────────────────────────────┴──┐
    │    ETL Pipeline (Nightly)              │
    │    Extract → Transform → Load          │
    │    (CDC-based incremental)             │
    └────────────────────────────────────────┘
```

---

## **WORKFLOW SCENARIO: Complete Example**

### **Context**
- **Company**: Awesome Inc. Superstore
- **Scenario**: A sales associate records orders and returns. A store manager analyzes this data.
- **Timeline**: Day 1 (Monday) - Data entry, Day 2 (Tuesday) - ETL runs, Day 3 (Wednesday) - Analytics

---

## **PHASE 1: USER 1 - SALES ASSOCIATE DATA ENTRY (Day 1 - Monday)**

### **Step 1: Login to Streamlit App**

**Action**: Sales Associate (John) opens http://localhost:8501

```
┌─────────────────────────────────┐
│ Awesome Inc. Analytics System   │
├─────────────────────────────────┤
│                                 │
│ Username: john_sales            │
│ Password: ••••••••              │
│ Role:     [Sales Associate ▼]   │
│                                 │
│          [Login Button]          │
└─────────────────────────────────┘
```

**What happens**: 
- Streamlit authenticates user (role: "Sales Associate")
- Access to "Data Entry" page is granted
- Other pages (Chat Analytics, ETL Management) are hidden

---

### **Step 2: CREATE CUSTOMER & ORDER (Order Entry Tab)**

**Action**: John navigates to **Data Entry** → **Order Entry Tab**

**Form Fill - Example 1: New Customer**

```
┌─────────────────────────────────────────────────────────────┐
│ RECORD NEW ORDER                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Customer Name:    Alice Johnson                            │
│ Customer Email:   alice.johnson@company.com               │
│ Segment:          [Corporate ▼]                           │
│ Market:           US                                       │
│ Region:           [East ▼]                                │
│ Order Priority:   [High ▼]                                │
│ Order Date:       [12/05/2024]                            │
│                                                             │
│                    [Record Order]                          │
└─────────────────────────────────────────────────────────────┘
```

**Database Operations (PostgreSQL OLTP)**:

```sql
-- PostgreSQL Background: Check if customer exists
SELECT customer_id FROM TBL_CUSTOMERS WHERE customer_email = 'alice.johnson@company.com';
-- Result: NOT FOUND → Create new customer

-- Insert New Customer
INSERT INTO TBL_CUSTOMERS 
(customer_name, customer_email, segment_id, market, region, TBL_LAST_DT)
SELECT 'Alice Johnson', 'alice.johnson@company.com', s.segment_id, 'US', 'East', NOW()
FROM SEGMENT s WHERE s.segment_name = 'Corporate'
RETURNING customer_id;
-- Result: customer_id = 1001, TBL_LAST_DT = '2024-12-05 09:00:00'

-- Insert Order
INSERT INTO TBL_ORDERS 
(customer_id, order_date, order_priority, TBL_LAST_DT)
VALUES (1001, '2024-12-05', 'High', NOW())
RETURNING order_id;
-- Result: order_id = ORD-001, TBL_LAST_DT = '2024-12-05 09:05:00'
```

**Result**: ✅ Order recorded successfully!
```
Order ID: ORD-001
Customer: Alice Johnson
Date: 2024-12-05
```

---

### **Step 3: ADD PRODUCTS TO ORDER (Product Entry Tab)**

**Action**: John clicks **Product Entry Tab** to add items to the order

**Form Fill - Example 1: Laptop**

```
┌──────────────────────────────────────────────────────────┐
│ ADD PRODUCT TO ORDER                                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Order ID:           ORD-001                             │
│ Product Name:       MacBook Pro 14"                     │
│ Category:           [Technology ▼]                      │
│ Quantity:           2                                   │
│ Sales Amount:       $4,800.00                           │
│ Discount (%):       ░░░░░░░░░░ 5%                       │
│ Subcategory:        Laptops                             │
│ Shipping Cost:      $150.00                             │
│ Ship Mode:          [First Class ▼]                     │
│ Ship Date:          [12-07-2024]                        │
│                                                          │
│              [Add Product to Order]                      │
└──────────────────────────────────────────────────────────┘
```

**Database Operations (PostgreSQL OLTP)**:

```sql
-- Check if order exists
SELECT order_id FROM TBL_ORDERS WHERE order_id = 'ORD-001';
-- Result: FOUND

-- Check if product exists
SELECT product_id FROM TBL_PRODUCTS WHERE product_name = 'MacBook Pro 14"';
-- Result: NOT FOUND → Create new product

-- Insert New Product
INSERT INTO TBL_PRODUCTS 
(product_name, category_id, subcategory_id, TBL_LAST_DT)
SELECT 'MacBook Pro 14"', c.category_id, sc.subcategory_id, NOW()
FROM CATEGORY c, SUBCATEGORY sc 
WHERE c.category_name = 'Technology' AND sc.subcategory_name = 'Laptops'
RETURNING product_id;
-- Result: product_id = PROD-501

-- Calculate profit (for business logic)
Profit = Sales - (Discount × Sales) - Shipping_Cost
       = 4800 - (0.05 × 4800) - 150
       = 4800 - 240 - 150
       = 4410

-- Insert into ORDER_PRODUCT junction table
INSERT INTO ORDER_PRODUCT 
(order_id, product_id, quantity, sales, discount, profit, 
 shipping_cost, ship_mode, ship_date, TBL_LAST_DT)
VALUES ('ORD-001', 'PROD-501', 2, 4800.00, 240.00, 4410.00, 
        150.00, 'First Class', '2024-12-07', NOW());
-- TBL_LAST_DT = '2024-12-05 09:15:00'
```

**Result**: ✅ Product added to order!
```
Order: ORD-001 | Product: MacBook Pro 14" | Qty: 2 | Amount: $4,800
```

**Form Fill - Example 2: Office Chair**

```
Order ID:           ORD-001
Product Name:       Ergonomic Office Chair
Category:           [Furniture ▼]
Quantity:           4
Sales Amount:       $1,200.00
Discount (%):       ░░░░░░░░░░ 10%
Subcategory:        Chairs
Shipping Cost:      $80.00
Ship Mode:          [Standard Class ▼]
Ship Date:          [12-07-2024]
```

**Database Result**:
```sql
-- Product profit calculation
Profit = 1200 - (0.10 × 1200) - 80
       = 1200 - 120 - 80
       = 1000

-- INSERT ORDER_PRODUCT row
(order_id='ORD-001', product_id='PROD-502', quantity=4, sales=1200.00, 
 discount=120.00, profit=1000.00, shipping_cost=80.00, TBL_LAST_DT='2024-12-05 09:20:00')
```

---

### **Step 4: RECORD RETURN (Return Entry Tab)**

**Action**: Customer Alice wants to return 1 of the 4 office chairs (defective)

**Form Fill**:

```
┌────────────────────────────────────────────────────────┐
│ RECORD RETURN                                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ Order ID / Sale ID:   ORD-001                         │
│ Return Reason:        [Defective ▼]                   │
│ Return Status:        [Pending ▼]                     │
│ Return Region:        [East ▼]                        │
│ Return Date:          [12-06-2024]                    │
│                                                        │
│              [Record Return]                          │
└────────────────────────────────────────────────────────┘
```

**Database Operations**:

```sql
-- Check if order exists
SELECT order_id FROM TBL_ORDERS WHERE order_id = 'ORD-001';
-- Result: FOUND

-- Insert Return
INSERT INTO TBL_RETURNS 
(order_id, return_reason, return_status, return_region, return_date, TBL_LAST_DT)
VALUES ('ORD-001', 'Defective', 'Pending', 'East', '2024-12-06', NOW())
RETURNING return_id;
-- Result: return_id = RET-001, TBL_LAST_DT = '2024-12-05 10:00:00'
```

**Result**: ✅ Return recorded!
```
Return ID: RET-001
Order ID: ORD-001
Reason: Defective
Status: Pending
```

---

### **State of OLTP Database (End of Day 1 - Monday)**

#### **TBL_CUSTOMERS** (PostgreSQL)
```
customer_id | customer_name  | customer_email            | segment_id | market | region | TBL_LAST_DT
1001        | Alice Johnson  | alice.johnson@company.com | 2          | US     | East   | 2024-12-05 09:00:00
```

#### **TBL_ORDERS**
```
order_id | customer_id | order_date | order_priority | TBL_LAST_DT
ORD-001  | 1001        | 2024-12-05 | High           | 2024-12-05 09:05:00
```

#### **TBL_PRODUCTS**
```
product_id | product_name           | category_id | subcategory_id | TBL_LAST_DT
PROD-501   | MacBook Pro 14"        | 1           | 3              | 2024-12-05 09:15:00
PROD-502   | Ergonomic Office Chair | 2           | 5              | 2024-12-05 09:20:00
```

#### **ORDER_PRODUCT** (Junction table)
```
order_id | product_id | quantity | sales    | discount | profit   | shipping_cost | ship_mode      | ship_date  | TBL_LAST_DT
ORD-001  | PROD-501   | 2        | 4800.00  | 240.00   | 4410.00  | 150.00        | First Class    | 2024-12-07 | 2024-12-05 09:15:00
ORD-001  | PROD-502   | 4        | 1200.00  | 120.00   | 1000.00  | 80.00         | Standard Class | 2024-12-07 | 2024-12-05 09:20:00
```

#### **TBL_RETURNS**
```
return_id | order_id | return_reason | return_status | return_region | return_date | TBL_LAST_DT
RET-001   | ORD-001  | Defective     | Pending       | East          | 2024-12-06  | 2024-12-05 10:00:00
```

---

## **PHASE 2: ETL PIPELINE EXECUTION (Day 2 - Tuesday, Nightly at 2 AM)**

**Trigger**: Automated nightly ETL job (or manual "Run ETL Now" button)

### **Step 1: EXTRACT Phase - CDC-Based Incremental Load**

**What happens**: ETL gets the last successful run timestamp from ETL_LOG

```
Last successful ETL: 2024-12-04 02:00:00 (Previous day)
```

**Extract Query - ORDERS**:
```sql
SELECT * FROM TBL_ORDERS 
WHERE TBL_LAST_DT > '2024-12-04 02:00:00'
ORDER BY TBL_LAST_DT;

-- Result: 1 row
-- ORD-001 (TBL_LAST_DT = 2024-12-05 09:05:00) ✅ CHANGED
```

**Extract Query - PRODUCTS** (Full load, always):
```sql
SELECT * FROM TBL_PRODUCTS;

-- Result: 2 rows (including master data)
-- PROD-501, PROD-502 ✅
```

**Extract Query - ORDER_PRODUCT**:
```sql
SELECT * FROM ORDER_PRODUCT 
WHERE TBL_LAST_DT > '2024-12-04 02:00:00'
ORDER BY TBL_LAST_DT;

-- Result: 2 rows
-- ORD-001 + PROD-501
-- ORD-001 + PROD-502 ✅ BOTH CHANGED
```

**Extract Query - RETURNS**:
```sql
SELECT * FROM TBL_RETURNS 
WHERE TBL_LAST_DT > '2024-12-04 02:00:00'
ORDER BY TBL_LAST_DT;

-- Result: 1 row
-- RET-001 (TBL_LAST_DT = 2024-12-05 10:00:00) ✅ CHANGED
```

**Extract Summary**:
- ✅ 1 changed order
- ✅ 2 changed order-product links
- ✅ 1 changed return
- ✅ 2 products (full load)
- ✅ 1 customer (full load)

---

### **Step 2: TRANSFORM Phase - Denormalize to OLAP Star Schema**

**Input**: CDC-extracted data from OLTP

**Transform Logic**:

#### **CREATE DIM_DATE**
```python
# Generate from order dates + ship dates
all_dates = [
    '2024-12-05' (order_date),
    '2024-12-07' (ship_date for both products)
]

for each date:
    date_key = 20241205 (YYYYMMDD format)
    year = 2024
    quarter = 4
    month = 12
    month_name = "December"
    week = 49
    day_of_week = "Monday"
```

**Result**:
```
date_key | date       | year | quarter | month | month_name | week | day_of_week
20241205 | 2024-12-05 | 2024 | 4       | 12    | December   | 49   | Monday
20241207 | 2024-12-07 | 2024 | 4       | 12    | December   | 49   | Wednesday
```

#### **CREATE DIM_CUSTOMER**
```python
# Source: TBL_CUSTOMERS
# Add: surrogate key, segment name

customer_key = 1 (sequential)
customer_id = 'alice.johnson@company.com' (from OLTP)
customer_name = 'Alice Johnson'
region = 'East'
segment_name = 'Corporate' (from SEGMENT table)
market = 'US'
```

**Result**:
```
customer_key | customer_id | customer_name | region | segment_name | market
1            | 1001        | Alice Johnson | East   | Corporate    | US
```

#### **CREATE DIM_PRODUCT**
```python
# Source: TBL_PRODUCTS + CATEGORY + SUBCATEGORY
# Add: surrogate key, category/subcategory names

Product 1:
  product_key = 1
  product_id = 'PROD-501'
  product_name = 'MacBook Pro 14"'
  category_name = 'Technology'
  subcategory_name = 'Laptops'

Product 2:
  product_key = 2
  product_id = 'PROD-502'
  product_name = 'Ergonomic Office Chair'
  category_name = 'Furniture'
  subcategory_name = 'Chairs'
```

**Result**:
```
product_key | product_id | product_name           | category_name | subcategory_name
1           | PROD-501   | MacBook Pro 14"        | Technology    | Laptops
2           | PROD-502   | Ergonomic Office Chair | Furniture     | Chairs
```

#### **CREATE DIM_RETURN**
```python
# Source: TBL_RETURNS
# Add: surrogate key

return_key = 1
return_id = 'RET-001'
return_status = 'Pending'
return_region = 'East'
```

**Result**:
```
return_key | return_id | return_status | return_region
1          | RET-001   | Pending       | East
```

#### **CREATE FACT_SALES**
```python
# Source: ORDER_PRODUCT joined with TBL_ORDERS
# Map: product_id → product_key, customer_id → customer_key, order_date → date_key

Row 1:
  order_id = 'ORD-001'
  product_id = 'PROD-501'
  customer_key = 1 (mapped from customer_id=1001)
  product_key = 1 (mapped from product_id='PROD-501')
  date_key = 20241207 (from ship_date)
  quantity = 2
  sales = 4800.00
  discount = 240.00
  profit = 4410.00
  shipping_cost = 150.00
  order_priority = 'High'

Row 2:
  order_id = 'ORD-001'
  product_id = 'PROD-502'
  customer_key = 1
  product_key = 2
  date_key = 20241207
  quantity = 4
  sales = 1200.00
  discount = 120.00
  profit = 1000.00
  shipping_cost = 80.00
  order_priority = 'High'
```

**Result**:
```
order_id | product_id | customer_key | product_key | date_key | quantity | sales   | discount | profit  | shipping_cost | order_priority
ORD-001  | PROD-501   | 1            | 1           | 20241207 | 2        | 4800.00 | 240.00   | 4410.00 | 150.00        | High
ORD-001  | PROD-502   | 1            | 2           | 20241207 | 4        | 1200.00 | 120.00   | 1000.00 | 80.00         | High
```

#### **CREATE FACT_RETURN**
```python
# Source: TBL_RETURNS joined with TBL_ORDERS + FACT_SALES
# Map: customer_id → customer_key, order_date → date_key, return → return_key

return_id = 'RET-001'
order_id = 'ORD-001'
customer_key = 1 (mapped)
return_key = 1 (mapped)
date_key = 20241205 (from order_date of ORD-001)
return_status = 'Pending'
```

**Result**:
```
return_id | order_id | customer_key | return_key | date_key | return_status
RET-001   | ORD-001  | 1            | 1          | 20241205 | Pending
```

---

### **Step 3: LOAD Phase - Insert into MySQL DW**

**Connection**: MySQL awesome_olap (localhost:3306)

**Loading Order** (Important - Dimensions first!):

1️⃣ **Load DIM_DATE** (first - referenced by facts)
```sql
INSERT INTO DIM_DATE 
(date_key, date, year, quarter, month, month_name, week, day_of_week)
VALUES 
(20241205, '2024-12-05', 2024, 4, 12, 'December', 49, 'Monday'),
(20241207, '2024-12-07', 2024, 4, 12, 'December', 49, 'Wednesday');
-- ✅ 2 rows inserted
```

2️⃣ **Load DIM_CUSTOMER**
```sql
INSERT INTO DIM_CUSTOMER 
(customer_key, customer_id, customer_name, region, segment_name, market)
VALUES 
(1, '1001', 'Alice Johnson', 'East', 'Corporate', 'US');
-- ✅ 1 row inserted
```

3️⃣ **Load DIM_PRODUCT**
```sql
INSERT INTO DIM_PRODUCT 
(product_key, product_id, product_name, category_name, subcategory_name)
VALUES 
(1, 'PROD-501', 'MacBook Pro 14"', 'Technology', 'Laptops'),
(2, 'PROD-502', 'Ergonomic Office Chair', 'Furniture', 'Chairs');
-- ✅ 2 rows inserted
```

4️⃣ **Load DIM_RETURN**
```sql
INSERT INTO DIM_RETURN 
(return_key, return_id, return_status, return_region)
VALUES 
(1, 'RET-001', 'Pending', 'East');
-- ✅ 1 row inserted
```

5️⃣ **Load FACT_SALES**
```sql
INSERT INTO FACT_SALES 
(order_id, product_id, customer_key, product_key, date_key, 
 quantity, sales, discount, profit, shipping_cost, order_priority)
VALUES 
('ORD-001', 'PROD-501', 1, 1, 20241207, 2, 4800.00, 240.00, 4410.00, 150.00, 'High'),
('ORD-001', 'PROD-502', 1, 2, 20241207, 4, 1200.00, 120.00, 1000.00, 80.00, 'High');
-- ✅ 2 rows inserted
```

6️⃣ **Load FACT_RETURN**
```sql
INSERT INTO FACT_RETURN 
(return_id, order_id, customer_key, return_key, date_key, return_status)
VALUES 
('RET-001', 'ORD-001', 1, 1, 20241205, 'Pending');
-- ✅ 1 row inserted
```

---

### **Step 4: Log ETL Run**

```sql
-- Insert into ETL_LOG (MySQL)
INSERT INTO ETL_LOG 
(etl_run_time, status, records_processed)
VALUES 
('2024-12-06 02:00:00', 'SUCCESS', 2);
-- Next ETL will use 2024-12-06 02:00:00 as the cutoff for CDC
```

**ETL Summary**:
```
✅ EXTRACT: 4 changed OLTP records (1 order, 2 order-products, 1 return)
✅ TRANSFORM: 6 OLAP tables created
✅ LOAD: 6 tables loaded into MySQL (2 DIM_DATE + 1 DIM_CUST + 1 DIM_PROD + 1 DIM_RET + 2 FACT_SALES + 1 FACT_RETURN)
✅ Total records processed: 2
✅ Duration: 45 seconds
```

---

## **PHASE 3: USER 2 - STORE MANAGER ANALYTICS (Day 3 - Wednesday)**

### **Step 1: Login as Store Manager**

**Action**: Store Manager (Sarah) opens http://localhost:8501

```
Username: sarah_manager
Password: ••••••••
Role:     [Store Manager ▼]
```

**Result**: Access to:
- ✅ Dashboard
- ✅ Chat Analytics
- ✅ ETL Management
- ❌ Data Entry (not authorized)

---

### **Step 2: View Dashboard**

**Page**: Dashboard

```
┌────────────────────────────────────────────────────────────┐
│ DASHBOARD                                                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Total Sales        Return Rate        Top Product  Regions │
│  $6,000.00          1.2%               MacBook Pro  4       │
│  +15% vs yesterday   -0.3% vs yesterday $4,800              │
│                                                            │
│ [Chart showing daily sales trends]                        │
│ [Chart showing product category breakdown]                │
│ [Chart showing customer segment distribution]             │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

### **Step 3: Chat Interface - Multi-Turn Conversation**

**Page**: Chat Analytics (AI-Powered Natural Language Q&A)

#### **Query 1: Basic Sales Analysis**

**Sarah asks**: "What's the total sales by product category?"

```
┌────────────────────────────────────────────────────────────┐
│ AI ANALYTICS CHAT                                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ You: What's the total sales by product category?          │
│                                                            │
│ AI:  📊 Analysis                                           │
│      Based on the latest data:                            │
│                                                            │
│      • Technology: $4,800.00 (2 units)                    │
│      • Furniture: $1,200.00 (4 units)                     │
│                                                            │
│      Total Revenue: $6,000.00                             │
│      Technology is leading with 80% of sales.             │
│                                                            │
│ [📥 Data Details (Advanced)]  [Download as CSV]           │
│                                                            │
│ ───────────────────────────────────────────────────────── │
│                                                            │
│ Your Question: _____________________________             │
│                              [Send]  [Clear]              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Behind the Scenes - RAG Pipeline**:

```
1. User Input: "What's the total sales by product category?"
   ↓
2. Vanna.AI Embedding Search:
   Find similar Q&A pairs from training data
   → Match: "Show me sales by product category" (High similarity score)
   ↓
3. Generate SQL (Vanna):
   SELECT 
       dp.category_name,
       SUM(fs.sales) as total_sales,
       SUM(fs.quantity) as total_units,
       COUNT(*) as transaction_count
   FROM FACT_SALES fs
   JOIN DIM_PRODUCT dp ON fs.product_key = dp.product_key
   GROUP BY dp.category_name
   ORDER BY total_sales DESC;
   ↓
4. Execute on MySQL DW:
   category_name  | total_sales | total_units | transaction_count
   Technology     | 4800.00     | 2           | 1
   Furniture      | 1200.00     | 4           | 1
   ↓
5. Gemini LLM Analysis:
   Summarize results in natural language
   Add business insights
   ↓
6. Return to User:
   "Based on the latest data:
    • Technology: $4,800.00 (2 units)
    • Furniture: $1,200.00 (4 units)
    Total Revenue: $6,000.00
    Technology is leading with 80% of sales."
```

---

#### **Query 2: Drill-down - What products in Technology?"**

**Sarah follows up**: "What products are in the Technology category? Show me details."

```
You: What products are in Technology? Show me the details.

AI:  📊 Analysis
     Technology products and their performance:
     
     • MacBook Pro 14"
       Revenue: $4,800.00
       Units Sold: 2
       Profit Margin: 91.9%
       Priority: High
     
     Technology category represents our best-performing segment
     with highest profit margins (91.9% vs 83.3% for furniture).
```

**Generated SQL**:
```sql
SELECT 
    dp.product_name,
    SUM(fs.sales) as revenue,
    SUM(fs.quantity) as units_sold,
    SUM(fs.profit) as total_profit,
    ROUND(SUM(fs.profit) / SUM(fs.sales) * 100, 1) as profit_margin_pct,
    MAX(fs.order_priority) as order_priority
FROM FACT_SALES fs
JOIN DIM_PRODUCT dp ON fs.product_key = dp.product_key
WHERE dp.category_name = 'Technology'
GROUP BY dp.product_name
ORDER BY revenue DESC;

-- Result:
product_name      | revenue  | units_sold | total_profit | profit_margin_pct | order_priority
MacBook Pro 14"   | 4800.00  | 2          | 4410.00      | 91.9              | High
```

---

#### **Query 3: Return Analysis**

**Sarah asks**: "What products are being returned and why?"

```
You: What products are being returned and why?

AI:  ⚠️ Analysis
     Return Status Summary:
     
     • 1 return recorded (Pending)
     • Return Rate: 16.7% of orders
     • Product: Ergonomic Office Chair (Furniture)
     • Reason: Defective
     • Region: East
     
     The office chair return needs immediate attention. 
     This could indicate quality issues in the Furniture category.
     Recommend investigating supplier quality standards.
```

**Generated SQL**:
```sql
SELECT 
    dp.product_name,
    dp.category_name,
    dr.return_status,
    COUNT(fr.return_id) as return_count,
    SUM(fs.sales) as returned_sales_value
FROM FACT_RETURN fr
JOIN FACT_SALES fs ON fr.order_id = fs.order_id
JOIN DIM_PRODUCT dp ON fs.product_key = dp.product_key
JOIN DIM_RETURN dr ON fr.return_key = dr.return_key
GROUP BY dp.product_name, dp.category_name, dr.return_status
ORDER BY return_count DESC;

-- Result:
product_name           | category_name | return_status | return_count | returned_sales_value
Ergonomic Office Chair | Furniture     | Pending       | 1            | 1200.00
```

---

#### **Query 4: Regional & Customer Segment Analysis**

**Sarah asks**: "Break down sales by customer segment and region"

```
You: Show me sales breakdown by customer segment and region

AI:  📊 Analysis
     Sales by Customer Segment & Region:
     
     Corporate - East:
     • Revenue: $6,000.00
     • Units Sold: 6
     • Profit: $5,410.00
     • Profit Margin: 90.2%
     
     The Corporate segment in the East region is performing well.
     100% of current sales are from this segment-region combination.
```

**Generated SQL**:
```sql
SELECT 
    dc.segment_name,
    dc.region,
    COUNT(DISTINCT fs.customer_key) as unique_customers,
    COUNT(*) as transaction_count,
    SUM(fs.sales) as total_sales,
    SUM(fs.profit) as total_profit,
    ROUND(SUM(fs.profit) / SUM(fs.sales) * 100, 1) as profit_margin_pct
FROM FACT_SALES fs
JOIN DIM_CUSTOMER dc ON fs.customer_key = dc.customer_key
GROUP BY dc.segment_name, dc.region
ORDER BY total_sales DESC;

-- Result:
segment_name | region | unique_customers | transaction_count | total_sales | total_profit | profit_margin_pct
Corporate    | East   | 1                | 2                 | 6000.00     | 5410.00      | 90.2
```

---

#### **Query 5: Time-Series Analysis**

**Sarah asks**: "Show me sales trends over the past week"

```
You: What are the sales trends this week?

AI:  📈 Trend Analysis
     Daily Sales Performance:
     
     Monday (12/05):    $0.00 (Data entry day)
     Tuesday (12/06):   $0.00 (ETL processing)
     Wednesday (12/07): $6,000.00 ✅ (Ship date)
     
     All orders were shipped on Wednesday (12/07).
     Single spike due to consolidation of orders from Monday.
     Peak represents efficient fulfillment.
```

**Generated SQL**:
```sql
SELECT 
    dd.date,
    dd.day_of_week,
    COUNT(*) as transaction_count,
    SUM(fs.sales) as daily_sales,
    SUM(fs.profit) as daily_profit
FROM FACT_SALES fs
JOIN DIM_DATE dd ON fs.date_key = dd.date_key
WHERE dd.date >= '2024-12-02'
GROUP BY dd.date, dd.day_of_week
ORDER BY dd.date DESC;

-- Result:
date       | day_of_week | transaction_count | daily_sales | daily_profit
2024-12-07 | Wednesday   | 2                 | 6000.00     | 5410.00
```

---

### **Step 4: ETL Management Page**

**Action**: Sarah clicks **ETL Management**

```
┌────────────────────────────────────────────────────────────┐
│ ETL PIPELINE MANAGEMENT                                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Overview                                                   │
│ ─────────────────────────────────────────────────────────  │
│ Pipeline Status:       Ready                 ✅            │
│ Successful Runs:       1                                  │
│ Last Run:              2024-12-06 02:00:00                │
│                                                            │
│ How ETL works:                                            │
│ 1. EXTRACT: Reads changed records from PostgreSQL OLTP   │
│    (Uses CDC via TBL_LAST_DT for efficiency)             │
│ 2. TRANSFORM: Denormalizes data to star schema            │
│ 3. LOAD: Inserts into MySQL Data Warehouse                │
│                                                            │
│ [Run ETL Now Button]                                      │
│                                                            │
│ ETL Run History                                            │
│ ─────────────────────────────────────────────────────────  │
│                                                            │
│ Run ID | Timestamp           | Status  | Records Processed │
│ 1      | 2024-12-06 02:00:00 | SUCCESS | 2                 │
│                                                            │
│ CDC Status: Last incremental load from 2024-12-06 02:00  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## **COMPLETE DATA FLOW SUMMARY**

### **Timeline View**

```
Day 1 - MONDAY 12/05/2024 (Data Entry Phase)
────────────────────────────────────────────
09:00 │ John (Sales Associate) logs in
09:05 │ Creates Order ORD-001 for Alice Johnson (Corporate, East)
      │ TBL_LAST_DT = 09:05:00
      │
09:15 │ Adds Product 1: MacBook Pro (2 units, $4,800)
      │ TBL_LAST_DT = 09:15:00
      │
09:20 │ Adds Product 2: Office Chair (4 units, $1,200)
      │ TBL_LAST_DT = 09:20:00
      │
10:00 │ Records Return RET-001 (Office Chair - Defective)
      │ TBL_LAST_DT = 10:00:00
      │
      │ OLTP PostgreSQL State:
      │ - 1 Customer (Alice Johnson)
      │ - 1 Order (ORD-001)
      │ - 2 Products (MacBook, Chair)
      │ - 2 Order-Product records
      │ - 1 Return (Pending)


Day 2 - TUESDAY 12/06/2024 (ETL Processing)
────────────────────────────────────────────
02:00 │ ETL Pipeline starts (nightly job)
      │
02:05 │ EXTRACT Phase:
      │ - CDC Query: Get all records where TBL_LAST_DT > 2024-12-04 02:00:00
      │ - Changed records: 1 order + 2 order-products + 1 return + master data
      │
02:20 │ TRANSFORM Phase:
      │ - Create DIM_DATE (2 rows)
      │ - Create DIM_CUSTOMER (1 row with surrogate key)
      │ - Create DIM_PRODUCT (2 rows with surrogate keys)
      │ - Create DIM_RETURN (1 row with surrogate key)
      │ - Create FACT_SALES (2 rows with foreign keys)
      │ - Create FACT_RETURN (1 row with foreign keys)
      │
02:40 │ LOAD Phase:
      │ - Insert all 6 OLAP tables into MySQL DW
      │ - Log ETL run: status=SUCCESS, records=2
      │
      │ OLAP MySQL State:
      │ - DIM_DATE: 2 rows
      │ - DIM_CUSTOMER: 1 row
      │ - DIM_PRODUCT: 2 rows
      │ - DIM_RETURN: 1 row
      │ - FACT_SALES: 2 rows
      │ - FACT_RETURN: 1 row


Day 3 - WEDNESDAY 12/07/2024 (Analytics Phase)
───────────────────────────────────────────────
08:00 │ Sarah (Store Manager) logs in
      │
08:05 │ Views Dashboard
      │ - Total Sales: $6,000
      │ - Top Product: MacBook Pro
      │ - Return Rate: 1 return
      │
08:15 │ Asks: "Total sales by category?"
      │ - Vanna finds similar training question
      │ - Generates: SELECT dp.category_name, SUM(fs.sales)...
      │ - Results: Technology=$4,800, Furniture=$1,200
      │ - Gemini LLM: "Technology is 80% of sales"
      │
08:25 │ Asks: "Which products have returns?"
      │ - Generated SQL joins FACT_RETURN + FACT_SALES + DIM_PRODUCT
      │ - Results: Office Chair - Defective (Pending)
      │ - Insight: "Quality issue detected, recommend supplier review"
      │
08:35 │ Checks ETL Status
      │ - Last run: 2024-12-06 02:00:00 (SUCCESS)
      │ - Records processed: 2
      │ - Next run: 2024-12-07 02:00:00
```

---

## **KEY TAKEAWAYS**

### **User 1 Workflow (Sales Associate - John)**
1. ✅ Log in → Data Entry page
2. ✅ Create Order (with automatic customer creation)
3. ✅ Add Products (with automatic product creation)
4. ✅ Record Returns (linking to orders)
5. ✅ Data stored in PostgreSQL OLTP with TBL_LAST_DT timestamps

### **Automated ETL Pipeline (System)**
1. ✅ CDC Extraction: Only fetch changed records (WHERE TBL_LAST_DT > last_run)
2. ✅ Transform: Denormalize to star schema with surrogate keys
3. ✅ Load: Insert into 6 OLAP tables (dimensions first, then facts)
4. ✅ Log: Store run metadata for next incremental load

### **User 2 Workflow (Store Manager - Sarah)**
1. ✅ Log in → Dashboard
2. ✅ Ask natural language questions via Chat
3. ✅ Vanna finds similar training examples
4. ✅ Generate SQL automatically
5. ✅ Execute on MySQL DW (already aggregated data)
6. ✅ Gemini LLM provides insights
7. ✅ Monitor ETL runs and pipeline health

---

## **Why This Architecture Works**

| Aspect | OLTP (PostgreSQL) | OLAP (MySQL) | ETL Pipeline |
|--------|-------------------|--------------|--------------|
| **Purpose** | Transactional | Analytical | Bridge |
| **Data** | Normalized | Denormalized (Star) | Transformation |
| **User** | Sales Associate (INSERT) | Store Manager (SELECT) | Automated |
| **Query** | Fast writes | Fast aggregations | CDC-based incremental |
| **Volume** | Real-time updates | Nightly refresh | Efficient batch |
| **AI Integration** | ❌ | ✅ Vanna + Gemini | Data pipeline |

