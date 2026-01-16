
-- PROCEDURE 1: Validate Customer (for Order Entry)
-- Returns: is_valid, customer_name, segment_name
CREATE OR REPLACE FUNCTION validate_customer(
    p_customer_id VARCHAR
)
RETURNS TABLE (
    is_valid BOOLEAN,
    customer_name VARCHAR,
    segment_name VARCHAR,
    error_message VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE WHEN c.customer_id IS NOT NULL THEN true ELSE false END,
        COALESCE(c.customer_name, 'N/A')::VARCHAR,
        COALESCE(s.segment_name, 'N/A')::VARCHAR,
        CASE 
            WHEN c.customer_id IS NULL THEN 'Customer not found'
            ELSE 'Valid'
        END::VARCHAR
    FROM (SELECT p_customer_id) AS dummy(id)
    LEFT JOIN "FA25_SSC_CUSTOMER" c ON c.customer_id = dummy.id
    LEFT JOIN "FA25_SSC_SEGMENT" s ON c.segment_id = s.segment_id;
END;
$$ LANGUAGE plpgsql;


-- PROCEDURE 2: Validate Order Exists (for Product Entry & Return Entry)
-- Returns: is_valid, customer_id, customer_name, product_count

CREATE OR REPLACE FUNCTION validate_order(
    p_order_id VARCHAR
)
RETURNS TABLE (
    is_valid BOOLEAN,
    customer_id VARCHAR,
    customer_name VARCHAR,
    product_count INTEGER,
    error_message VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE WHEN o.order_id IS NOT NULL THEN true ELSE false END,
        COALESCE(o.customer_id, 'N/A')::VARCHAR,
        COALESCE(c.customer_name, 'N/A')::VARCHAR,
        COALESCE((SELECT COUNT(*)::INTEGER FROM "FA25_SSC_ORDER_PRODUCT" WHERE order_id = p_order_id), 0),
        CASE 
            WHEN o.order_id IS NULL THEN 'Order not found'
            WHEN o.customer_id IS NULL THEN 'Customer reference missing'
            ELSE 'Valid'
        END::VARCHAR
    FROM (SELECT p_order_id) AS dummy(id)
    LEFT JOIN "FA25_SSC_ORDER" o ON o.order_id = dummy.id
    LEFT JOIN "FA25_SSC_CUSTOMER" c ON o.customer_id = c.customer_id;
END;
$$ LANGUAGE plpgsql;


-- PROCEDURE 3: Validate Product (for Product Entry)
-- Returns: is_valid, product_name, category, subcategory

CREATE OR REPLACE FUNCTION validate_product(
    p_product_id VARCHAR
)
RETURNS TABLE (
    is_valid BOOLEAN,
    product_name VARCHAR,
    category_name VARCHAR,
    subcategory_name VARCHAR,
    error_message VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE WHEN p.product_id IS NOT NULL THEN true ELSE false END,
        COALESCE(p.product_name, 'N/A')::VARCHAR,
        COALESCE(c.category_name, 'N/A')::VARCHAR,
        COALESCE(sc.subcategory_name, 'N/A')::VARCHAR,
        CASE 
            WHEN p.product_id IS NULL THEN 'Product not found'
            ELSE 'Valid'
        END::VARCHAR
    FROM (SELECT p_product_id) AS dummy(id)
    LEFT JOIN "FA25_SSC_PRODUCT" p ON p.product_id = dummy.id
    LEFT JOIN "FA25_SSC_SUBCATEGORY" sc ON p.subcategory_id = sc.subcategory_id
    LEFT JOIN "FA25_SSC_CATEGORY" c ON sc.category_id = c.category_id;
END;
$$ LANGUAGE plpgsql;


-- PROCEDURE 4: Validate Return Data (for Return Entry - Future)
-- Returns: is_valid, order_id, return_status, return_region

CREATE OR REPLACE FUNCTION validate_return(
    p_return_id VARCHAR
)
RETURNS TABLE (
    is_valid BOOLEAN,
    order_id VARCHAR,
    return_status VARCHAR,
    return_region VARCHAR,
    error_message VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE WHEN r.return_id IS NOT NULL THEN true ELSE false END,
        COALESCE(r.order_id, 'N/A')::VARCHAR,
        COALESCE(r.return_status, 'N/A')::VARCHAR,
        COALESCE(r.return_region, 'N/A')::VARCHAR,
        CASE 
            WHEN r.return_id IS NULL THEN 'Return not found'
            WHEN r.order_id IS NULL THEN 'Order reference missing'
            WHEN (SELECT COUNT(*) FROM "FA25_SSC_ORDER" WHERE order_id = r.order_id) = 0 THEN 'Referenced order not found'
            ELSE 'Valid'
        END::VARCHAR
    FROM (SELECT p_return_id) AS dummy(id)
    LEFT JOIN "FA25_SSC_RETURN" r ON r.return_id = dummy.id;
END;
$$ LANGUAGE plpgsql;


-- PROCEDURE 5: Check Data Integrity (Future - Data Quality)
-- Returns: table_name, check_type, issue_count, details

CREATE OR REPLACE FUNCTION check_data_integrity()
RETURNS TABLE (
    table_name VARCHAR,
    check_type VARCHAR,
    issue_count INTEGER,
    details TEXT
) AS $$
BEGIN
    -- Check for orphaned ORDER_PRODUCT records
    RETURN QUERY
    SELECT 
        'FA25_SSC_ORDER_PRODUCT'::VARCHAR,
        'Orphaned Records'::VARCHAR,
        COUNT(*)::INTEGER,
        CONCAT('FA25_SSC_ORDER_PRODUCT records with non-existent order_id: ', STRING_AGG(DISTINCT op.order_id, ', '))::TEXT
    FROM "FA25_SSC_ORDER_PRODUCT" op
    LEFT JOIN "FA25_SSC_ORDER" o ON op.order_id = o.order_id
    WHERE o.order_id IS NULL;

    -- Check for orphaned RETURN records
    RETURN QUERY
    SELECT 
        'FA25_SSC_RETURN'::VARCHAR,
        'Orphaned Records'::VARCHAR,
        COUNT(*)::INTEGER,
        CONCAT('FA25_SSC_RETURN records with non-existent order_id: ', STRING_AGG(DISTINCT r.order_id, ', '))::TEXT
    FROM "FA25_SSC_RETURN" r
    LEFT JOIN "FA25_SSC_ORDER" o ON r.order_id = o.order_id
    WHERE o.order_id IS NULL;

    -- Check for missing customer records
    RETURN QUERY
    SELECT 
        'FA25_SSC_ORDER'::VARCHAR,
        'Missing Customer'::VARCHAR,
        COUNT(*)::INTEGER,
        'FA25_SSC_ORDER records with non-existent customer_id'::TEXT
    FROM "FA25_SSC_ORDER" o
    LEFT JOIN "FA25_SSC_CUSTOMER" c ON o.customer_id = c.customer_id
    WHERE c.customer_id IS NULL;

    -- Check for NULL values in critical fields
    RETURN QUERY
    SELECT 
        'FA25_SSC_PRODUCT'::VARCHAR,
        'NULL Values'::VARCHAR,
        COUNT(*)::INTEGER,
        'FA25_SSC_PRODUCT records with missing critical fields'::TEXT
    FROM "FA25_SSC_PRODUCT"
    WHERE product_id IS NULL OR product_name IS NULL OR subcategory_id IS NULL;
END;
$$ LANGUAGE plpgsql;


-- PROCEDURE 6: Get Data Quality Summary (Future - Analytics)
-- Returns: entity, total_count, valid_count, orphaned_count, quality_percentage

CREATE OR REPLACE FUNCTION get_data_quality_summary()
RETURNS TABLE (
    entity VARCHAR,
    total_count BIGINT,
    valid_count BIGINT,
    orphaned_count BIGINT,
    quality_percentage NUMERIC
) AS $$
BEGIN
    -- Customer quality
    RETURN QUERY
    SELECT 
        'FA25_SSC_CUSTOMER'::VARCHAR,
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN customer_id IS NOT NULL AND customer_name IS NOT NULL THEN 1 END)::BIGINT,
        0::BIGINT,
        ROUND(COUNT(CASE WHEN customer_id IS NOT NULL AND customer_name IS NOT NULL THEN 1 END)::NUMERIC / 
            NULLIF(COUNT(*), 0) * 100, 2)::NUMERIC
    FROM "FA25_SSC_CUSTOMER";

    -- Product quality
    RETURN QUERY
    SELECT 
        'FA25_SSC_PRODUCT'::VARCHAR,
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN product_id IS NOT NULL AND product_name IS NOT NULL AND subcategory_id IS NOT NULL THEN 1 END)::BIGINT,
        0::BIGINT,
        ROUND(COUNT(CASE WHEN product_id IS NOT NULL AND product_name IS NOT NULL AND subcategory_id IS NOT NULL THEN 1 END)::NUMERIC / 
            NULLIF(COUNT(*), 0) * 100, 2)::NUMERIC
    FROM "FA25_SSC_PRODUCT";

    -- Order quality (including referential integrity)
    RETURN QUERY
    SELECT 
        'FA25_SSC_ORDER'::VARCHAR,
        COUNT(DISTINCT o.order_id)::BIGINT,
        COUNT(DISTINCT CASE WHEN c.customer_id IS NOT NULL THEN o.order_id END)::BIGINT,
        COUNT(DISTINCT CASE WHEN c.customer_id IS NULL THEN o.order_id END)::BIGINT,
        ROUND(COUNT(DISTINCT CASE WHEN c.customer_id IS NOT NULL THEN o.order_id END)::NUMERIC / 
            NULLIF(COUNT(DISTINCT o.order_id), 0) * 100, 2)::NUMERIC
    FROM "FA25_SSC_ORDER" o
    LEFT JOIN "FA25_SSC_CUSTOMER" c ON o.customer_id = c.customer_id;

    -- Return quality
    RETURN QUERY
    SELECT 
        'FA25_SSC_RETURN'::VARCHAR,
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN return_id IS NOT NULL AND order_id IS NOT NULL THEN 1 END)::BIGINT,
        COUNT(CASE WHEN order_id IS NOT NULL AND order_id NOT IN (SELECT order_id FROM "FA25_SSC_ORDER") THEN 1 END)::BIGINT,
        ROUND(COUNT(CASE WHEN return_id IS NOT NULL AND order_id IS NOT NULL THEN 1 END)::NUMERIC / 
            NULLIF(COUNT(*), 0) * 100, 2)::NUMERIC
    FROM "FA25_SSC_RETURN";
END;
$$ LANGUAGE plpgsql;


-- PROCEDURE 7: Cleanup Orphaned Records (Future - Maintenance)
-- Returns: deleted_count, deleted_tables

CREATE OR REPLACE FUNCTION cleanup_orphaned_records(
    OUT deleted_count INTEGER,
    OUT deleted_tables TEXT
)
AS $$
DECLARE
    orphaned_count INTEGER := 0;
    deleted_tables_str TEXT := '';
BEGIN
    -- Delete orphaned ORDER_PRODUCT records
    DELETE FROM "FA25_SSC_ORDER_PRODUCT" 
    WHERE order_id NOT IN (SELECT order_id FROM "FA25_SSC_ORDER");
    orphaned_count := orphaned_count + FOUND::INTEGER::INTEGER;
    IF FOUND THEN
        deleted_tables_str := deleted_tables_str || 'ORDER_PRODUCT, ';
    END IF;

    -- Delete orphaned RETURN records
    DELETE FROM "FA25_SSC_RETURN" 
    WHERE order_id NOT IN (SELECT order_id FROM "FA25_SSC_ORDER");
    orphaned_count := orphaned_count + FOUND::INTEGER::INTEGER;
    IF FOUND THEN
        deleted_tables_str := deleted_tables_str || 'RETURN, ';
    END IF;

    -- Trim trailing comma and space
    deleted_tables_str := TRIM(TRAILING ', ' FROM deleted_tables_str);
    
    deleted_count := orphaned_count;
    deleted_tables := deleted_tables_str;
END;
$$ LANGUAGE plpgsql;


-- GRANT PERMISSIONS

-- Functions in use now
GRANT EXECUTE ON FUNCTION validate_customer(VARCHAR) TO awesome_admin;
GRANT EXECUTE ON FUNCTION validate_order(VARCHAR) TO awesome_admin;
GRANT EXECUTE ON FUNCTION validate_product(VARCHAR) TO awesome_admin;

-- Functions for future use
GRANT EXECUTE ON FUNCTION validate_return(VARCHAR) TO awesome_admin;
GRANT EXECUTE ON FUNCTION check_data_integrity() TO awesome_admin;
GRANT EXECUTE ON FUNCTION get_data_quality_summary() TO awesome_admin;
GRANT EXECUTE ON FUNCTION cleanup_orphaned_records() TO awesome_admin;
