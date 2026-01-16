#!/usr/bin/env python3
import psycopg2
import mysql.connector
from src.utils import load_env_config

config = load_env_config()

# Check PostgreSQL
print("Checking PostgreSQL...")
try:
    pg_conn = psycopg2.connect(
        host=config['POSTGRES']['HOST'],
        port=config['POSTGRES']['PORT'],
        database=config['POSTGRES']['DB'],
        user=config['POSTGRES']['USER'],
        password=config['POSTGRES']['PASSWORD']
    )
    pg_cur = pg_conn.cursor()
    
    pg_cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='fa25_ssc_users_sales_associate')")
    users_exists = pg_cur.fetchone()[0]
    
    pg_cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='fa25_ssc_password_reset_tokens_sales')")
    tokens_exists = pg_cur.fetchone()[0]
    
    print(f"  fa25_ssc_users_sales_associate: {users_exists}")
    print(f"  fa25_ssc_password_reset_tokens_sales: {tokens_exists}")
    
    if users_exists:
        pg_cur.execute("SELECT COUNT(*) FROM fa25_ssc_users_sales_associate")
        count = pg_cur.fetchone()[0]
        print(f"  fa25_ssc_users_sales_associate row count: {count}")
    
    pg_cur.close()
    pg_conn.close()
except Exception as e:
    print(f"  ERROR: {e}")

# Check MySQL
print("\nChecking MySQL...")
try:
    mysql_conn = mysql.connector.connect(
        host=config['MYSQL']['HOST'],
        port=config['MYSQL']['PORT'],
        database=config['MYSQL']['DB'],
        user=config['MYSQL']['USER'],
        password=config['MYSQL']['PASSWORD']
    )
    mysql_cur = mysql_conn.cursor()
    
    mysql_cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='fa25_ssc_users_store_manager')")
    store_mgr_exists = mysql_cur.fetchone()[0]
    
    mysql_cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='fa25_ssc_users_executive')")
    exec_exists = mysql_cur.fetchone()[0]
    
    print(f"  fa25_ssc_users_store_manager: {bool(store_mgr_exists)}")
    print(f"  fa25_ssc_users_executive: {bool(exec_exists)}")
    
    if store_mgr_exists:
        mysql_cur.execute("SELECT COUNT(*) FROM fa25_ssc_users_store_manager")
        count = mysql_cur.fetchone()[0]
        print(f"  fa25_ssc_users_store_manager row count: {count}")
    
    if exec_exists:
        mysql_cur.execute("SELECT COUNT(*) FROM fa25_ssc_users_executive")
        count = mysql_cur.fetchone()[0]
        print(f"  fa25_ssc_users_executive row count: {count}")
    
    mysql_cur.close()
    mysql_conn.close()
except Exception as e:
    print(f"  ERROR: {e}")



