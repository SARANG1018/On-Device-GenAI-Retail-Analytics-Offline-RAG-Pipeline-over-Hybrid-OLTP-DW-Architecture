"""
Test Suite for PII Masking - Customer Data

Tests masking for customer_name and postal_code fields only.
These are the ONLY fields masked in production.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pii_masking import PIIMasking
import pandas as pd


def test_mask_customer_name():
    """Test customer name masking"""
    print("\n[TEST 1] Customer Name Masking...")
    
    assert PIIMasking.mask_name("John Doe") == "J*** D**"
    assert PIIMasking.mask_name("Alice Smith") == "A**** S****"
    assert PIIMasking.mask_name("Bob") == "B**"
    assert PIIMasking.mask_name("Mary Johnson") == "M*** J******"
    
    assert PIIMasking.mask_name("John Doe", PIIMasking.LEVEL_FULL) == "****"
    assert PIIMasking.mask_name("John Doe", PIIMasking.LEVEL_SHOW_LAST) == "J*** Doe"
    
    assert PIIMasking.mask_name("") == "***"
    assert PIIMasking.mask_name(None) == "***"
    assert PIIMasking.mask_name("   ") == "***"
    
    print("[PASS] Customer name masking works correctly")
    return True


def test_mask_postal_code():
    """Test postal code masking"""
    print("\n[TEST 2] Postal Code Masking...")
    
    assert PIIMasking.mask_postal_code("12345") == "123**"
    assert PIIMasking.mask_postal_code("67890") == "678**"
    assert PIIMasking.mask_postal_code("90210") == "902**"
    assert PIIMasking.mask_postal_code("AB12CD") == "AB1***"
    
    assert PIIMasking.mask_postal_code("123") == "***"
    assert PIIMasking.mask_postal_code("12") == "**"
    
    assert PIIMasking.mask_postal_code("") == "*****"
    assert PIIMasking.mask_postal_code(None) == "*****"
    
    print("[PASS] Postal code masking works correctly")
    return True




def test_get_default_mappings():
    """Test that production masks only customer_name and postal_code"""
    print("\n[TEST 3] Production Masking Mappings...")
    
    customer_map = PIIMasking.get_default_mappings_for_table('customer')
    assert len(customer_map) == 2, "Customer table should mask only 2 fields"
    assert customer_map['customer_name'] == 'name'
    assert customer_map['postal_code'] == 'postal_code'
    
    order_map = PIIMasking.get_default_mappings_for_table('order')
    assert len(order_map) == 0, "Order table should have no PII masking"
    
    product_map = PIIMasking.get_default_mappings_for_table('product')
    assert len(product_map) == 0, "Product table should have no PII masking"
    
    return_map = PIIMasking.get_default_mappings_for_table('return')
    assert len(return_map) == 0, "Return table should have no PII masking"
    
    print("[PASS] Production mappings correct - only customer_name and postal_code")
    return True


def test_dataframe_customer_masking():
    """Test DataFrame masking for customer data"""
    print("\n[TEST 4] DataFrame Masking - Customer Data...")
    
    try:
        df = pd.DataFrame({
            'customer_id': ['C001', 'C002', 'C003'],
            'customer_name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'postal_code': ['12345', '67890', '54321'],
            'segment': ['Consumer', 'Corporate', 'Home Office']
        })
        
        mappings = {
            'customer_name': 'name',
            'postal_code': 'postal_code'
        }
        
        masked_df = PIIMasking.mask_dataframe(df, mappings)
        
        assert masked_df['customer_name'].iloc[0] == 'J*** D**'
        assert masked_df['postal_code'].iloc[0] == '123**'
        assert masked_df['customer_id'].iloc[0] == 'C001'
        assert masked_df['segment'].iloc[0] == 'Consumer'
        
        assert df['customer_name'].iloc[0] == 'John Doe'
        
        print("[PASS] DataFrame customer masking works correctly")
        return True
    
    except ImportError:
        print("[SKIP] pandas not available - skipping")
        return True


def test_dict_customer_masking():
    """Test dictionary masking for customer data"""
    print("\n[TEST 5] Dictionary Masking - Customer Data...")
    
    data = {
        'customer_id': 'C001',
        'customer_name': 'Alice Cooper',
        'postal_code': '90210',
        'city': 'Beverly Hills'
    }
    
    mappings = {
        'customer_name': 'name',
        'postal_code': 'postal_code'
    }
    
    masked = PIIMasking.mask_dict(data, mappings)
    
    assert masked['customer_name'] == 'A**** C*****'
    assert masked['postal_code'] == '902**'
    assert masked['city'] == 'Beverly Hills'
    assert data['customer_name'] == 'Alice Cooper'
    
    print("[PASS] Dictionary customer masking works correctly")
    return True


def test_masking_consistency():
    """Test consistency of masking"""
    print("\n[TEST 6] Masking Consistency...")
    
    name1 = PIIMasking.mask_name("Robert Parker")
    name2 = PIIMasking.mask_name("Robert Parker")
    assert name1 == name2, "Same name should produce same mask"
    
    postal1 = PIIMasking.mask_postal_code("50505")
    postal2 = PIIMasking.mask_postal_code("50505")
    assert postal1 == postal2, "Same postal code should produce same mask"
    
    print("[PASS] Masking consistency verified")
    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PII MASKING TEST SUITE")
    print("Production: Masks customer_name and postal_code only")
    print("="*70)
    
    try:
        results = []
        results.append(("Customer Name Masking", test_mask_customer_name()))
        results.append(("Postal Code Masking", test_mask_postal_code()))
        results.append(("Production Mappings", test_get_default_mappings()))
        results.append(("DataFrame Masking", test_dataframe_customer_masking()))
        results.append(("Dictionary Masking", test_dict_customer_masking()))
        results.append(("Consistency Check", test_masking_consistency()))
        
        print("\n" + "="*70)
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"RESULTS: {passed}/{total} tests passed")
        print("="*70)
        
        print("\nPII Masking Configuration:")
        print("   • Customer table: Masks customer_name, postal_code")
        print("   • Order table: No masking")
        print("   • Return table: No masking")
        print("   • Product table: No masking")
        print("   • Category table: No masking")
        print("   • Subcategory table: No masking")
        print("   • Segment table: No masking")
        
        if passed == total:
            print("\n[SUCCESS] All tests passed")
        else:
            print(f"\n[FAILED] {total - passed} test(s) failed")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n[ERROR] TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70)
        sys.exit(1)




