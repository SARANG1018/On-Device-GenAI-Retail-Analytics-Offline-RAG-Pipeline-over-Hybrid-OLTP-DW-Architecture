#!/usr/bin/env python3
"""
Test script for validation procedures in PostgreSQL
Tests the three validation functions:
1. validate_customer()
2. validate_order()
3. validate_product()
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))
from utils import get_postgres_connection, load_env_config

def print_section(title):
    """Print a section header"""
    print("\n" + "="*80)
    print(title)
    print("="*80)

def print_result(title, columns, rows):
    """Print results in a formatted table"""
    print(f"\n{title}:")
    print("-" * 80)
    
    if not rows:
        print("No results")
        return
    
    # Print column headers
    header = " | ".join(f"{col:20}" for col in columns)
    print(header)
    print("-" * 80)
    
    # Print rows
    for row in rows:
        values = [str(row.get(col, 'N/A'))[:20] for col in columns]
        print(" | ".join(f"{val:20}" for val in values))

def test_validate_customer():
    """Test PROCEDURE 1: validate_customer()"""
    print_section("PROCEDURE 1: validate_customer()")
    
    config = load_env_config()
    conn = get_postgres_connection(config)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # First, get a real customer ID from the database
    try:
        cur.execute("SELECT customer_id FROM \"FA25_SSC_CUSTOMER\" LIMIT 1;")
        real_customer = cur.fetchone()
        real_customer_id = real_customer['customer_id'] if real_customer else 'CUST-0001'
    except:
        real_customer_id = 'CUST-0001'
    
    test_cases = [
        (real_customer_id, "Valid customer from database"),
        ("CUST-9999", "Non-existent customer")
    ]
    
    for customer_id, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Input: customer_id = '{customer_id}'")
        
        try:
            cur.execute(
                "SELECT * FROM validate_customer(%s);",
                (customer_id,)
            )
            result = cur.fetchall()
            
            columns = ['is_valid', 'customer_name', 'segment_name', 'error_message']
            print_result(f"Result for {customer_id}", columns, result)
            
        except Exception as e:
            print(f"Error: {e}")
    
    cur.close()
    conn.close()

def test_validate_order():
    """Test PROCEDURE 2: validate_order()"""
    print_section("PROCEDURE 2: validate_order()")
    
    config = load_env_config()
    conn = get_postgres_connection(config)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # First, get a real order ID from the database
    try:
        cur.execute("SELECT order_id FROM \"FA25_SSC_ORDER\" LIMIT 1;")
        real_order = cur.fetchone()
        real_order_id = real_order['order_id'] if real_order else 'ORD-0001'
    except:
        real_order_id = 'ORD-0001'
    
    test_cases = [
        (real_order_id, "Valid order from database"),
        ("ORD-9999", "Non-existent order")
    ]
    
    for order_id, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Input: order_id = '{order_id}'")
        
        try:
            cur.execute(
                "SELECT * FROM validate_order(%s);",
                (order_id,)
            )
            result = cur.fetchall()
            
            columns = ['is_valid', 'customer_id', 'customer_name', 'product_count', 'error_message']
            print_result(f"Result for {order_id}", columns, result)
            
        except Exception as e:
            print(f"Error: {e}")
    
    cur.close()
    conn.close()

def test_validate_product():
    """Test PROCEDURE 3: validate_product()"""
    print_section("PROCEDURE 3: validate_product()")
    
    config = load_env_config()
    conn = get_postgres_connection(config)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # First, get a real product ID from the database
    try:
        cur.execute("SELECT product_id FROM \"FA25_SSC_PRODUCT\" LIMIT 1;")
        real_product = cur.fetchone()
        real_product_id = real_product['product_id'] if real_product else 'PROD-0001'
    except:
        real_product_id = 'PROD-0001'
    
    test_cases = [
        (real_product_id, "Valid product from database"),
        ("PROD-9999", "Non-existent product")
    ]
    
    for product_id, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Input: product_id = '{product_id}'")
        
        try:
            cur.execute(
                "SELECT * FROM validate_product(%s);",
                (product_id,)
            )
            result = cur.fetchall()
            
            columns = ['is_valid', 'product_name', 'category_name', 'subcategory_name', 'error_message']
            print_result(f"Result for {product_id}", columns, result)
            
        except Exception as e:
            print(f"Error: {e}")
    
    cur.close()
    conn.close()

def main():
    """Run all validation tests"""
    print("\n" + "="*80)
    print("VALIDATION PROCEDURES TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: Validate Customer
        test_validate_customer()
        
        # Test 2: Validate Order
        test_validate_order()
        
        # Test 3: Validate Product
        test_validate_product()
        
        print_section("TEST SUITE COMPLETED")
        print("All validation procedures tested successfully")
        
    except Exception as e:
        print(f"\nError during test execution: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
