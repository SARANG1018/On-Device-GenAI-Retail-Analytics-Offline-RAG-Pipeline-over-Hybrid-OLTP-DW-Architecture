"""
Test Suite for Security Questions Functionality

Tests the following:
1. Setting security question answers
2. Verifying security question answers
3. Multiple answer verification (majority voting)
4. Getting random security questions
5. Checking if user has security questions set
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.auth import (
    set_security_answers,
    verify_security_answer,
    verify_multiple_security_answers,
    get_security_questions_for_user,
    has_security_questions_set,
    SECURITY_QUESTIONS,
    SECURITY_ANSWERS
)

def test_1_set_security_answers():
    """Test setting security question answers"""
    print("\n[TEST 1] Setting Security Answers...")
    
    # Clear previous data
    if "test_user" in SECURITY_ANSWERS:
        del SECURITY_ANSWERS["test_user"]
    
    # Set answer to question 0
    result = set_security_answers("test_user", 0, "Blue")
    assert result == True, "Failed to set security answer"
    
    # Set answer to question 2
    result = set_security_answers("test_user", 2, "Toronto")
    assert result == True, "Failed to set second security answer"
    
    # Set answer to question 4
    result = set_security_answers("test_user", 4, "St. Mary's School")
    assert result == True, "Failed to set third security answer"
    
    print("✅ PASS: Security answers set successfully")


def test_2_verify_security_answers():
    """Test verifying security question answers"""
    print("\n[TEST 2] Verifying Security Answers...")
    
    # Test correct answer
    result = verify_security_answer("test_user", 0, "Blue")
    assert result == True, "Failed to verify correct answer"
    print("  ✅ Correct answer verified")
    
    # Test incorrect answer
    result = verify_security_answer("test_user", 0, "Red")
    assert result == False, "Verified incorrect answer (should fail)"
    print("  ✅ Incorrect answer rejected")
    
    # Test case insensitivity
    result = verify_security_answer("test_user", 2, "TORONTO")
    assert result == True, "Case insensitivity failed"
    print("  ✅ Case insensitivity working")
    
    # Test different answer
    result = verify_security_answer("test_user", 4, "St. Mary's School")
    assert result == True, "Failed to verify different answer"
    print("  ✅ Different answer verified")
    
    print("✅ PASS: All answer verifications passed")


def test_3_multiple_answer_verification():
    """Test verifying multiple answers with majority voting"""
    print("\n[TEST 3] Multiple Answer Verification (Majority Voting)...")
    
    # Test with 2 correct, 1 incorrect (should pass - 2/3)
    answers = {
        0: "Blue",        # Correct
        2: "Toronto",     # Correct
        4: "Wrong"        # Incorrect
    }
    
    result = verify_multiple_security_answers("test_user", answers)
    assert result == True, "Failed majority voting (2/3 correct should pass)"
    print("  ✅ Majority voting passed (2/3 correct)")
    
    # Test with 1 correct, 2 incorrect (should fail)
    answers = {
        0: "Blue",        # Correct
        2: "Paris",       # Incorrect
        4: "Wrong"        # Incorrect
    }
    
    result = verify_multiple_security_answers("test_user", answers)
    assert result == False, "Failed to reject minority voting (1/3 correct should fail)"
    print("  ✅ Minority voting rejected (1/3 correct)")
    
    # Test all correct
    answers = {
        0: "Blue",
        2: "Toronto",
        4: "St. Mary's School"
    }
    
    result = verify_multiple_security_answers("test_user", answers)
    assert result == True, "Failed with all correct answers"
    print("  ✅ All correct answers verified (3/3)")
    
    print("✅ PASS: Multiple answer verification working")


def test_4_get_random_questions():
    """Test getting random security questions"""
    print("\n[TEST 4] Getting Random Security Questions...")
    
    questions = get_security_questions_for_user("test_user", 3)
    
    assert len(questions) == 3, f"Expected 3 questions, got {len(questions)}"
    print(f"  ✅ Got 3 random questions")
    
    # Verify format
    for q_index, question_text in questions:
        assert isinstance(q_index, int), "Question index should be integer"
        assert isinstance(question_text, str), "Question text should be string"
        assert 0 <= q_index < len(SECURITY_QUESTIONS), "Invalid question index"
    
    print(f"  ✅ Question format verified")
    print(f"  Sample questions:")
    for idx, (q_idx, q_text) in enumerate(questions, 1):
        print(f"    Q{idx}: {q_text}")
    
    print("✅ PASS: Random question selection working")


def test_5_has_security_questions():
    """Test checking if user has security questions set"""
    print("\n[TEST 5] Checking Security Question Configuration...")
    
    # Test user with questions
    result = has_security_questions_set("test_user")
    assert result == True, "Failed to detect user with security questions"
    print("  ✅ User with questions detected")
    
    # Test user without questions
    result = has_security_questions_set("nonexistent_user")
    assert result == False, "Incorrectly detected questions for user without any"
    print("  ✅ User without questions correctly identified")
    
    print("✅ PASS: Security question detection working")


def test_6_invalid_question_index():
    """Test error handling for invalid question indices"""
    print("\n[TEST 6] Error Handling for Invalid Question Index...")
    
    # Test invalid index (too high)
    result = set_security_answers("test_user", 999, "Answer")
    assert result == False, "Should reject invalid question index"
    print("  ✅ Invalid high index rejected")
    
    # Test invalid index (negative)
    result = set_security_answers("test_user", -1, "Answer")
    assert result == False, "Should reject negative question index"
    print("  ✅ Invalid negative index rejected")
    
    print("✅ PASS: Error handling working")


def test_7_new_user_flow():
    """Test complete flow for a new user"""
    print("\n[TEST 7] New User Security Questions Flow...")
    
    # Clear previous data
    if "new_user" in SECURITY_ANSWERS:
        del SECURITY_ANSWERS["new_user"]
    
    # Step 1: Check user has no questions
    assert has_security_questions_set("new_user") == False
    print("  ✅ New user has no security questions")
    
    # Step 2: Get questions for user
    questions = get_security_questions_for_user("new_user", 3)
    assert len(questions) == 3
    print("  ✅ Retrieved 3 questions for new user")
    
    # Step 3: Set answers
    set_security_answers("new_user", questions[0][0], "Answer1")
    set_security_answers("new_user", questions[1][0], "Answer2")
    set_security_answers("new_user", questions[2][0], "Answer3")
    print("  ✅ Set 3 security answers")
    
    # Step 4: Verify user now has questions
    assert has_security_questions_set("new_user") == True
    print("  ✅ Verified new user has security questions")
    
    # Step 5: Verify all answers
    answers_dict = {
        questions[0][0]: "Answer1",
        questions[1][0]: "Answer2",
        questions[2][0]: "Answer3"
    }
    result = verify_multiple_security_answers("new_user", answers_dict)
    assert result == True
    print("  ✅ All answers verified successfully")
    
    print("✅ PASS: New user flow complete")


def test_8_answer_case_insensitivity():
    """Test that answer verification is case-insensitive"""
    print("\n[TEST 8] Case Insensitivity Testing...")
    
    # Clear and set initial answer
    if "case_test_user" in SECURITY_ANSWERS:
        del SECURITY_ANSWERS["case_test_user"]
    
    set_security_answers("case_test_user", 0, "MyAnswer")
    
    # Test various cases
    test_cases = [
        ("MyAnswer", True),      # Exact match
        ("MYANSWER", True),      # All caps
        ("myanswer", True),      # All lowercase
        ("MyAnSwEr", True),      # Mixed case
        ("Wrong", False),         # Completely different
    ]
    
    for answer, expected in test_cases:
        result = verify_security_answer("case_test_user", 0, answer)
        assert result == expected, f"Failed for answer '{answer}'"
        print(f"  ✅ '{answer}' -> {result} (expected {expected})")
    
    print("✅ PASS: Case insensitivity verified")


if __name__ == "__main__":
    print("=" * 70)
    print("SECURITY QUESTIONS TEST SUITE")
    print("=" * 70)
    
    try:
        test_1_set_security_answers()
        test_2_verify_security_answers()
        test_3_multiple_answer_verification()
        test_4_get_random_questions()
        test_5_has_security_questions()
        test_6_invalid_question_index()
        test_7_new_user_flow()
        test_8_answer_case_insensitivity()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED (8/8)")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("=" * 70)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print("=" * 70)
        sys.exit(1)



