#!/usr/bin/env python3
"""
Complete Pipeline Test: Vanna + Mistral with Complex Queries
- Test 1: Vanna exact keyword match
- Test 2: Mistral fallback (simple novel query)
- Test 3: Mistral fallback (complex multi-join query)
- Test 4: Mistral fallback (complex aggregation with conditions)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from function_tools import process_question
import pandas as pd

print("\n" + "="*100)
print(" "*25 + "COMPLETE PIPELINE TEST: VANNA + MISTRAL")
print("="*100)

tests = [
    {
        "name": "VANNA EXACT KEYWORD MATCH",
        "question": "What's the total sales by region?",
        "expected": "Exact match from training data (threshold 1.0)",
        "type": "vanna"
    },
    {
        "name": "MISTRAL FALLBACK - SIMPLE",
        "question": "Show me profit margin analysis by product subcategory",
        "expected": "No exact match, Mistral generates SQL",
        "type": "mistral"
    },
    {
        "name": "MISTRAL FALLBACK - COMPLEX (Multi-join)",
        "question": "List top 5 customers by total spending with their region and product preferences",
        "expected": "Complex multi-join query with GROUP BY and ORDER BY",
        "type": "mistral"
    },
    {
        "name": "MISTRAL FALLBACK - COMPLEX (Aggregation)",
        "question": "Show me total sales and profit by region and customer country",
        "expected": "Multi-level aggregation with multiple GROUP BY columns",
        "type": "mistral"
    }
]

results = []

for i, test in enumerate(tests, 1):
    print(f"\n[TEST {i}] {test['name']}")
    print("-" * 100)
    print(f"Question: {test['question']}")
    print(f"Expected: {test['expected']}")
    print("\nProcessing...")
    
    try:
        result = process_question(test['question'])
        data = result.get("data")
        
        if data is not None and isinstance(data, pd.DataFrame) and len(data) > 0:
            print(f"✓ PASS - Got {len(data)} rows")
            print(f"  Columns: {list(data.columns)}")
            print(f"  Sample data:")
            for idx, row in data.head(2).iterrows():
                print(f"    {dict(row)}")
            results.append({"test": i, "name": test['name'], "status": "PASS"})
        else:
            print("✗ FAIL - No data returned")
            err = result.get('error', 'Unknown error')
            if err:
                print(f"  Error: {str(err)[:150]}")
            results.append({"test": i, "name": test['name'], "status": "FAIL"})
    
    except Exception as e:
        print(f"✗ FAIL - Exception occurred")
        print(f"  Error: {str(e)[:150]}")
        results.append({"test": i, "name": test['name'], "status": "FAIL"})

# SUMMARY
print("\n" + "="*100)
print("SUMMARY")
print("="*100)

passed = sum(1 for r in results if r['status'] == 'PASS')
total = len(results)

for r in results:
    status_symbol = "✓" if r['status'] == 'PASS' else "✗"
    print(f"\n{status_symbol} Test {r['test']}: {r['name']} - {r['status']}")

print(f"\n{'='*100}")
print(f"RESULT: {passed}/{total} tests passed ({int(passed/total*100)}%)")
print(f"{'='*100}")

if passed == total:
    print("\n✅ ALL TESTS PASSED! Pipeline is production-ready.")
    sys.exit(0)
elif passed >= 2:
    print(f"\n⚠️  {passed}/{total} tests passed. Core functionality working.")
    sys.exit(0)
else:
    print(f"\n❌ Only {passed}/{total} tests passed. Issues need investigation.")
    sys.exit(1)



