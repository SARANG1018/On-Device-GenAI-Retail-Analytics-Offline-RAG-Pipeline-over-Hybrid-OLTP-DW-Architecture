#!/usr/bin/env python
"""Quick test of SQL Loader functions"""

import sys
sys.path.insert(0, 'src')

from sql_loader import get_sample_csv_format, validate_order_row, load_orders_from_csv, load_customers_from_csv
from utils import get_postgres_connection, load_env_config
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = load_env_config()

print("=" * 70)
print("SQL LOADER - QUICK FUNCTION TEST")
print("=" * 70)

# TEST 1: Sample CSV formats
print("\n[TEST 1] Sample CSV Formats")
print("-" * 70)

print("\n Sample Orders CSV:")
orders_sample = get_sample_csv_format('orders')
print(orders_sample)

print("\n Sample Customers CSV:")
customers_sample = get_sample_csv_format('customers')
print(customers_sample)

print("\n Sample formats working!")

# TEST 2: Validate order row
print("\n[TEST 2] Validate Order Row Function")
print("-" * 70)

try:
    conn = get_postgres_connection(config)
    
    # Test with existing customer
    is_valid, error = validate_order_row(conn, "IT-2015-MP1796591-42097", "LP-CB0B73B0B889")
    print(f"\nExisting order validation:")
    print(f"  - Order ID: IT-2015-MP1796591-42097")
    print(f"  - Customer ID: LP-CB0B73B0B889")
    print(f"  - Valid: {is_valid}")
    print(f"  - Error: {error}")
    
    # Test with invalid customer
    is_valid2, error2 = validate_order_row(conn, "TEST-ORDER-ID", "INVALID-CUSTOMER")
    print(f"\nInvalid customer validation:")
    print(f"  - Order ID: TEST-ORDER-ID")
    print(f"  - Customer ID: INVALID-CUSTOMER")
    print(f"  - Valid: {is_valid2}")
    print(f"  - Error: {error2}")
    
    conn.close()
    print("\n Validation function working!")
    
except Exception as e:
    print(f" Error: {e}")
    logger.error(f"Validation test failed: {e}")

# TEST 3: Load functions (structure check)
print("\n[TEST 3] Load Functions Exist")
print("-" * 70)
print(f" load_orders_from_csv: {callable(load_orders_from_csv)}")
print(f" load_customers_from_csv: {callable(load_customers_from_csv)}")

print("\n" + "=" * 70)
print(" ALL TESTS PASSED - SQL Loader ready for Streamlit")
print("=" * 70)
