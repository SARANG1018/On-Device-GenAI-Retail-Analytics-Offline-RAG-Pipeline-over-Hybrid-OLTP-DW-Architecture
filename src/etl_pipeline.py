import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple
import json

from utils import (
    get_postgres_connection,
    release_postgres_connection,
    get_mysql_connection,
    load_env_config,
    get_last_etl_run_timestamp,
    save_etl_run_metadata,
    get_changed_records_since_last_run,
    logger
)


def get_last_etl_timestamp(config: Dict) -> str:
    logger.info("CDC: Getting last ETL run timestamp for incremental load")
    timestamp = get_last_etl_run_timestamp(config)
    logger.info(f"CDC: Will extract records changed after {timestamp}")
    return timestamp


def extract_from_oltp(config: Dict, last_timestamp: str) -> Dict[str, pd.DataFrame]:
    try:
        logger.info("=" * 80)
        logger.info("EXTRACT PHASE: CDC-Based Incremental Load (8 OLTP Tables)")
        logger.info(f"Last successful ETL run: {last_timestamp}")
        logger.info("=" * 80)
        
        conn = get_postgres_connection(config)
        
        # Extract SEGMENT master data
        logger.info("Extracting SEGMENT master data...")
        sql_segment = "SELECT * FROM \"FA25_SSC_SEGMENT\""
        df_segment = pd.read_sql(sql_segment, conn)
        logger.info(f"Extracted {len(df_segment)} segment records")
        
        # Extract CATEGORY master data
        logger.info("Extracting CATEGORY master data...")
        sql_category = "SELECT * FROM \"FA25_SSC_CATEGORY\""
        df_category = pd.read_sql(sql_category, conn)
        logger.info(f"Extracted {len(df_category)} category records")
        
        # Extract SUBCATEGORY master data
        logger.info("Extracting SUBCATEGORY master data...")
        sql_subcategory = "SELECT * FROM \"FA25_SSC_SUBCATEGORY\""
        df_subcategory = pd.read_sql(sql_subcategory, conn)
        logger.info(f"Extracted {len(df_subcategory)} subcategory records")
        
        # Extract PRODUCTS (with category/subcategory relationships)
        logger.info("Extracting all PRODUCT dimension records...")
        sql_products = "SELECT * FROM \"FA25_SSC_PRODUCT\""
        df_products = pd.read_sql(sql_products, conn)
        logger.info(f"Extracted {len(df_products)} product records")
        
        # Extract CUSTOMERS (with segment relationships)
        logger.info("Extracting all CUSTOMER dimension records...")
        sql_customers = "SELECT * FROM \"FA25_SSC_CUSTOMER\""
        df_customers = pd.read_sql(sql_customers, conn)
        logger.info(f"Extracted {len(df_customers)} customer records")
        
        # Extract ORDERS changed records using CDC
        logger.info("CDC: Extracting changed ORDER records...")
        sql_orders = f"""
        SELECT * FROM \"FA25_SSC_ORDER\" 
        WHERE \"tbl_last_dt\" > '{last_timestamp}'
        ORDER BY \"tbl_last_dt\"
        """
        df_orders = pd.read_sql(sql_orders, conn)
        logger.info(f"CDC: Extracted {len(df_orders)} changed order records")
        
        # Extract ORDER_PRODUCT changed records using CDC
        logger.info("CDC: Extracting changed ORDER_PRODUCT records...")
        sql_order_product = f"""
        SELECT * FROM \"FA25_SSC_ORDER_PRODUCT\" 
        WHERE \"tbl_last_dt\" > '{last_timestamp}'
        ORDER BY \"tbl_last_dt\"
        """
        df_order_product = pd.read_sql(sql_order_product, conn)
        logger.info(f"CDC: Extracted {len(df_order_product)} changed order-product records")
        
        # Extract RETURNS changed records using CDC
        logger.info("CDC: Extracting changed RETURN records...")
        sql_returns = f"""
        SELECT * FROM "FA25_SSC_RETURN" 
        WHERE "tbl_last_dt" > '{last_timestamp}'
        ORDER BY "tbl_last_dt"
        """
        df_returns = pd.read_sql(sql_returns, conn)
        logger.info(f"CDC: Extracted {len(df_returns)} changed return records")
        
        release_postgres_connection(conn)
        
        extracted_data = {
            'segment': df_segment,
            'category': df_category,
            'subcategory': df_subcategory,
            'products': df_products,
            'customers': df_customers,
            'orders': df_orders,
            'order_product': df_order_product,
            'returns': df_returns
        }
        
        logger.info("=" * 80)
        logger.info("EXTRACT PHASE COMPLETED")
        logger.info(f"Total records to process: {len(df_orders) + len(df_order_product) + len(df_returns)}")
        logger.info("=" * 80)
        return extracted_data
    
    except Exception as e:
        logger.error(f"Error in EXTRACT phase: {e}")
        raise


