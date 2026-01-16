
-- Grant permissions to awesome_admin
GRANT USAGE ON SCHEMA public TO awesome_admin;
GRANT CREATE ON SCHEMA public TO awesome_admin;

-- Create a function to update tbl_last_dt
CREATE OR REPLACE FUNCTION update_tbl_last_dt()
RETURNS TRIGGER AS $$
BEGIN
    NEW.tbl_last_dt := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for FA25_SSC_SEGMENT table
CREATE TRIGGER FA25_SSC_segment_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_SEGMENT"
FOR EACH ROW
EXECUTE FUNCTION update_tbl_last_dt();

-- Trigger for FA25_SSC_CATEGORY table
CREATE TRIGGER FA25_SSC_category_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_CATEGORY"
FOR EACH ROW
EXECUTE FUNCTION update_tbl_last_dt();

-- Trigger for FA25_SSC_SUBCATEGORY table
CREATE TRIGGER FA25_SSC_subcategory_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_SUBCATEGORY"
FOR EACH ROW
EXECUTE FUNCTION update_tbl_last_dt();

-- Trigger for FA25_SSC_PRODUCT table
CREATE TRIGGER FA25_SSC_product_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_PRODUCT"
FOR EACH ROW
EXECUTE FUNCTION update_tbl_last_dt();

-- Trigger for FA25_SSC_CUSTOMER table
CREATE TRIGGER FA25_SSC_customer_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_CUSTOMER"
FOR EACH ROW
EXECUTE FUNCTION update_tbl_last_dt();

-- Trigger for FA25_SSC_ORDER table
CREATE TRIGGER FA25_SSC_order_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_ORDER"
FOR EACH ROW
EXECUTE FUNCTION update_tbl_last_dt();

-- Trigger for FA25_SSC_ORDER_PRODUCT table
CREATE TRIGGER FA25_SSC_order_product_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_ORDER_PRODUCT"
FOR EACH ROW
EXECUTE FUNCTION update_tbl_last_dt();

-- Trigger for FA25_SSC_RETURN table
CREATE TRIGGER FA25_SSC_return_update_tbl_last_dt
BEFORE INSERT OR UPDATE ON "FA25_SSC_RETURN"
FOR EACH ROW
EXECUTE FUNCTION update_tbl_last_dt();
