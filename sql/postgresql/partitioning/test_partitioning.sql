-- TEST 1: Insert ORDER record into June 2012 partition
INSERT INTO FA25_SSC_ORDER_PARTITIONED (
    ROW_ID, ORDER_ID, ORDER_DATE, SHIP_DATE, SHIP_MODE, 
    CUSTOMER_ID, CUSTOMER_NAME, SEGMENT, POSTAL_CODE, CITY, 
    STATE, COUNTRY, REGION, MARKET, PRODUCT_ID, CATEGORY, 
    SUB_CATEGORY, PRODUCT_NAME, SALES, QUANTITY, DISCOUNT, 
    PROFIT, SHIPPING_COST, ORDER_PRIORITY
) VALUES (
    99999, 'TEST-2012-ABC', '2012-06-15', NOW(), 'Standard',
    'CUST-001', 'Test Customer', 'Consumer', '12345', 'New York',
    'NY', 'USA', 'East', 'Americas', 'PROD-001', 'Office',
    'Paper', 'Copy Paper', 100.00, 1, 0.0, 25.00, 5.00, 'High'
);

-- TEST 2: Insert RETURN record 
INSERT INTO FA25_SSC_RETURN_PARTITIONED (RETURNED, ORDER_ID, RETURN_DATE, REGION)
VALUES ('Yes', 'TEST-2012-ABC', '2012-06-15', 'East');

-- TEST 3: Verify order was inserted
SELECT 'ORDER record' as type, COUNT(*) as count 
FROM FA25_SSC_ORDER_PARTITIONED 
WHERE ORDER_ID = 'TEST-2012-ABC';

-- TEST 4: Verify return was inserted
SELECT 'RETURN record' as type, COUNT(*) as count 
FROM FA25_SSC_RETURN_PARTITIONED 
WHERE ORDER_ID = 'TEST-2012-ABC';

-- TEST 5: Verify ORDER went to correct partition (2012-06)
SELECT 'In P_2012_06?' as check_name, COUNT(*) as rows 
FROM FA25_SSC_ORDER_P_2012_06 
WHERE ORDER_ID = 'TEST-2012-ABC';

-- TEST 6: Verify RETURN went to correct partition (2012-06)
SELECT 'In P_2012_06?' as check_name, COUNT(*) as rows 
FROM FA25_SSC_RETURN_P_2012_06 
WHERE ORDER_ID = 'TEST-2012-ABC';