# TRANSFORM PHASE
def transform_to_star_schema(extracted_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    try:
        logger.info("=" * 80)
        logger.info("TRANSFORM Phase: Converting OLTP to OLAP star schema (6 tables)")
        logger.info("=" * 80)
        
        # Extract all OLTP tables
        df_segment = extracted_data['segment']
        df_category = extracted_data['category']
        df_subcategory = extracted_data['subcategory']
        df_products = extracted_data['products']
        df_customers = extracted_data['customers']
        df_orders = extracted_data['orders']
        df_order_product = extracted_data['order_product']
        df_returns = extracted_data['returns']
        
        # Create fa25_ssc_dim_date (time dimension)
        logger.info("Creating fa25_ssc_dim_date table (time dimension)")
        # Generate date range from orders
        if len(df_orders) > 0:
            all_dates = pd.concat([
                pd.to_datetime(df_orders['order_date']),
                pd.to_datetime(df_order_product['ship_date']) if len(df_order_product) > 0 else pd.Series([])
            ], ignore_index=True).dropna().unique()
            
            date_range = pd.date_range(start=min(all_dates), end=max(all_dates), freq='D')
        else:
            date_range = pd.date_range(start='2020-01-01', end=datetime.now().date(), freq='D')
        
        fa25_ssc_dim_date = pd.DataFrame({'full_date': date_range})
        # Use YYYYMMDD format for date_key (e.g., 20251210) - matches fa25_ssc_fact_sales date_key format
        fa25_ssc_dim_date['date_key'] = fa25_ssc_dim_date['full_date'].dt.strftime('%Y%m%d').astype(int)
        fa25_ssc_dim_date['year'] = fa25_ssc_dim_date['full_date'].dt.year
        fa25_ssc_dim_date['month'] = fa25_ssc_dim_date['full_date'].dt.month
        fa25_ssc_dim_date['day'] = fa25_ssc_dim_date['full_date'].dt.day
        logger.info(f"fa25_ssc_dim_date created with {len(fa25_ssc_dim_date)} rows")
        
        # Create fa25_ssc_dim_customer
        logger.info("Creating fa25_ssc_dim_customer table")
        fa25_ssc_dim_customer = df_customers.copy()
        fa25_ssc_dim_customer['customer_key'] = range(1, len(fa25_ssc_dim_customer) + 1)
        # Note: segment_name, market removed from DW schema - using region instead
        logger.info(f"fa25_ssc_dim_customer created with {len(fa25_ssc_dim_customer)} rows")
        
        # Create fa25_ssc_dim_product
        logger.info("Creating fa25_ssc_dim_product table")
        fa25_ssc_dim_product = df_products.copy()
        fa25_ssc_dim_product['product_key'] = range(1, len(fa25_ssc_dim_product) + 1)
        
        # Add subcategory information first
        if len(df_subcategory) > 0:
            fa25_ssc_dim_product = fa25_ssc_dim_product.merge(
                df_subcategory[['subcategory_id', 'subcategory_name', 'category_id']],
                on='subcategory_id',
                how='left'
            )
        
        # Then add category information
        if len(df_category) > 0:
            fa25_ssc_dim_product = fa25_ssc_dim_product.merge(
                df_category[['category_id', 'category_name']],
                on='category_id',
                how='left'
            )
        logger.info(f"fa25_ssc_dim_product created with {len(fa25_ssc_dim_product)} rows")
        
        # Create fa25_ssc_dim_return
        logger.info("Creating fa25_ssc_dim_return table")
        if len(df_returns) > 0:
            fa25_ssc_dim_return = df_returns.copy()
            fa25_ssc_dim_return['return_key'] = range(1, len(fa25_ssc_dim_return) + 1)
            # Select columns from FA25_SSC_RETURN (columns are already correct: return_status, order_id, return_region)
            fa25_ssc_dim_return = fa25_ssc_dim_return[[
                'return_key', 'return_id', 'return_status', 'return_region', 'order_id'
            ]]
        else:
            fa25_ssc_dim_return = pd.DataFrame(columns=['return_key', 'return_id', 'return_status', 'return_region', 'order_id'])
        logger.info(f"fa25_ssc_dim_return created with {len(fa25_ssc_dim_return)} rows")
        
        # Create fa25_ssc_fact_sales
        logger.info("Creating fa25_ssc_fact_sales table")
        if len(df_order_product) > 0:
            fa25_ssc_fact_sales = df_order_product.copy()
            
            # Add order information
            if len(df_orders) > 0:
                fa25_ssc_fact_sales = fa25_ssc_fact_sales.merge(
                    df_orders[['order_id', 'customer_id', 'order_date']],
                    on='order_id',
                    how='left'
                )
            
            # Map to dimension keys
            fa25_ssc_fact_sales['customer_key'] = fa25_ssc_fact_sales['customer_id'].map(
                dict(zip(df_customers['customer_id'], fa25_ssc_dim_customer['customer_key']))
            )
            fa25_ssc_fact_sales['product_key'] = fa25_ssc_fact_sales['product_id'].map(
                dict(zip(df_products['product_id'], fa25_ssc_dim_product['product_key']))
            )
            
            # Convert ship_date to date_key for star schema
            fa25_ssc_fact_sales['ship_date'] = pd.to_datetime(fa25_ssc_fact_sales['ship_date'])
            fa25_ssc_fact_sales['date_key'] = fa25_ssc_fact_sales['ship_date'].dt.strftime('%Y%m%d').astype(int)
            
            # Calculate profit if not present
            if 'profit' not in fa25_ssc_fact_sales.columns:
                fa25_ssc_fact_sales['profit'] = fa25_ssc_fact_sales.get('sales', 0) - (fa25_ssc_fact_sales.get('discount', 0) * fa25_ssc_fact_sales.get('sales', 0))
            
            # Map return_key if returns exist (FK to fa25_ssc_dim_return)
            if len(fa25_ssc_dim_return) > 0:
                fa25_ssc_fact_sales['return_key'] = fa25_ssc_fact_sales['order_id'].map(
                    dict(zip(df_returns['order_id'], fa25_ssc_dim_return['return_key']))
                )
            else:
                fa25_ssc_fact_sales['return_key'] = None
        else:
            fa25_ssc_fact_sales = pd.DataFrame()
        
        logger.info(f"fa25_ssc_fact_sales created with {len(fa25_ssc_fact_sales)} rows")
        
        # Create fa25_ssc_fact_return
        logger.info("Creating fa25_ssc_fact_return table")
        if len(df_returns) > 0:
            fa25_ssc_fact_return = df_returns.copy()
            
            # Add order information to returns
            if len(df_orders) > 0:
                fa25_ssc_fact_return = fa25_ssc_fact_return.merge(
                    df_orders[['order_id', 'customer_id', 'order_date']],
                    on='order_id',
                    how='left'
                )
            
            # Map to dimension keys
            fa25_ssc_fact_return['customer_key'] = fa25_ssc_fact_return['customer_id'].map(
                dict(zip(df_customers['customer_id'], fa25_ssc_dim_customer['customer_key']))
            )
            fa25_ssc_fact_return['return_key'] = range(1, len(fa25_ssc_fact_return) + 1)
            
            # Create order_key from order_id (sequential mapping)
            fa25_ssc_fact_return['order_key'] = fa25_ssc_fact_return['order_id'].map(
                dict(zip(df_orders['order_id'], range(1, len(df_orders) + 1)))
            ).fillna(0).astype(int)  # Default to 0 if order_id not found
            
            # Create date_key from order_date
            fa25_ssc_fact_return['order_date'] = pd.to_datetime(fa25_ssc_fact_return['order_date'])
            fa25_ssc_fact_return['date_key'] = fa25_ssc_fact_return['order_date'].dt.strftime('%Y%m%d').astype(int)
            
            # Rename columns to match DW schema: returned -> return_status, region -> return_region
            fa25_ssc_fact_return = fa25_ssc_fact_return.rename(columns={
                'returned': 'return_status',
                'region': 'return_region'
            })
        else:
            fa25_ssc_fact_return = pd.DataFrame()
        
        logger.info(f"fa25_ssc_fact_return created with {len(fa25_ssc_fact_return)} rows")
        
        transformed_data = {
            'fa25_ssc_dim_date': fa25_ssc_dim_date,
            'fa25_ssc_dim_customer': fa25_ssc_dim_customer,
            'fa25_ssc_dim_product': fa25_ssc_dim_product,
            'fa25_ssc_dim_return': fa25_ssc_dim_return,
            'fa25_ssc_fact_sales': fa25_ssc_fact_sales,
            'fa25_ssc_fact_return': fa25_ssc_fact_return
        }
        
        logger.info("=" * 80)
        logger.info("TRANSFORM Phase completed successfully (6 OLAP tables ready)")
        logger.info("=" * 80)
        return transformed_data
    
    except Exception as e:
        logger.error(f"Error in TRANSFORM phase: {e}")
        raise


# LOAD PHASE
def load_to_dw(config: Dict, transformed_data: Dict[str, pd.DataFrame]) -> bool:

    
    try:
        logger.info("=" * 80)
        logger.info("LOAD Phase: Loading 6 OLAP tables into MySQL DW (CDC-aware upserts)")
        logger.info("=" * 80)
        
        conn = get_mysql_connection(config)
        cursor = conn.cursor()
        
        # ===== LOAD DIMENSIONS FIRST =====
        
        # Load fa25_ssc_dim_date (must be first - referenced by facts)
        logger.info("Loading fa25_ssc_dim_date with CDC deduplication...")
        fa25_ssc_dim_date = transformed_data['fa25_ssc_dim_date']
        date_inserted = 0
        if len(fa25_ssc_dim_date) > 0:
            # Batch insert - much faster than row by row
            batch_size = 1000
            for batch_start in range(0, len(fa25_ssc_dim_date), batch_size):
                batch_end = min(batch_start + batch_size, len(fa25_ssc_dim_date))
                batch = fa25_ssc_dim_date.iloc[batch_start:batch_end]
                
                # Build batch INSERT statement
                values_list = []
                params = []
                for _, row in batch.iterrows():
                    values_list.append("(%s, %s, %s, %s, %s, NOW(), NOW())")
                    params.extend([
                        int(row['date_key']),
                        row['full_date'].date(),
                        int(row['year']),
                        int(row['month']),
                        int(row['day'])
                    ])
                
                sql = f"""
                INSERT INTO fa25_ssc_dim_date 
                (date_key, full_date, year, month, day, created_at, updated_at)
                VALUES {','.join(values_list)}
                ON DUPLICATE KEY UPDATE
                full_date = VALUES(full_date),
                year = VALUES(year),
                month = VALUES(month),
                day = VALUES(day),
                updated_at = NOW()
                """
                cursor.execute(sql, params)
                date_inserted += len(batch)
            conn.commit()
        logger.info(f"fa25_ssc_dim_date loaded: {date_inserted} records (inserts + updates)")
        
        # Load fa25_ssc_dim_customer with CDC deduplication
        logger.info("Loading fa25_ssc_dim_customer with CDC deduplication...")
        fa25_ssc_dim_customer = transformed_data['fa25_ssc_dim_customer']
        customer_inserted = 0
        if len(fa25_ssc_dim_customer) > 0:
            # Batch insert - much faster
            batch_size = 1000
            for batch_start in range(0, len(fa25_ssc_dim_customer), batch_size):
                batch_end = min(batch_start + batch_size, len(fa25_ssc_dim_customer))
                batch = fa25_ssc_dim_customer.iloc[batch_start:batch_end]
                
                values_list = []
                params = []
                for _, row in batch.iterrows():
                    values_list.append("(%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())")
                    params.extend([
                        int(row.get('customer_key', 0)),
                        str(row.get('customer_id', None)) if row.get('customer_id') is not None else None,
                        row.get('customer_name', None),
                        row.get('country', None),
                        row.get('state', None),
                        row.get('city', None),
                        row.get('postal_code', None),
                        row.get('region', None)
                    ])
                
                sql = f"""
                INSERT INTO fa25_ssc_dim_customer 
                (customer_key, customer_id, customer_name, country, state, city, postal_code, region, created_at, updated_at)
                VALUES {','.join(values_list)}
                ON DUPLICATE KEY UPDATE
                customer_name = VALUES(customer_name),
                country = VALUES(country),
                state = VALUES(state),
                city = VALUES(city),
                postal_code = VALUES(postal_code),
                region = VALUES(region),
                updated_at = NOW()
                """
                cursor.execute(sql, params)
                customer_inserted += len(batch)
            conn.commit()
        logger.info(f"fa25_ssc_dim_customer loaded: {customer_inserted} records (inserts + updates)")
        
        # Load fa25_ssc_dim_product with CDC deduplication
        logger.info("Loading fa25_ssc_dim_product with CDC deduplication...")
        fa25_ssc_dim_product = transformed_data['fa25_ssc_dim_product']
        product_inserted = 0
        if len(fa25_ssc_dim_product) > 0:
            # Batch insert
            batch_size = 1000
            for batch_start in range(0, len(fa25_ssc_dim_product), batch_size):
                batch_end = min(batch_start + batch_size, len(fa25_ssc_dim_product))
                batch = fa25_ssc_dim_product.iloc[batch_start:batch_end]
                
                values_list = []
                params = []
                for _, row in batch.iterrows():
                    values_list.append("(%s, %s, %s, %s, %s, NOW(), NOW())")
                    params.extend([
                        int(row.get('product_key', 0)),
                        str(row.get('product_id', None)) if row.get('product_id') is not None else None,
                        row.get('product_name', None),
                        row.get('category_name', None),
                        row.get('subcategory_name', None)
                    ])
                
                sql = f"""
                INSERT INTO fa25_ssc_dim_product 
                (product_key, product_id, product_name, category_name, subcategory_name, created_at, updated_at)
                VALUES {','.join(values_list)}
                ON DUPLICATE KEY UPDATE
                product_name = VALUES(product_name),
                category_name = VALUES(category_name),
                subcategory_name = VALUES(subcategory_name),
                updated_at = NOW()
                """
                cursor.execute(sql, params)
                product_inserted += len(batch)
            conn.commit()
        logger.info(f"fa25_ssc_dim_product loaded: {product_inserted} records (inserts + updates)")
        
        # Load fa25_ssc_dim_return with CDC deduplication
        logger.info("Loading fa25_ssc_dim_return with CDC deduplication...")
        fa25_ssc_dim_return = transformed_data['fa25_ssc_dim_return']
        return_inserted = 0
        if len(fa25_ssc_dim_return) > 0:
            # Batch insert
            batch_size = 1000
            for batch_start in range(0, len(fa25_ssc_dim_return), batch_size):
                batch_end = min(batch_start + batch_size, len(fa25_ssc_dim_return))
                batch = fa25_ssc_dim_return.iloc[batch_start:batch_end]
                
                values_list = []
                params = []
                for _, row in batch.iterrows():
                    values_list.append("(%s, %s, %s, %s, NOW(), NOW())")
                    params.extend([
                        int(row.get('return_key', 0)),
                        str(row.get('return_id', None)) if row.get('return_id') is not None else None,
                        row.get('return_status', None),
                        row.get('return_region', None)
                    ])
                
                sql = f"""
                INSERT INTO fa25_ssc_dim_return 
                (return_key, return_id, return_status, return_region, created_at, updated_at)
                VALUES {','.join(values_list)}
                ON DUPLICATE KEY UPDATE
                return_status = VALUES(return_status),
                return_region = VALUES(return_region),
                updated_at = NOW()
                """
                cursor.execute(sql, params)
                return_inserted += len(batch)
            conn.commit()
        logger.info(f"fa25_ssc_dim_return loaded: {return_inserted} records (inserts + updates)")
        
        # ===== LOAD FACTS =====
        # Facts use surrogate keys, so each CDC change creates a new fact record
        # This preserves the audit trail and handles stock adjustments correctly
        
        # Load fa25_ssc_fact_sales
        logger.info("Loading fa25_ssc_fact_sales (CDC incremental)...")
        fa25_ssc_fact_sales = transformed_data['fa25_ssc_fact_sales']
        sales_inserted = 0
        if len(fa25_ssc_fact_sales) > 0:
            # Batch insert for facts (faster)
            batch_size = 1000
            for batch_start in range(0, len(fa25_ssc_fact_sales), batch_size):
                batch_end = min(batch_start + batch_size, len(fa25_ssc_fact_sales))
                batch = fa25_ssc_fact_sales.iloc[batch_start:batch_end]
                
                values_list = []
                params = []
                for _, row in batch.iterrows():
                    values_list.append("(%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())")
                    params.extend([
                        int(row.get('customer_key', 0)),
                        int(row.get('product_key', 0)),
                        int(row.get('date_key', 0)),
                        int(row.get('return_key', 0)) if pd.notna(row.get('return_key')) else None,
                        float(row.get('sales', 0)),
                        int(row.get('quantity', 0)),
                        float(row.get('discount', 0)),
                        float(row.get('profit', 0)),
                        float(row.get('shipping_cost', 0))
                    ])
                
                sql = f"""
                INSERT INTO fa25_ssc_fact_sales 
                (customer_key, product_key, date_key, return_key, 
                 sales, quantity, discount, profit, shipping_cost, created_at, updated_at)
                VALUES {','.join(values_list)}
                """
                cursor.execute(sql, params)
                sales_inserted += len(batch)
            conn.commit()
        logger.info(f"fa25_ssc_fact_sales loaded: {sales_inserted} records (CDC incremental)")
        
        # Load fa25_ssc_fact_return
        logger.info("Loading fa25_ssc_fact_return (CDC incremental)...")
        fa25_ssc_fact_return = transformed_data['fa25_ssc_fact_return']
        return_facts_inserted = 0
        if len(fa25_ssc_fact_return) > 0:
            # Batch insert for facts
            batch_size = 1000
            for batch_start in range(0, len(fa25_ssc_fact_return), batch_size):
                batch_end = min(batch_start + batch_size, len(fa25_ssc_fact_return))
                batch = fa25_ssc_fact_return.iloc[batch_start:batch_end]
                
                values_list = []
                params = []
                for _, row in batch.iterrows():
                    values_list.append("(%s, %s, %s, %s, %s, %s, NOW(), NOW())")
                    params.extend([
                        int(row.get('return_key', 0)),
                        row.get('order_key', None),
                        int(row.get('customer_key', 0)),
                        int(row.get('date_key', 0)),
                        row.get('return_status', None),
                        row.get('return_region', None)
                    ])
                
                sql = f"""
                INSERT INTO fa25_ssc_fact_return 
                (return_key, order_key, customer_key, date_key, return_status, return_region, created_at, updated_at)
                VALUES {','.join(values_list)}
                """
                cursor.execute(sql, params)
                return_facts_inserted += len(batch)
            conn.commit()
        logger.info(f"fa25_ssc_fact_return loaded: {return_facts_inserted} records (CDC incremental)")
        
        cursor.close()
        conn.close()
        
        logger.info("=" * 80)
        logger.info("LOAD Phase completed successfully (6 OLAP tables loaded)")
        logger.info(f"Summary: Dimensions upserted, Facts inserted (CDC audit trail preserved)")
        logger.info(f"  fa25_ssc_dim_date: {date_inserted} | fa25_ssc_dim_customer: {customer_inserted} | fa25_ssc_dim_product: {product_inserted} | fa25_ssc_dim_return: {return_inserted}")
        logger.info(f"  fa25_ssc_fact_sales: {sales_inserted} | fa25_ssc_fact_return: {return_facts_inserted}")
        logger.info("=" * 80)
        return True
    
    except Exception as e:
        logger.error(f"Error in LOAD phase: {e}")
        return False


def log_etl_run(config: Dict, status: str, records_processed: int) -> None:
    """
    Log ETL run metadata to FA25_SSC_ETL_LOG for CDC tracking
    
    This enables future incremental loads by storing:
    - etl_run_time: When this run completed
    - status: SUCCESS or FAILED
    - records_processed: How many records were processed
    
    Args:
        config: Configuration dictionary
        status: 'SUCCESS' or 'FAILED'
        records_processed: Number of records processed
    """
    logger.info("Logging ETL run metadata for CDC tracking...")
    success = save_etl_run_metadata(config, status, records_processed)
    
    if success:
        logger.info(f"CDC: ETL run logged - Status: {status}, Records: {records_processed}")
    else:
        logger.error("CDC: Failed to log ETL run metadata")


# ============================================================================
# MAIN ETL ORCHESTRATION
# ============================================================================

def run_etl_pipeline(config: Dict = None) -> bool:
    """
    Main ETL pipeline orchestration function with CDC support
    
    INCREMENTAL LOAD WORKFLOW:
    1. Get last successful ETL run timestamp from FA25_SSC_ETL_LOG
    2. Extract only records changed since last run (CDC via TBL_LAST_DT)
    3. Transform to star schema (denormalize)
    4. Load into MySQL DW
    5. Log this run to FA25_SSC_ETL_LOG for next incremental load
    
    CDC FLOW:
    Data Entry → TBL_SALES (TBL_LAST_DT = NOW())
           ↓
    Database Trigger (sets TBL_LAST_DT)
           ↓
    ETL queries: SELECT WHERE TBL_LAST_DT > last_run
           ↓
    Only changed records extracted (incremental!)
           ↓
    Load to DW, store run_time in FA25_SSC_ETL_LOG
           ↓
    Next run uses new timestamp for efficient incremental load
    
    Args:
        config: Configuration dictionary (loads from env.yaml if None)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if config is None:
            config = load_env_config()
        
        start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("ETL PIPELINE STARTED - CDC-Based Incremental Load")
        logger.info(f"Start time: {start_time}")
        logger.info("=" * 80)
        
        # Step 1: Get last ETL timestamp (CDC tracking)
        logger.info("Step 1/5: CDC - Getting last ETL run timestamp")
        last_timestamp = get_last_etl_timestamp(config)
        logger.info(f"CDC: Last successful ETL: {last_timestamp}")
        
        # Step 2: Extract from OLTP using CDC
        logger.info("Step 2/5: CDC-Based EXTRACT - Getting changed records from OLTP (8 tables)")
        extracted_data = extract_from_oltp(config, last_timestamp)
        total_changes = len(extracted_data['orders']) + len(extracted_data['order_product']) + len(extracted_data['returns'])
        logger.info(f"CDC: Extracted {total_changes} changed records from 8 OLTP tables")
        
        # Step 3: Transform to star schema
        logger.info("Step 3/5: TRANSFORM - Denormalizing to 6-table OLAP star schema")
        transformed_data = transform_to_star_schema(extracted_data)
        logger.info(f"Transform: Created 6 OLAP tables (fa25_ssc_dim_date, fa25_ssc_dim_customer, fa25_ssc_dim_product, fa25_ssc_dim_return, fa25_ssc_fact_sales, fa25_ssc_fact_return)")
        
        # Step 4: Load into DW
        logger.info("Step 4/5: LOAD - Writing to MySQL DW")
        load_success = load_to_dw(config, transformed_data)
        
        if not load_success:
            logger.error("LOAD FAILED - ETL pipeline aborted")
            log_etl_run(config, 'FAILED', 0)
            return False
        
        # Step 5: Log the run (for next incremental load)
        logger.info("Step 5/5: CDC - Logging ETL run for next incremental load")
        total_records = len(transformed_data['fa25_ssc_fact_sales'])
        log_etl_run(config, 'SUCCESS', total_records)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"End time: {end_time}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Records processed: {total_records}")
        logger.info(f"OLTP Tables extracted: 8 (SEGMENT, CATEGORY, SUBCATEGORY, PRODUCT, CUSTOMER, ORDER, ORDER_PRODUCT, RETURN)")
        logger.info(f"OLAP Tables loaded: 6 (fa25_ssc_dim_date, fa25_ssc_dim_customer, fa25_ssc_dim_product, fa25_ssc_dim_return, fa25_ssc_fact_sales, fa25_ssc_fact_return)")
        logger.info(f"Next incremental load will fetch records after: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        return True
    
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"ETL PIPELINE FAILED: {e}")
        logger.error("=" * 80)
        log_etl_run(config, 'FAILED', 0)
        return False


# ============================================================================
# UTILITY FUNCTION FOR MANUAL RUNS
# ============================================================================

if __name__ == "__main__":
    """
    Run ETL pipeline manually
    
    Usage: python etl_pipeline.py
    """
    config = load_env_config()
    success = run_etl_pipeline(config)
    
    if success:
        print("ETL Pipeline completed successfully!")
    else:
        print("ETL Pipeline failed!")


