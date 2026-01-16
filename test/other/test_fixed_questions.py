"""
Test to verify fixed security questions logic

Verifies:
1. All signup users get the SAME 4 fixed questions
2. Password recovery selects only from those 4 fixed questions
3. No mismatch between signup and recovery questions
"""

import sys
import os
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.auth import (
    get_signup_security_questions,
    get_security_questions_for_user,
    SIGNUP_SECURITY_QUESTION_INDICES,
    SECURITY_QUESTIONS
)

def test_signup_questions_are_fixed():
    """Verify all users get the SAME 4 fixed questions for signup"""
    print("\n[TEST 1] Signup Questions Are Fixed (Same for All Users)...")
    
    # Get signup questions multiple times
    questions_1 = get_signup_security_questions()
    questions_2 = get_signup_security_questions()
    questions_3 = get_signup_security_questions()
    
    # Verify they're identical
    assert len(questions_1) == 4, f"Expected 4 questions, got {len(questions_1)}"
    assert questions_1 == questions_2, "Signup questions differ on second call"
    assert questions_1 == questions_3, "Signup questions differ on third call"
    
    # Verify they match the fixed indices
    expected_indices = SIGNUP_SECURITY_QUESTION_INDICES
    actual_indices = [idx for idx, _ in questions_1]
    
    assert actual_indices == expected_indices, \
        f"Indices don't match. Expected {expected_indices}, got {actual_indices}"
    
    print(f"  ✅ All signup users get same 4 questions:")
    for idx, (q_idx, question) in enumerate(questions_1, 1):
        print(f"     Q{idx} (index {q_idx}): {question}")
    
    return True


def test_recovery_selects_from_fixed():
    """Verify password recovery only selects from the 4 fixed questions"""
    print("\n[TEST 2] Password Recovery Selects from Fixed Questions...")
    
    # Get recovery questions multiple times
    recovery_sets = []
    for _ in range(10):  # Test 10 times to verify randomness
        recovery = get_security_questions_for_user("test_user", 3)
        recovery_sets.append([idx for idx, _ in recovery])
    
    # Verify all questions are from the fixed set
    fixed_indices = set(SIGNUP_SECURITY_QUESTION_INDICES)
    for recovery_indices in recovery_sets:
        for idx in recovery_indices:
            assert idx in fixed_indices, \
                f"Recovery question index {idx} not in fixed set {SIGNUP_SECURITY_QUESTION_INDICES}"
    
    # Verify we get exactly 3 questions
    for recovery_indices in recovery_sets:
        assert len(recovery_indices) == 3, \
            f"Expected 3 recovery questions, got {len(recovery_indices)}"
    
    # Verify we get variation (not the same 3 every time)
    unique_sets = set(tuple(sorted(r)) for r in recovery_sets)
    assert len(unique_sets) > 1, "Recovery questions should vary (not always the same 3)"
    
    print(f"  ✅ Recovery questions all selected from fixed set")
    print(f"  ✅ Got {len(unique_sets)} different combinations from 10 attempts")
    print(f"  ✅ Sample recovery sets:")
    for i, recovery_indices in enumerate(recovery_sets[:3], 1):
        recovery = get_security_questions_for_user("test_user", 3)
        print(f"     Set {i}: {[q[1] for q in recovery]}")
    
    return True


def test_no_mismatch_between_signup_and_recovery():
    """Verify no mismatch: all recovery questions are from signup questions"""
    print("\n[TEST 3] No Mismatch Between Signup and Recovery Questions...")
    
    signup_questions = get_signup_security_questions()
    signup_indices = set(idx for idx, _ in signup_questions)
    
    # Generate multiple recovery question sets
    for attempt in range(20):
        recovery_questions = get_security_questions_for_user("test_user", 3)
        recovery_indices = set(idx for idx, _ in recovery_questions)
        
        # Verify all recovery questions are in signup questions
        assert recovery_indices.issubset(signup_indices), \
            f"Recovery attempt {attempt} has questions not in signup: {recovery_indices - signup_indices}"
    
    print(f"  ✅ All recovery questions (20 attempts) are subset of signup questions")
    print(f"  ✅ No mismatch detected: users will be asked only questions they answered")
    
    return True


def test_fixed_indices_correct():
    """Verify SIGNUP_SECURITY_QUESTION_INDICES constant is correct"""
    print("\n[TEST 4] Fixed Indices Constant Validation...")
    
    expected_indices = [0, 2, 4, 6]
    actual_indices = SIGNUP_SECURITY_QUESTION_INDICES
    
    assert actual_indices == expected_indices, \
        f"Expected indices {expected_indices}, got {actual_indices}"
    
    # Verify they map to real questions
    print(f"  ✅ Fixed indices {actual_indices} map to:")
    for idx in actual_indices:
        assert idx < len(SECURITY_QUESTIONS), f"Index {idx} out of range"
        print(f"     Index {idx}: {SECURITY_QUESTIONS[idx]}")
    
    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("FIXED SECURITY QUESTIONS LOGIC TEST SUITE")
    print("="*70)
    
    try:
        test_1_pass = test_signup_questions_are_fixed()
        test_2_pass = test_recovery_selects_from_fixed()
        test_3_pass = test_no_mismatch_between_signup_and_recovery()
        test_4_pass = test_fixed_indices_correct()
        
        print("\n" + "="*70)
        if all([test_1_pass, test_2_pass, test_3_pass, test_4_pass]):
            print("✅ ALL TESTS PASSED (4/4)")
            print("="*70)
            print("\n✅ Fixed Questions Logic Verified:")
            print("   • All signup users get same 4 fixed questions")
            print("   • Password recovery selects 3 from those same 4")
            print("   • No mismatch between signup and recovery")
            print("   • Security questions properly configured")
        else:
            print("❌ SOME TESTS FAILED")
            print("="*70)
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70)
        sys.exit(1)



