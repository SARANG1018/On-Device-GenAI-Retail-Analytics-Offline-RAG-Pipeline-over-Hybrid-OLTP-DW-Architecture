
-- Query to retrieve data dictionary:
SELECT 
    t.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'Yes' ELSE 'No' END AS is_primary_key,
    CASE WHEN fk.constraint_name IS NOT NULL THEN 'Yes' ELSE 'No' END AS is_foreign_key
FROM 
    information_schema.tables t
    LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
    LEFT JOIN information_schema.table_constraints tc 
        ON t.table_name = tc.table_name 
        AND c.column_name = ANY(string_to_array(tc.constraint_def, ', '))
    LEFT JOIN information_schema.referential_constraints fk 
        ON tc.constraint_name = fk.constraint_name
WHERE 
    t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
ORDER BY 
    t.table_name, c.ordinal_position;


-- TABLE: FA25_SSC_SEGMENT (Master Data)
CREATE TABLE "FA25_SSC_SEGMENT" (
    row_id                 bigint                              NOT NULL,
    segment_id             text                                NOT NULL PRIMARY KEY,
    segment_name           text                                NOT NULL,
    tbl_last_dt            timestamp without time zone         NOT NULL
);

-- TABLE: FA25_SSC_CATEGORY (Master Data)
CREATE TABLE "FA25_SSC_CATEGORY" (
    row_id                 bigint                              NOT NULL,
    category_id            text                                NOT NULL PRIMARY KEY,
    category_name          text                                NOT NULL,
    tbl_last_dt            timestamp without time zone         NOT NULL
);

-- TABLE: FA25_SSC_SUBCATEGORY (Master Data)
CREATE TABLE "FA25_SSC_SUBCATEGORY" (
    row_id                 bigint                              NOT NULL,
    subcategory_id         text                                NOT NULL PRIMARY KEY,
    subcategory_name       text                                NOT NULL,
    category_id            text                                NOT NULL (FK → FA25_SSC_CATEGORY),
    tbl_last_dt            timestamp without time zone         NOT NULL
);

-- TABLE: FA25_SSC_PRODUCT (Dimension)
CREATE TABLE "FA25_SSC_PRODUCT" (
    row_id                 bigint                              NOT NULL,
    product_id             text                                NOT NULL PRIMARY KEY,
    product_name           text                                NOT NULL,
    subcategory_id         text                                NOT NULL (FK → FA25_SSC_SUBCATEGORY),
    tbl_last_dt            timestamp without time zone         NOT NULL
);

-- TABLE: FA25_SSC_CUSTOMER (Dimension)
CREATE TABLE "FA25_SSC_CUSTOMER" (
    row_id                 bigint                              NOT NULL,
    customer_id            text                                NOT NULL PRIMARY KEY,
    customer_name          text                                NOT NULL,
    country                text                                NOT NULL,
    state                  text                                NOT NULL,
    city                   text                                NOT NULL,
    postal_code            text                                NULL,
    market                 text                                NOT NULL,
    region                 text                                NOT NULL,
    segment_id             text                                NULL (FK → FA25_SSC_SEGMENT),
    tbl_last_dt            timestamp without time zone         NOT NULL
);

-- TABLE: FA25_SSC_ORDER (Transactional)
CREATE TABLE "FA25_SSC_ORDER" (
    row_id                 bigint                              NOT NULL,
    order_id               text                                NOT NULL PRIMARY KEY,
    order_date             date                                NOT NULL,
    order_priority         text                                NOT NULL,
    customer_id            text                                NOT NULL (FK → FA25_SSC_CUSTOMER),
    tbl_last_dt            timestamp without time zone         NOT NULL
);

-- TABLE: FA25_SSC_ORDER_PRODUCT (Transactional - Line Items)
CREATE TABLE "FA25_SSC_ORDER_PRODUCT" (
    row_id                 bigint                              NOT NULL,
    order_id               text                                NOT NULL (FK → FA25_SSC_ORDER),
    product_id             text                                NOT NULL (FK → FA25_SSC_PRODUCT),
    quantity               integer                             NOT NULL,
    sales                  numeric(12,2)                       NOT NULL,
    discount               numeric(5,2)                        NOT NULL,
    profit                 numeric(12,2)                       NOT NULL,
    ship_date              date                                NOT NULL,
    ship_mode              text                                NOT NULL,
    shipping_cost          numeric(12,2)                       NOT NULL,
    tbl_last_dt            timestamp without time zone         NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

-- TABLE: fa25_ssc_return_partitioned (Transactional - Partitioned)
CREATE TABLE fa25_ssc_return_partitioned (
    row_id                 bigint                              NOT NULL,
    returned               text                                NOT NULL,
    order_id               text                                NOT NULL (FK → FA25_SSC_ORDER),
    return_date            date                                NULL,
    region                 text                                NOT NULL,
    tbl_last_dt            timestamp without time zone         NOT NULL,
    PRIMARY KEY (order_id)
) PARTITION BY RANGE (return_date);

-- TABLE: stg_orders_raw (Staging)
-- Rows: Variable (temporary)
CREATE TABLE stg_orders_raw (
    row_id                 text,
    order_id               text,
    order_date             text,
    ship_date              text,
    ship_mode              text,
    customer_id            text,
    customer_name          text,
    segment                text,
    postal_code            text,
    city                   text,
    state                  text,
    country                text,
    region                 text,
    market                 text,
    product_id             text,
    category               text,
    sub_category           text,
    product_name           text,
    sales                  text,
    quantity               text,
    discount               text,
    profit                 text,
    shipping_cost          text,
    order_priority         text
);

-- TABLE: stg_returns_raw (Staging)
-- Rows: Variable (temporary)
CREATE TABLE stg_returns_raw (
    returned               text,
    order_id               text,
    region                 text
);

-- ============================================================================
-- CDC INDEXES FOR EFFICIENT INCREMENTAL EXTRACTION
-- ============================================================================
-- All tables have indexes on tbl_last_dt column for Change Data Capture
-- These indexes enable efficient querying of changed records since last ETL run

-- ============================================================================
-- SUMMARY STATISTICS
-- ============================================================================
-- Master/Reference Tables:    3 (SEGMENT, CATEGORY, SUBCATEGORY)
-- Dimension Tables:           2 (PRODUCT, CUSTOMER)
-- Transactional Tables:       3 (ORDER, ORDER_PRODUCT, RETURN_PARTITIONED)
-- Staging Tables:             2 (stg_orders_raw, stg_returns_raw)
-- Total Tables:               10

-- Total OLTP Records:
-- - SEGMENT:            3 records
-- - CATEGORY:           3 records
-- - SUBCATEGORY:        14 records
-- - PRODUCT:            4,861 records
-- - CUSTOMER:           793 records
-- - ORDER:              51,290 records
-- - ORDER_PRODUCT:      179,659 records
-- - RETURN:             2,167 records
-- TOTAL:                238,790 records
