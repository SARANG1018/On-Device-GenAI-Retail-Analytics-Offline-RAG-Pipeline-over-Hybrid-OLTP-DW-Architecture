

-- INDEXES FOR CDC (Change Data Capture)
CREATE INDEX idx_FA25_SSC_SEGMENT_tbl_last_dt ON "FA25_SSC_SEGMENT" (tbl_last_dt);
CREATE INDEX idx_FA25_SSC_CATEGORY_tbl_last_dt ON "FA25_SSC_CATEGORY" (tbl_last_dt);
CREATE INDEX idx_FA25_SSC_SUBCATEGORY_tbl_last_dt ON "FA25_SSC_SUBCATEGORY" (tbl_last_dt);
CREATE INDEX idx_FA25_SSC_PRODUCT_tbl_last_dt ON "FA25_SSC_PRODUCT" (tbl_last_dt);
CREATE INDEX idx_FA25_SSC_CUSTOMER_tbl_last_dt ON "FA25_SSC_CUSTOMER" (tbl_last_dt);
CREATE INDEX idx_FA25_SSC_ORDER_tbl_last_dt ON "FA25_SSC_ORDER" (tbl_last_dt);
CREATE INDEX idx_FA25_SSC_ORDER_PRODUCT_tbl_last_dt ON "FA25_SSC_ORDER_PRODUCT" (tbl_last_dt);
CREATE INDEX idx_FA25_SSC_RETURN_tbl_last_dt ON fa25_ssc_return_partitioned (tbl_last_dt);

-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
CREATE OR REPLACE FUNCTION update_tbl_last_dt()
RETURNS TRIGGER AS $$
BEGIN
    NEW.tbl_last_dt := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER FA25_SSC_segment_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_SEGMENT"
FOR EACH ROW EXECUTE FUNCTION update_tbl_last_dt();

CREATE TRIGGER FA25_SSC_category_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_CATEGORY"
FOR EACH ROW EXECUTE FUNCTION update_tbl_last_dt();

CREATE TRIGGER FA25_SSC_subcategory_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_SUBCATEGORY"
FOR EACH ROW EXECUTE FUNCTION update_tbl_last_dt();

CREATE TRIGGER FA25_SSC_product_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_PRODUCT"
FOR EACH ROW EXECUTE FUNCTION update_tbl_last_dt();

CREATE TRIGGER FA25_SSC_customer_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_CUSTOMER"
FOR EACH ROW EXECUTE FUNCTION update_tbl_last_dt();

CREATE TRIGGER FA25_SSC_order_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_ORDER"
FOR EACH ROW EXECUTE FUNCTION update_tbl_last_dt();

CREATE TRIGGER FA25_SSC_order_product_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_ORDER_PRODUCT"
FOR EACH ROW EXECUTE FUNCTION update_tbl_last_dt();

CREATE TRIGGER FA25_SSC_return_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON fa25_ssc_return_partitioned
FOR EACH ROW EXECUTE FUNCTION update_tbl_last_dt();


-- STORED PROCEDURES FOR DATA VALIDATION

-- PROCEDURE 1: Validate Customer
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


-- PROCEDURE 2: Validate Order
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
            ELSE 'Valid'
        END::VARCHAR
    FROM (SELECT p_order_id) AS dummy(id)
    LEFT JOIN "FA25_SSC_ORDER" o ON o.order_id = dummy.id
    LEFT JOIN "FA25_SSC_CUSTOMER" c ON o.customer_id = c.customer_id;
END;
$$ LANGUAGE plpgsql;


-- PROCEDURE 3: Validate Product
CREATE OR REPLACE FUNCTION validate_product(
    p_product_id VARCHAR
)
RETURNS TABLE (
    is_valid BOOLEAN,
    product_name VARCHAR,
    subcategory_name VARCHAR,
    category_name VARCHAR,
    error_message VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE WHEN p.product_id IS NOT NULL THEN true ELSE false END,
        COALESCE(p.product_name, 'N/A')::VARCHAR,
        COALESCE(s.subcategory_name, 'N/A')::VARCHAR,
        COALESCE(c.category_name, 'N/A')::VARCHAR,
        CASE 
            WHEN p.product_id IS NULL THEN 'Product not found'
            ELSE 'Valid'
        END::VARCHAR
    FROM (SELECT p_product_id) AS dummy(id)
    LEFT JOIN "FA25_SSC_PRODUCT" p ON p.product_id = dummy.id
    LEFT JOIN "FA25_SSC_SUBCATEGORY" s ON p.subcategory_id = s.subcategory_id
    LEFT JOIN "FA25_SSC_CATEGORY" c ON s.category_id = c.category_id;
END;
$$ LANGUAGE plpgsql;
