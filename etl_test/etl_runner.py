#!/usr/bin/env python3
"""
ETL PIPELINE - PHASE BY PHASE RUNNER
Allows running Extract, Transform, Load phases independently
"""

import sys
sys.path.insert(0, 'src')

from etl_pipeline import (
    extract_from_oltp,
    transform_to_star_schema,
    load_to_dw,
    get_last_etl_timestamp
)
from utils import load_env_config, setup_logger
import pickle
import os
from datetime import datetime

# Setup logger
logger = setup_logger(__name__, log_file='logs/etl_runner.log')

config = load_env_config()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def save_phase_output(phase_name, data):
    """Save phase output to pickle file for next phase"""
    filename = f"phase_output_{phase_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    logger.info(f"[OK] Phase output saved: {filename}")
    return filename

def load_phase_output(filename):
    """Load phase output from pickle file"""
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    logger.info(f"[OK] Phase output loaded: {filename}")
    return data

# ============================================================================
# PHASE 1: EXTRACT
# ============================================================================

def run_extract_phase():
    """Extract changed data from PostgreSQL OLTP"""
    print("\n" + "="*80)
    print("PHASE 1: EXTRACT - CDC from PostgreSQL OLTP")
    print("="*80 + "\n")
    
    try:
        # Get last ETL timestamp (for incremental load)
        last_timestamp = get_last_etl_timestamp(config)
        logger.info(f"Using CDC timestamp: {last_timestamp}")
        
        # Extract from OLTP
        extracted_data = extract_from_oltp(config, last_timestamp)
        
        # Display summary
        print("\n" + "="*80)
        print("EXTRACT PHASE SUMMARY")
        print("="*80)
        print(f"[OK] SEGMENT records: {len(extracted_data['segment'])}")
        print(f"[OK] CATEGORY records: {len(extracted_data['category'])}")
        print(f"[OK] SUBCATEGORY records: {len(extracted_data['subcategory'])}")
        print(f"[OK] PRODUCT records: {len(extracted_data['products'])}")
        print(f"[OK] CUSTOMER records: {len(extracted_data['customers'])}")
        print(f"[OK] ORDER records (CDC): {len(extracted_data['orders'])}")
        print(f"[OK] ORDER_PRODUCT records (CDC): {len(extracted_data['order_product'])}")
        print(f"[OK] RETURN records (CDC): {len(extracted_data['returns'])}")
        print("="*80 + "\n")
        
        # Save output
        output_file = save_phase_output('extract', extracted_data)
        
        print(f"\n[FILE] EXTRACT phase output saved to: {output_file}")
        print("\nNext: Run TRANSFORM phase with this file\n")
        return extracted_data, output_file
        
    except Exception as e:
        logger.error(f"[ERROR] EXTRACT phase FAILED: {e}")
        raise

# ============================================================================
# PHASE 2: TRANSFORM
# ============================================================================

def run_transform_phase(extracted_data=None, input_file=None):
    """Transform normalized OLTP data to star schema"""
    print("\n" + "="*80)
    print("PHASE 2: TRANSFORM - Denormalize to OLAP Star Schema")
    print("="*80 + "\n")
    
    try:
        # Load data if not provided
        if extracted_data is None and input_file:
            extracted_data = load_phase_output(input_file)
        elif extracted_data is None:
            raise ValueError("No extracted data provided")
        
        # Transform to star schema
        transformed_data = transform_to_star_schema(extracted_data)
        
        # Display summary
        print("\n" + "="*80)
        print("TRANSFORM PHASE SUMMARY")
        print("="*80)
        print(f"[OK] DIM_DATE records: {len(transformed_data['dim_date'])}")
        print(f"[OK] DIM_CUSTOMER records: {len(transformed_data['dim_customer'])}")
        print(f"[OK] DIM_PRODUCT records: {len(transformed_data['dim_product'])}")
        print(f"[OK] DIM_RETURN records: {len(transformed_data['dim_return'])}")
        print(f"[OK] FACT_SALES records: {len(transformed_data['fact_sales'])}")
        print(f"[OK] FACT_RETURN records: {len(transformed_data['fact_return'])}")
        print("="*80 + "\n")
        
        # Save output
        output_file = save_phase_output('transform', transformed_data)
        
        print(f"\n[FILE] TRANSFORM phase output saved to: {output_file}")
        print("\nNext: Run LOAD phase with this file\n")
        return transformed_data, output_file
        
    except Exception as e:
        logger.error(f"[ERROR] TRANSFORM phase FAILED: {e}")
        raise

# ============================================================================
# PHASE 3: LOAD
# ============================================================================

def run_load_phase(transformed_data=None, input_file=None):
    """Load transformed data to MySQL OLAP warehouse"""
    print("\n" + "="*80)
    print("PHASE 3: LOAD - Insert into MySQL OLAP Warehouse")
    print("="*80 + "\n")
    
    try:
        # Load data if not provided
        if transformed_data is None and input_file:
            transformed_data = load_phase_output(input_file)
        elif transformed_data is None:
            raise ValueError("No transformed data provided")
        
        # Load to OLAP
        load_to_dw(config, transformed_data)
        
        print("\n" + "="*80)
        print("LOAD PHASE COMPLETED")
        print("="*80)
        print("[OK] Data successfully loaded to MySQL OLAP warehouse")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"[ERROR] LOAD phase FAILED: {e}")
        raise

# ============================================================================
# MAIN MENU
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("\n" + "="*80)
        print("ETL PIPELINE - PHASE BY PHASE RUNNER")
        print("="*80)
        print("\nUsage:")
        print("  python etl_runner.py extract              # Run EXTRACT phase")
        print("  python etl_runner.py transform [file]     # Run TRANSFORM phase (optionally from file)")
        print("  python etl_runner.py load [file]          # Run LOAD phase (optionally from file)")
        print("  python etl_runner.py full                 # Run all phases in sequence")
        print("="*80 + "\n")
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    try:
        if command == 'extract':
            run_extract_phase()
        
        elif command == 'transform':
            input_file = sys.argv[2] if len(sys.argv) > 2 else None
            run_transform_phase(input_file=input_file)
        
        elif command == 'load':
            input_file = sys.argv[2] if len(sys.argv) > 2 else None
            run_load_phase(input_file=input_file)
        
        elif command == 'full':
            print("\n[RUN] Running FULL ETL Pipeline (Extract -> Transform -> Load)\n")
            extracted_data, extract_file = run_extract_phase()
            transformed_data, transform_file = run_transform_phase(extracted_data)
            run_load_phase(transformed_data)
            print("\n[OK] FULL ETL PIPELINE COMPLETED SUCCESSFULLY!\n")
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n[ERROR] ETL Pipeline Error: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
