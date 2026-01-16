
-- OLTP DDL (Data Definition Language)
-- PostgreSQL OLTP Database Schema

-- Master Tables
CREATE TABLE public."FA25_SSC_SEGMENT" (
    row_id bigint NOT NULL,
    segment_id text NOT NULL PRIMARY KEY,
    segment_name text NOT NULL,
    tbl_last_dt timestamp without time zone NOT NULL
);

CREATE TABLE public."FA25_SSC_CATEGORY" (
    row_id bigint NOT NULL,
    category_id text NOT NULL PRIMARY KEY,
    category_name text NOT NULL,
    tbl_last_dt timestamp without time zone NOT NULL
);

CREATE TABLE public."FA25_SSC_SUBCATEGORY" (
    row_id bigint NOT NULL,
    subcategory_id text NOT NULL PRIMARY KEY,
    subcategory_name text NOT NULL,
    category_id text NOT NULL REFERENCES "FA25_SSC_CATEGORY"(category_id),
    tbl_last_dt timestamp without time zone NOT NULL
);

-- Dimension Tables
CREATE TABLE public."FA25_SSC_PRODUCT" (
    row_id bigint NOT NULL,
    product_id text NOT NULL PRIMARY KEY,
    product_name text NOT NULL,
    subcategory_id text NOT NULL REFERENCES "FA25_SSC_SUBCATEGORY"(subcategory_id),
    tbl_last_dt timestamp without time zone NOT NULL
);

CREATE TABLE public."FA25_SSC_CUSTOMER" (
    row_id bigint NOT NULL,
    customer_id text NOT NULL PRIMARY KEY,
    customer_name text NOT NULL,
    country text NOT NULL,
    state text NOT NULL,
    city text NOT NULL,
    postal_code text,
    market text NOT NULL,
    region text NOT NULL,
    segment_id text REFERENCES "FA25_SSC_SEGMENT"(segment_id),
    tbl_last_dt timestamp without time zone NOT NULL
);

-- Transactional Tables
CREATE TABLE public."FA25_SSC_ORDER" (
    row_id bigint NOT NULL,
    order_id text NOT NULL PRIMARY KEY,
    order_date date NOT NULL,
    order_priority text NOT NULL,
    customer_id text NOT NULL REFERENCES "FA25_SSC_CUSTOMER"(customer_id),
    tbl_last_dt timestamp without time zone NOT NULL
);

CREATE TABLE public."FA25_SSC_ORDER_PRODUCT" (
    row_id bigint NOT NULL,
    order_id text NOT NULL REFERENCES "FA25_SSC_ORDER"(order_id),
    product_id text NOT NULL REFERENCES "FA25_SSC_PRODUCT"(product_id),
    quantity integer NOT NULL,
    sales numeric(12,2) NOT NULL,
    discount numeric(5,2) NOT NULL,
    profit numeric(12,2) NOT NULL,
    ship_date date NOT NULL,
    ship_mode text NOT NULL,
    shipping_cost numeric(12,2) NOT NULL,
    tbl_last_dt timestamp without time zone NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE public.fa25_ssc_return_partitioned (
    row_id bigint NOT NULL,
    returned text NOT NULL,
    order_id text NOT NULL REFERENCES "FA25_SSC_ORDER"(order_id),
    return_date date,
    region text NOT NULL,
    tbl_last_dt timestamp without time zone NOT NULL,
    PRIMARY KEY (order_id)
) PARTITION BY RANGE (return_date);

-- Staging Tables
CREATE TABLE public.stg_orders_raw (
    row_id text,
    order_id text,
    order_date text,
    ship_date text,
    ship_mode text,
    customer_id text,
    customer_name text,
    segment text,
    postal_code text,
    city text,
    state text,
    country text,
    region text,
    market text,
    product_id text,
    category text,
    sub_category text,
    product_name text,
    sales text,
    quantity text,
    discount text,
    profit text,
    shipping_cost text,
    order_priority text
);

CREATE TABLE public.stg_returns_raw (
    returned text,
    order_id text,
    region text
);

-- Trigger Function for CDC Timestamp
CREATE FUNCTION public.set_tbl_last_dt() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.tbl_last_dt := CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$;
