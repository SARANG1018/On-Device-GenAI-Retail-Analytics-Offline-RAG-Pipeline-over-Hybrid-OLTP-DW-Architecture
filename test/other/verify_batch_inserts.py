#!/usr/bin/env python3
"""
Verify batch insert data integrity - compare OLTP source vs DW loaded
"""

from src.utils import load_env_config, get_postgres_connection, get_mysql_connection, release_postgres_connection

config = load_env_config()

# Get OLTP counts
pg_conn = get_postgres_connection(config)
pg_cursor = pg_conn.cursor()

print('DATA INTEGRITY VERIFICATION')
print('=' * 60)
print()

# OLTP Source counts
print('OLTP Source (PostgreSQL):')
print('-' * 60)
pg_cursor.execute('SELECT COUNT(*) FROM "FA25_SSC_CUSTOMER"')
customer_count = pg_cursor.fetchone()[0]
print(f'CUSTOMER table:           {customer_count:>10,}')

pg_cursor.execute('SELECT COUNT(*) FROM "FA25_SSC_PRODUCT"')
product_count = pg_cursor.fetchone()[0]
print(f'PRODUCT table:            {product_count:>10,}')

pg_cursor.execute('SELECT COUNT(*) FROM "FA25_SSC_ORDER"')
order_count = pg_cursor.fetchone()[0]
print(f'ORDER table:              {order_count:>10,}')

pg_cursor.execute('SELECT COUNT(*) FROM "FA25_SSC_ORDER_PRODUCT"')
order_product_count = pg_cursor.fetchone()[0]
print(f'ORDER_PRODUCT (line items):{order_product_count:>9,}')

pg_cursor.execute('SELECT COUNT(*) FROM "FA25_SSC_RETURN"')
return_count = pg_cursor.fetchone()[0]
print(f'RETURN table:             {return_count:>10,}')

pg_cursor.close()

# DW counts
print()
print('DW Loaded (MySQL):')
print('-' * 60)
mysql_conn = get_mysql_connection(config)
mysql_cursor = mysql_conn.cursor()

mysql_cursor.execute('SELECT COUNT(*) FROM fa25_ssc_dim_customer')
fa25_ssc_dim_customer = mysql_cursor.fetchone()[0]
print(f'fa25_ssc_dim_customer:             {fa25_ssc_dim_customer:>10,}')

mysql_cursor.execute('SELECT COUNT(*) FROM fa25_ssc_dim_product')
fa25_ssc_dim_product = mysql_cursor.fetchone()[0]
print(f'fa25_ssc_dim_product:              {fa25_ssc_dim_product:>10,}')

mysql_cursor.execute('SELECT COUNT(*) FROM fa25_ssc_fact_sales')
fa25_ssc_fact_sales = mysql_cursor.fetchone()[0]
print(f'fa25_ssc_fact_sales:               {fa25_ssc_fact_sales:>10,}')

mysql_cursor.execute('SELECT COUNT(*) FROM fa25_ssc_fact_return')
fa25_ssc_fact_return = mysql_cursor.fetchone()[0]
print(f'fa25_ssc_fact_return:              {fa25_ssc_fact_return:>10,}')

mysql_cursor.close()
mysql_conn.close()

print()
print('MATCH CHECK:')
print('-' * 60)
c_match = 'MATCH' if customer_count == fa25_ssc_dim_customer else 'MISMATCH'
p_match = 'MATCH' if product_count == fa25_ssc_dim_product else 'MISMATCH'
o_match = 'MATCH' if order_product_count == fa25_ssc_fact_sales else 'MISMATCH'
r_match = 'MATCH' if return_count == fa25_ssc_fact_return else 'MISMATCH'

print(f'CUSTOMER → fa25_ssc_dim_customer:       {customer_count:>10,} → {fa25_ssc_dim_customer:>10,}  {c_match}')
print(f'PRODUCT  → fa25_ssc_dim_product:        {product_count:>10,} → {fa25_ssc_dim_product:>10,}  {p_match}')
print(f'ORDER_PRODUCT → fa25_ssc_fact_sales:    {order_product_count:>10,} → {fa25_ssc_fact_sales:>10,}  {o_match}')
print(f'RETURN   → fa25_ssc_fact_return:        {return_count:>10,} → {fa25_ssc_fact_return:>10,}  {r_match}')

all_match = all([customer_count == fa25_ssc_dim_customer, product_count == fa25_ssc_dim_product, 
                 order_product_count == fa25_ssc_fact_sales, return_count == fa25_ssc_fact_return])
print()
print('=' * 60)
if all_match:
    print('NO DATA LOSS DETECTED - All batch inserts successful!')
else:
    print('WARNING: Data mismatch detected - investigate before proceeding')



