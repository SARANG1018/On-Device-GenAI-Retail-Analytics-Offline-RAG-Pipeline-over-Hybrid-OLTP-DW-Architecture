import logging
import pandas as pd
from typing import Dict
from utils import get_postgres_connection, release_postgres_connection, load_env_config

logger = logging.getLogger(__name__)

# Orders + Products Loader
def load_orders_with_products(csv_data: pd.DataFrame) -> Dict:
    config = load_env_config()
    conn = get_postgres_connection(config)
    
    results = {
        'total_rows': len(csv_data),
        'orders_loaded': 0,
        'products_loaded': 0,
        'errors': []
    }
    
    try:
        if len(csv_data) == 0:
            results['errors'].append("CSV file is empty")
            return results
        
        logger.info(f"Loading {len(csv_data)} order+product rows...")
        
        cursor = conn.cursor()
        
        # Process each row - insert order if new, then insert product
        for idx, row in csv_data.iterrows():
            try:
                # Create savepoint for this row to avoid transaction abort
                savepoint_name = f"sp_row_{idx}"
                cursor.execute(f"SAVEPOINT {savepoint_name}")
                
                order_id = str(row.get('order_id', ''))
                customer_id = str(row.get('customer_id', ''))
                order_date = str(row.get('order_date', ''))
                order_priority = str(row.get('order_priority', 'Not Specified'))
                
                # Check if order already exists
                cursor.execute(
                    'SELECT order_id FROM "FA25_SSC_ORDER" WHERE order_id = %s',
                    (order_id,)
                )
                order_exists = cursor.fetchone() is not None
                
                # Insert ORDER if new
                if not order_exists:
                    cursor.execute(
                        '''INSERT INTO "FA25_SSC_ORDER" 
                           (order_id, customer_id, order_date, order_priority)
                           VALUES (%s, %s, %s, %s)''',
                        (order_id, customer_id, order_date, order_priority)
                    )
                    results['orders_loaded'] += 1
                    logger.debug(f"Inserted order: {order_id}")
                
                # Insert PRODUCT/ORDER_PRODUCT
                product_id = str(row.get('product_id', ''))
                sales = float(row.get('sales_amount', 0))  # Map sales_amount to sales column
                quantity = int(row.get('quantity', 1))
                discount = float(row.get('discount', 0))
                shipping_cost = float(row.get('shipping_cost', 0))
                ship_date = str(row.get('ship_date', order_date))
                ship_mode = str(row.get('ship_mode', 'Standard Class'))
                
                # Calculate profit: sales * (1 - discount) - shipping_cost
                profit = (sales * (1 - discount)) - shipping_cost
                
                cursor.execute(
                    '''INSERT INTO "FA25_SSC_ORDER_PRODUCT"
                       (order_id, product_id, quantity, sales, discount, profit,
                        shipping_cost, ship_date, ship_mode)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (order_id, product_id, quantity, sales, discount, profit,
                     shipping_cost, ship_date, ship_mode)
                )
                results['products_loaded'] += 1
                logger.debug(f"Inserted product for order: {order_id}")
                
            except Exception as e:
                error_msg = f"Row {idx+1}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                try:
                    cursor.execute(f"ROLLBACK TO {savepoint_name}")
                except:
                    pass
        
        conn.commit()
        logger.info(f"Loaded {results['orders_loaded']} orders, {results['products_loaded']} products")
        
        cursor.close()
        return results
        
    except Exception as e:
        conn.rollback()
        error_msg = f"SQL Loader error: {str(e)}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        return results
    
    finally:
        release_postgres_connection(conn)


def load_returns_from_csv(csv_data: pd.DataFrame) -> Dict:
    """
    Bulk load returns from CSV
    Columns: returned, order_id, return_date, region
    
    Args:
        csv_data: DataFrame with return data
    
    Returns:
        Dictionary with results
    """
    config = load_env_config()
    conn = get_postgres_connection(config)
    
    results = {
        'total_rows': len(csv_data),
        'loaded_rows': 0,
        'errors': []
    }
    
    try:
        if len(csv_data) == 0:
            results['errors'].append("CSV file is empty")
            return results
        
        logger.info(f"Loading {len(csv_data)} returns...")
        
        cursor = conn.cursor()
        
        # Process each row with tbl_last_dt for CDC tracking
        for idx, row in csv_data.iterrows():
            try:
                import uuid
                return_id = f"RET-{uuid.uuid4().hex[:8].upper()}"  # Generate unique return_id
                return_status = str(row.get('return_status', 'No'))
                order_id = str(row.get('return_id', ''))  # CSV has return_id column which contains order_id
                return_region = str(row.get('return_region', ''))
                
                cursor.execute('''
                    INSERT INTO "FA25_SSC_RETURN" 
                    (return_id, return_status, order_id, return_region, tbl_last_dt)
                    VALUES (%s, %s, %s, %s, NOW())
                ''', (return_id, return_status, order_id, return_region))
                
                results['loaded_rows'] += 1
                logger.debug(f"Inserted return {return_id} for order: {order_id}")
                
            except Exception as e:
                error_msg = f"Row {idx+1}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        conn.commit()
        logger.info(f"Loaded {results['loaded_rows']} returns")
        
        cursor.close()
        return results
        
    except Exception as e:
        conn.rollback()
        error_msg = f"SQL Loader error: {str(e)}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        return results
    
    finally:
        release_postgres_connection(conn)


def get_sample_csv_format(data_type: str) -> str:
    """
    Get sample CSV format for users
    
    Args:
        data_type: 'orders' or 'returns'
    
    Returns:
        Sample CSV as string
    """
    if data_type == 'orders':
        return """order_id,customer_id,order_date,order_priority,category,product_name,sales_amount,quantity,discount,shipping_cost,ship_date,subcategory,ship_mode
ORD-20251213-001,LP-CB0B73B0B889,2025-12-13,High,Technology,Laptop,1299.99,1,0.1,50.00,2025-12-13,Computers,Standard Class
ORD-20251213-002,LP-A1C2F4E5D6G7,2025-12-13,Medium,Furniture,Desk Chair,299.99,2,0.05,25.00,2025-12-13,Chairs,Express Class
ORD-20251213-003,LP-H8I9J0K1L2M3,2025-12-13,Low,Office Supplies,Pen Pack,49.99,5,0.0,10.00,2025-12-13,Writing Instruments,Standard Class"""
    
    elif data_type == 'returns':
        return """returned,order_id,return_date,region
Yes,ORD-20251213-001,2025-12-13,Central US
Yes,ORD-20251213-002,2025-12-13,Eastern Asia
Yes,ORD-20251213-003,2025-12-13,Oceania"""
    
    return ""
    
    return ""
