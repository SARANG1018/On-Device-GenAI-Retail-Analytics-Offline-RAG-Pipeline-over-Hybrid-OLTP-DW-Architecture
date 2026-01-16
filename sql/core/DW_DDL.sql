
-- DIMENSION: fa25_ssc_dim_date
-- Purpose: Time dimension for temporal analysis
-- Granularity: Daily
CREATE TABLE fa25_ssc_dim_date (
    date_key            INT PRIMARY KEY,
    full_date           DATE NOT NULL UNIQUE,
    year                INT NOT NULL,
    month               INT NOT NULL,
    day                 INT NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- DIMENSION: fa25_ssc_dim_customer
-- Purpose: Customer information and geographic location
-- Granularity: One row per unique customer
CREATE TABLE fa25_ssc_dim_customer (
    customer_key        INT PRIMARY KEY AUTO_INCREMENT,
    customer_id         VARCHAR(20) UNIQUE NOT NULL,
    customer_name       VARCHAR(255) NOT NULL,
    country             VARCHAR(100),
    state               VARCHAR(100),
    city                VARCHAR(100),
    postal_code         VARCHAR(20),
    region              VARCHAR(50),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- DIMENSION: fa25_ssc_dim_product
-- Purpose: Product details with category hierarchy
-- Granularity: One row per unique product
CREATE TABLE fa25_ssc_dim_product (
    product_key         INT PRIMARY KEY AUTO_INCREMENT,
    product_id          VARCHAR(20) UNIQUE NOT NULL,
    product_name        VARCHAR(255) NOT NULL,
    subcategory_id      VARCHAR(20),
    subcategory_name    VARCHAR(100),
    category_id         VARCHAR(20),
    category_name       VARCHAR(100),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- DIMENSION: fa25_ssc_dim_return
-- Purpose: Return/refund details
-- Granularity: One row per unique return
CREATE TABLE fa25_ssc_dim_return (
    return_key          INT PRIMARY KEY AUTO_INCREMENT,
    return_id           VARCHAR(50),
    return_status       VARCHAR(50) NOT NULL,
    return_region       VARCHAR(50),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- FACT: fa25_ssc_fact_sales
-- Purpose: Transactional sales facts
-- Granularity: One row per line item (order-product combination)
-- Type: Additive fact table
CREATE TABLE fa25_ssc_fact_sales (
    sales_key           INT PRIMARY KEY AUTO_INCREMENT,
    customer_key        INT NOT NULL,
    product_key         INT NOT NULL,
    date_key            INT NOT NULL,
    return_key          INT,
    sales               DECIMAL(12,2) NOT NULL,
    quantity            INT NOT NULL,
    discount            DECIMAL(5,2),
    profit              DECIMAL(12,2),
    shipping_cost       DECIMAL(12,2),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_key) REFERENCES fa25_ssc_dim_customer(customer_key),
    FOREIGN KEY (product_key) REFERENCES fa25_ssc_dim_product(product_key),
    FOREIGN KEY (date_key) REFERENCES fa25_ssc_dim_date(date_key),
    FOREIGN KEY (return_key) REFERENCES fa25_ssc_dim_return(return_key),
    INDEX idx_customer_key (customer_key),
    INDEX idx_product_key (product_key),
    INDEX idx_date_key (date_key),
    INDEX idx_return_key (return_key)
);

-- FACT: fa25_ssc_fact_return
-- Purpose: Return/refund transactions
-- Granularity: One row per return event
-- Type: Additive fact table
CREATE TABLE fa25_ssc_fact_return (
    return_fact_key     INT PRIMARY KEY AUTO_INCREMENT,
    return_key          INT NOT NULL,
    customer_key        INT NOT NULL,
    order_key           INT,
    date_key            INT NOT NULL,
    return_status       VARCHAR(50),
    return_region       VARCHAR(50),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (return_key) REFERENCES fa25_ssc_dim_return(return_key),
    FOREIGN KEY (customer_key) REFERENCES fa25_ssc_dim_customer(customer_key),
    FOREIGN KEY (date_key) REFERENCES fa25_ssc_dim_date(date_key),
    INDEX idx_return_key (return_key),
    INDEX idx_customer_key (customer_key),
    INDEX idx_date_key (date_key)
);

-- ============================================================================
-- STAR SCHEMA SUMMARY
-- ============================================================================
-- Dimensions:    4 (date, customer, product, return)
-- Facts:         2 (sales, return)
-- Design Type:   Traditional Star Schema
-- Typical Use:   OLAP analytics queries (aggregations, comparisons)

-- ============================================================================
-- INDEXES FOR QUERY PERFORMANCE
-- ============================================================================
-- All dimension tables have primary keys on dimension keys
-- All fact tables have foreign keys with indexes for efficient joins
-- Date key is indexed on all fact tables for time-based queries
-- Customer and product keys are indexed for dimensional analysis

-- ============================================================================
-- CDC SUPPORT FOR INCREMENTAL LOADS
-- ============================================================================
-- All tables have updated_at timestamp for tracking changes
-- ON DUPLICATE KEY UPDATE strategy used in ETL for deduplication
-- Allows efficient incremental loads on subsequent ETL runs
