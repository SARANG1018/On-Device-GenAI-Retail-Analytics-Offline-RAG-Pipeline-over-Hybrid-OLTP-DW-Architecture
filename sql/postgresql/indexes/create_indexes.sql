
-- Index on FA25_SSC_SEGMENT table
CREATE INDEX idx_FA25_SSC_SEGMENT_tbl_last_dt ON "FA25_SSC_SEGMENT" (tbl_last_dt);

-- Index on FA25_SSC_CATEGORY table
CREATE INDEX idx_FA25_SSC_CATEGORY_tbl_last_dt ON "FA25_SSC_CATEGORY" (tbl_last_dt);

-- Index on FA25_SSC_SUBCATEGORY table
CREATE INDEX idx_FA25_SSC_SUBCATEGORY_tbl_last_dt ON "FA25_SSC_SUBCATEGORY" (tbl_last_dt);

-- Index on FA25_SSC_PRODUCT table
CREATE INDEX idx_FA25_SSC_PRODUCT_tbl_last_dt ON "FA25_SSC_PRODUCT" (tbl_last_dt);

-- Index on FA25_SSC_CUSTOMER table
CREATE INDEX idx_FA25_SSC_CUSTOMER_tbl_last_dt ON "FA25_SSC_CUSTOMER" (tbl_last_dt);

-- Index on FA25_SSC_ORDER table (Most important - 51,290 rows)
CREATE INDEX idx_FA25_SSC_ORDER_tbl_last_dt ON "FA25_SSC_ORDER" (tbl_last_dt);

-- Index on FA25_SSC_ORDER_PRODUCT table (Important - large transactional table)
CREATE INDEX idx_FA25_SSC_ORDER_PRODUCT_tbl_last_dt ON "FA25_SSC_ORDER_PRODUCT" (tbl_last_dt);

-- Index on FA25_SSC_RETURN table (1,079 rows)
CREATE INDEX idx_FA25_SSC_RETURN_tbl_last_dt ON "FA25_SSC_RETURN" (tbl_last_dt);

-- verify all indexes exist:
-- SELECT indexname FROM pg_indexes WHERE tablename IN 
-- ('SEGMENT', 'CATEGORY', 'SUBCATEGORY', 'PRODUCT', 'CUSTOMER', 'ORDER', 'ORDER_PRODUCT', 'RETURN')
-- AND indexname LIKE 'idx_%tbl_last_dt';
