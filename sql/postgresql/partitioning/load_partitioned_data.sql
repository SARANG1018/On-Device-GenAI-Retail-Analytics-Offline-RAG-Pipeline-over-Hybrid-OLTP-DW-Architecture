-- Load ORDER data into partitioned table
INSERT INTO FA25_SSC_ORDER_PARTITIONED
SELECT 
    ROW_ID, ORDER_ID, ORDER_DATE, 
    CURRENT_TIMESTAMP as SHIP_DATE,
    'Standard' as SHIP_MODE,
    CUSTOMER_ID,
    'Customer' as CUSTOMER_NAME,
    'Consumer' as SEGMENT,
    '12345' as POSTAL_CODE,
    'City' as CITY,
    'State' as STATE,
    'USA' as COUNTRY,
    'North America' as REGION,
    'Americas' as MARKET,
    'PRODUCT-001' as PRODUCT_ID,
    'Office Supplies' as CATEGORY,
    'Paper' as SUB_CATEGORY,
    'Product Name' as PRODUCT_NAME,
    100.00 as SALES,
    1 as QUANTITY,
    0.0 as DISCOUNT,
    25.00 as PROFIT,
    5.00 as SHIPPING_COST,
    'Medium' as ORDER_PRIORITY,
    CURRENT_TIMESTAMP
FROM "FA25_SSC_ORDER";

-- Load RETURN data into partitioned table (using actual order dates)
INSERT INTO FA25_SSC_RETURN_PARTITIONED (RETURNED, ORDER_ID, RETURN_DATE, REGION)
SELECT 
    r.return_status, 
    r.order_id,
    o.order_date as return_date,
    r.return_region
FROM "FA25_SSC_RETURN" r
JOIN "FA25_SSC_ORDER" o ON r.order_id = o.order_id;

-- Verify data loaded
SELECT 'FA25_SSC_ORDER_PARTITIONED' as table_name, COUNT(*) as rows FROM FA25_SSC_ORDER_PARTITIONED
UNION ALL
SELECT 'FA25_SSC_RETURN_PARTITIONED' as table_name, COUNT(*) as rows FROM FA25_SSC_RETURN_PARTITIONED;

-- Show data distribution by year
SELECT 'Orders' as type, EXTRACT(YEAR FROM ORDER_DATE)::INT as year, COUNT(*) as count FROM FA25_SSC_ORDER_PARTITIONED GROUP BY year
UNION ALL
SELECT 'Returns' as type, EXTRACT(YEAR FROM RETURN_DATE)::INT as year, COUNT(*) as count FROM FA25_SSC_RETURN_PARTITIONED GROUP BY year
ORDER BY type, year;

