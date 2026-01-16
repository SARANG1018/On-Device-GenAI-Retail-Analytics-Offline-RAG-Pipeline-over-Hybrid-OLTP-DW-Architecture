"""
Integration Test Script for Vanna.AI Implementation

This script tests the new Vanna.AI SQL generation with the existing analysis pipeline.
Run this BEFORE launching main.py to verify everything works correctly.

Usage:
    python test_vanna_integration.py
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import load_env_config, setup_logger
from function_tools import process_question

# Setup logging
logger = setup_logger(__name__, log_file='logs/test_vanna_integration.log')


def test_vanna_integration():
    """Test the complete Vanna.AI + Analysis pipeline"""
    
    logger.info("="*80)
    logger.info("VANNA.AI INTEGRATION TEST")
    logger.info("="*80)
    
    try:
        # Load configuration
        logger.info("Step 1: Loading configuration...")
        config = load_env_config()
        logger.info("[OK] Configuration loaded successfully")
        
        # Test 1: Simple query
        logger.info("\n" + "="*80)
        logger.info("TEST 1: Simple Query - Store Performance")
        logger.info("="*80)
        
        question_1 = "What's the total sales by store?"
        logger.info(f"Question: {question_1}")
        
        result_1 = process_question(question_1, config)
        
        if result_1.get("error"):
            logger.error(f"[FAIL] TEST 1 FAILED: {result_1['error']}")
            return False
        
        logger.info("[OK] TEST 1 PASSED")
        logger.info(f"SQL Generated: {result_1.get('conversation_turn', {}).get('sql', 'N/A')[:100]}...")
        logger.info(f"Rows Returned: {result_1.get('conversation_turn', {}).get('num_rows', 0)}")
        logger.info(f"Response: {result_1.get('natural_response', 'N/A')[:150]}...")
        
        # Test 2: Multi-turn conversation
        logger.info("\n" + "="*80)
        logger.info("TEST 2: Multi-Turn Conversation - Follow-up Question")
        logger.info("="*80)
        
        conversation_history = [result_1.get('conversation_turn')]
        question_2 = "Show me the top 3 stores by sales"
        logger.info(f"Question: {question_2}")
        logger.info(f"With {len(conversation_history)} previous turn(s)")
        
        result_2 = process_question(question_2, config, conversation_history)
        
        if result_2.get("error"):
            logger.error(f"[FAIL] TEST 2 FAILED: {result_2['error']}")
            return False
        
        logger.info("[OK] TEST 2 PASSED")
        logger.info(f"SQL Generated: {result_2.get('conversation_turn', {}).get('sql', 'N/A')[:100]}...")
        logger.info(f"Rows Returned: {result_2.get('conversation_turn', {}).get('num_rows', 0)}")
        logger.info(f"Response: {result_2.get('natural_response', 'N/A')[:150]}...")
        
        # Test 3: Product analysis
        logger.info("\n" + "="*80)
        logger.info("TEST 3: Product Analysis")
        logger.info("="*80)
        
        question_3 = "Show me the top 5 selling products"
        logger.info(f"Question: {question_3}")
        
        result_3 = process_question(question_3, config)
        
        if result_3.get("error"):
            logger.error(f"[FAIL] TEST 3 FAILED: {result_3['error']}")
            return False
        
        logger.info("[OK] TEST 3 PASSED")
        logger.info(f"SQL Generated: {result_3.get('conversation_turn', {}).get('sql', 'N/A')[:100]}...")
        logger.info(f"Rows Returned: {result_3.get('conversation_turn', {}).get('num_rows', 0)}")
        logger.info(f"Response: {result_3.get('natural_response', 'N/A')[:150]}...")
        
        # Test 4: Return analysis
        logger.info("\n" + "="*80)
        logger.info("TEST 4: Return Rate Analysis")
        logger.info("="*80)
        
        question_4 = "What's the return rate by store?"
        logger.info(f"Question: {question_4}")
        
        result_4 = process_question(question_4, config)
        
        if result_4.get("error"):
            logger.error(f"[FAIL] TEST 4 FAILED: {result_4['error']}")
            return False
        
        logger.info("[OK] TEST 4 PASSED")
        logger.info(f"SQL Generated: {result_4.get('conversation_turn', {}).get('sql', 'N/A')[:100]}...")
        logger.info(f"Rows Returned: {result_4.get('conversation_turn', {}).get('num_rows', 0)}")
        logger.info(f"Response: {result_4.get('natural_response', 'N/A')[:150]}...")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("[OK] ALL TESTS PASSED!")
        logger.info("="*80)
        logger.info("\nVanna.AI integration successful!")
        logger.info("You can now run: streamlit run src/main.py")
        logger.info("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"\n[FAIL] TEST FAILED WITH EXCEPTION:")
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_vanna_integration()
    sys.exit(0 if success else 1)



