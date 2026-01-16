import sys
sys.path.insert(0, 'src')
import psycopg2
from utils import load_env_config

config = load_env_config()
postgres_config = config.get('POSTGRES', {})

conn = psycopg2.connect(
    host=postgres_config.get('HOST', 'localhost'),
    port=postgres_config.get('PORT', 5432),
    database=postgres_config.get('DB', 'awesome_inc_oltp'),
    user=postgres_config.get('USER', 'postgres'),
    password=postgres_config.get('PASSWORD', '')
)
cursor = conn.cursor()

try:
    print("Cleaning up test data loaded today...")
    
    # Delete RETURN records for TEST orders FIRST (they have FK to orders)
    cursor.execute('''
        DELETE FROM "FA25_SSC_RETURN" 
        WHERE order_id LIKE 'TEST-%'
    ''')
    deleted_returns = cursor.rowcount
    print(f"✓ Deleted {deleted_returns} RETURN records")
    
    # Delete ORDER_PRODUCT records for TEST orders
    cursor.execute('''
        DELETE FROM "FA25_SSC_ORDER_PRODUCT" 
        WHERE order_id LIKE 'TEST-%'
    ''')
    deleted_products = cursor.rowcount
    print(f"✓ Deleted {deleted_products} ORDER_PRODUCT records")
    
    # Delete ORDER records for TEST orders LAST
    cursor.execute('''
        DELETE FROM "FA25_SSC_ORDER" 
        WHERE order_id LIKE 'TEST-%'
    ''')
    deleted_orders = cursor.rowcount
    print(f"✓ Deleted {deleted_orders} ORDER records")
    
    conn.commit()
    print("\n✅ Cleanup completed successfully!")
    print(f"   Total records deleted: {deleted_products + deleted_orders + deleted_returns}")
    print("\nTest data is now clean. Ready for fresh SQL Loader testing!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
