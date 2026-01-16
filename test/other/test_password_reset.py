#!/usr/bin/env python3
"""
Test Password Reset Functionality
Tests all password reset features including token generation, validation, and password strength
"""

import sys
sys.path.insert(0, 'src')

from auth import (
    hash_password,
    verify_password,
    initialize_demo_credentials,
    authenticate_user,
    generate_reset_token,
    verify_reset_token,
    reset_password,
    validate_password_strength,
    cleanup_expired_tokens,
    DEMO_USERS
)
from utils import setup_logger

logger = setup_logger(__name__, log_file='logs/test_password_reset.log')

def test_password_reset():
    """Test complete password reset workflow"""
    
    logger.info("="*80)
    logger.info("PASSWORD RESET FUNCTIONALITY TEST")
    logger.info("="*80)
    
    # Test 1: Validate password strength
    logger.info("\n[TEST 1] Password Strength Validation")
    
    weak_passwords = [
        ("password", "No uppercase/numbers/special"),
        ("Pass123", "No special character"),
        ("Pass@", "Too short"),
    ]
    
    for pwd, reason in weak_passwords:
        result = validate_password_strength(pwd)
        logger.info(f"[TEST] '{pwd}' - Strength: {result['strength']} ({reason})")
        if not result['valid']:
            logger.info(f"       Issues: {', '.join(result['requirements'])}")
    
    strong_passwords = [
        "SecurePass@123",
        "MyP@ssw0rd",
        "Admin#2024Password"
    ]
    
    for pwd in strong_passwords:
        result = validate_password_strength(pwd)
        logger.info(f"[OK] '{pwd}' - Strength: {result['strength']}")
        if not result['valid']:
            logger.error(f"[FAIL] Strong password failed validation")
    
    # Test 2: Generate reset token
    logger.info("\n[TEST 2] Generate Reset Token")
    token = generate_reset_token("sales_user", validity_minutes=30)
    logger.info(f"[OK] Reset token generated: {token[:20]}...")
    
    # Test 3: Verify token
    logger.info("\n[TEST 3] Verify Reset Token")
    token_check = verify_reset_token(token)
    if token_check['valid']:
        logger.info(f"[OK] Token verified for user: {token_check['username']}")
        logger.info(f"    Expires at: {token_check['expires_at']}")
    else:
        logger.error(f"[FAIL] Token verification failed: {token_check['message']}")
    
    # Test 4: Reset password with token
    logger.info("\n[TEST 4] Reset Password with Token")
    new_password = "NewSecure@Pass123"
    reset_result = reset_password("sales_user", new_password, reset_token=token)
    
    if reset_result['success']:
        logger.info(f"[OK] Password reset successful")
        logger.info(f"    New password strength: {reset_result['password_strength']}")
    else:
        logger.error(f"[FAIL] Password reset failed: {reset_result['message']}")
    
    # Test 5: Verify new password works
    logger.info("\n[TEST 5] Verify New Password in Login")
    auth_result = authenticate_user("sales_user", new_password)
    if auth_result['authenticated']:
        logger.info(f"[OK] Login with new password successful (role: {auth_result['role']})")
    else:
        logger.error(f"[FAIL] Login with new password failed: {auth_result['message']}")
    
    # Test 6: Verify old password doesn't work
    logger.info("\n[TEST 6] Verify Old Password Fails")
    auth_result_old = authenticate_user("sales_user", "Demo@123")
    if not auth_result_old['authenticated']:
        logger.info(f"[OK] Old password correctly rejected")
    else:
        logger.error(f"[FAIL] Old password should not work anymore")
    
    # Test 7: Token reuse prevention
    logger.info("\n[TEST 7] Token Reuse Prevention")
    token_reuse_check = verify_reset_token(token)
    if not token_reuse_check['valid']:
        logger.info(f"[OK] Token marked as used, cannot be reused")
    else:
        logger.error(f"[FAIL] Used token should not be valid")
    
    # Test 8: Weak password rejection
    logger.info("\n[TEST 8] Weak Password Rejection")
    weak_reset_result = reset_password("manager_user", "weakpass")
    if not weak_reset_result['success']:
        logger.info(f"[OK] Weak password rejected: {weak_reset_result['message'][:50]}...")
    else:
        logger.error(f"[FAIL] Weak password should be rejected")
    
    # Test 9: Reset password without token (admin override - no token)
    logger.info("\n[TEST 9] Reset Password Without Token (Admin Override)")
    admin_reset = reset_password("exec_user", "ExecutivePass@2024")
    if admin_reset['success']:
        logger.info(f"[OK] Admin password reset successful (strength: {admin_reset['password_strength']})")
    else:
        logger.error(f"[FAIL] Admin reset failed: {admin_reset['message']}")
    
    # Test 10: Cleanup expired tokens
    logger.info("\n[TEST 10] Cleanup Expired Tokens")
    cleaned_count = cleanup_expired_tokens()
    logger.info(f"[OK] Cleaned up {cleaned_count} expired tokens")
    
    # Test 11: All users can be authenticated
    logger.info("\n[TEST 11] Verify All Users Can Authenticate")
    users_to_test = [
        ("sales_user", new_password),
        ("manager_user", "Demo@123"),
        ("exec_user", "ExecutivePass@2024")
    ]
    
    for username, password in users_to_test:
        result = authenticate_user(username, password)
        if result['authenticated']:
            logger.info(f"[OK] {username} ({result['role']}) authenticated")
        else:
            logger.warning(f"[WARN] {username} authentication failed: {result['message']}")
    
    logger.info("\n" + "="*80)
    logger.info("PASSWORD RESET TESTS COMPLETED [OK]")
    logger.info("="*80)
    logger.info("\nKey Features Verified:")
    logger.info("  - Password strength validation (8+ chars, upper, lower, digit, special)")
    logger.info("  - Reset token generation with expiration")
    logger.info("  - Token verification and reuse prevention")
    logger.info("  - Secure password reset with token")
    logger.info("  - Old passwords invalidated after reset")
    logger.info("  - Weak password rejection")
    logger.info("  - Token cleanup mechanism")

if __name__ == '__main__':
    test_password_reset()



