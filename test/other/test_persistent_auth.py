#!/usr/bin/env python3
"""
Comprehensive Test Script for Persistent User Authentication (Database-Backed)

Tests all scenarios:
1. Sales Associate signup → PostgreSQL OLTP
2. Store Manager signup → MySQL OLAP
3. Executive signup → MySQL OLAP
4. Login from database (not in-memory)
5. Forgot password with security questions
6. Verify no credentials leak between databases
7. Password hashing with bcrypt
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import load_env_config, get_postgres_connection, get_mysql_connection
from auth import (
    register_user_db,
    authenticate_user_db,
    store_security_answers_db,
    get_security_answers_db,
    reset_password_db,
    verify_password,
    validate_password_strength,
    get_user_table_name
)
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test credentials
TEST_USERS = {
    "Sales Associate": {
        "username": "test_sales_user",
        "password": "TestPass@123",
        "role": "Sales Associate",
        "security_answers": {
            0: "Blue",
            2: "Toronto",
            4: "St. Mary's",
            6: "1990"
        }
    },
    "Store Manager": {
        "username": "test_manager_user",
        "password": "ManagerPass@456",
        "role": "Store Manager",
        "security_answers": {
            0: "Red",
            2: "New York",
            4: "Central High",
            6: "1985"
        }
    },
    "Executive": {
        "username": "test_exec_user",
        "password": "ExecPass@789",
        "role": "Executive",
        "security_answers": {
            0: "Green",
            2: "Boston",
            4: "Lincoln High",
            6: "1988"
        }
    }
}

class AuthTestSuite:
    def __init__(self):
        self.config = load_env_config()
        self.passed = 0
        self.failed = 0
    
    def log_test(self, test_name, result, message=""):
        if result:
            logger.info(f"✓ PASS: {test_name}")
            self.passed += 1
        else:
            logger.error(f"✗ FAIL: {test_name} - {message}")
            self.failed += 1
    
    def cleanup_user(self, username, role):
        """Delete test user from database"""
        try:
            if role == "Sales Associate":
                conn = get_postgres_connection(self.config)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM fa25_ssc_users_sales_associate WHERE username = %s', (username,))
                conn.commit()
                cursor.close()
                conn.close()
            else:
                conn = get_mysql_connection(self.config)
                cursor = conn.cursor()
                table = "fa25_ssc_users_store_manager" if role == "Store Manager" else "fa25_ssc_users_executive"
                cursor.execute(f'DELETE FROM {table} WHERE username = %s', (username,))
                conn.commit()
                cursor.close()
                conn.close()
        except Exception as e:
            logger.warning(f"Cleanup failed for {username}: {e}")
    
    def test_1_signup_all_roles(self):
        """Test 1: Signup users with all three roles"""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: Signup Users with All Roles")
        logger.info("="*70)
        
        for role_name, user_data in TEST_USERS.items():
            try:
                # Cleanup first
                self.cleanup_user(user_data["username"], role_name)
                
                # Get connection for role
                if role_name == "Sales Associate":
                    conn = get_postgres_connection(self.config)
                else:
                    conn = get_mysql_connection(self.config)
                
                # Register user
                result = register_user_db(
                    user_data["username"],
                    user_data["password"],
                    role_name,
                    conn
                )
                
                success = result['success']
                self.log_test(
                    f"Signup {role_name} ({user_data['username']})",
                    success,
                    result['message'] if not success else ""
                )
                
                if success:
                    # Store security answers
                    answers_result = store_security_answers_db(
                        user_data["username"],
                        role_name,
                        user_data["security_answers"],
                        conn
                    )
                    
                    self.log_test(
                        f"Store security answers for {role_name}",
                        answers_result['success'],
                        answers_result['message'] if not answers_result['success'] else ""
                    )
                
                conn.close()
            
            except Exception as e:
                self.log_test(f"Signup {role_name}", False, str(e))
    
    def test_2_login_all_roles(self):
        """Test 2: Login with correct credentials from each role's database"""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: Login from Database (Not In-Memory)")
        logger.info("="*70)
        
        for role_name, user_data in TEST_USERS.items():
            try:
                # Get connection for role
                if role_name == "Sales Associate":
                    conn = get_postgres_connection(self.config)
                else:
                    conn = get_mysql_connection(self.config)
                
                # Authenticate
                result = authenticate_user_db(
                    user_data["username"],
                    user_data["password"],
                    role_name,
                    conn
                )
                
                success = result['authenticated']
                self.log_test(
                    f"Login {role_name} ({user_data['username']})",
                    success,
                    result['message'] if not success else ""
                )
                
                conn.close()
            
            except Exception as e:
                self.log_test(f"Login {role_name}", False, str(e))
    
    def test_3_login_wrong_password(self):
        """Test 3: Login fails with wrong password"""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: Login Fails with Wrong Password")
        logger.info("="*70)
        
        for role_name, user_data in TEST_USERS.items():
            try:
                if role_name == "Sales Associate":
                    conn = get_postgres_connection(self.config)
                else:
                    conn = get_mysql_connection(self.config)
                
                result = authenticate_user_db(
                    user_data["username"],
                    "WrongPassword123",  # Wrong password
                    role_name,
                    conn
                )
                
                # Should NOT be authenticated
                success = not result['authenticated']
                self.log_test(
                    f"Login rejection for {role_name} with wrong password",
                    success
                )
                
                conn.close()
            
            except Exception as e:
                self.log_test(f"Wrong password test {role_name}", False, str(e))
    
    def test_4_login_wrong_role(self):
        """Test 4: User can't login with different role's database"""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: Cross-Role Login Isolation")
        logger.info("="*70)
        
        # Try to login Sales Associate from Store Manager's database
        sales_user = TEST_USERS["Sales Associate"]
        
        try:
            # Connect to WRONG database (MySQL instead of PostgreSQL)
            conn = get_mysql_connection(self.config)
            
            result = authenticate_user_db(
                sales_user["username"],
                sales_user["password"],
                "Sales Associate",  # Say it's Sales Associate but query MySQL
                conn
            )
            
            # Should NOT be authenticated (user not in MySQL)
            success = not result['authenticated']
            self.log_test(
                "Sales Associate not found in Store Manager database (MySQL)",
                success
            )
            
            conn.close()
        
        except Exception as e:
            self.log_test("Cross-role isolation test", False, str(e))
    
    def test_5_password_hashing(self):
        """Test 5: Verify bcrypt hashing is working"""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: Password Hashing with Bcrypt")
        logger.info("="*70)
        
        try:
            # Get a user's hashed password from database
            conn = get_postgres_connection(self.config)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT password_hash FROM fa25_ssc_users_sales_associate WHERE username = %s',
                (TEST_USERS["Sales Associate"]["username"],)
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                hashed_pwd = row[0]
                
                # Verify correct password
                correct_verify = verify_password(
                    TEST_USERS["Sales Associate"]["password"],
                    hashed_pwd
                )
                
                # Verify wrong password
                wrong_verify = verify_password("WrongPassword123", hashed_pwd)
                
                # Check format (bcrypt hashes start with $2b$)
                bcrypt_format = hashed_pwd.startswith("$2b$")
                
                self.log_test("Password hashing uses bcrypt format", bcrypt_format)
                self.log_test("Correct password verifies", correct_verify)
                self.log_test("Wrong password fails verification", not wrong_verify)
            else:
                self.log_test("Get hashed password from database", False, "User not found")
        
        except Exception as e:
            self.log_test("Password hashing test", False, str(e))
    
    def test_6_security_questions(self):
        """Test 6: Security questions stored and retrieved correctly"""
        logger.info("\n" + "="*70)
        logger.info("TEST 6: Security Questions (Bcrypt Hashed)")
        logger.info("="*70)
        
        for role_name, user_data in TEST_USERS.items():
            try:
                if role_name == "Sales Associate":
                    conn = get_postgres_connection(self.config)
                else:
                    conn = get_mysql_connection(self.config)
                
                # Get stored answers
                stored_answers = get_security_answers_db(
                    user_data["username"],
                    role_name,
                    conn
                )
                
                if stored_answers:
                    # Verify one answer
                    answer_verified = False
                    for q_idx, hashed_answer in stored_answers.items():
                        q_idx_int = int(q_idx)  # Convert string key to int
                        if q_idx_int in user_data["security_answers"]:
                            answer_verified = verify_password(
                                user_data["security_answers"][q_idx_int],
                                hashed_answer
                            )
                            if answer_verified:
                                break
                    
                    self.log_test(
                        f"Security questions stored and hashed for {role_name}",
                        answer_verified
                    )
                else:
                    self.log_test(f"Retrieve security answers for {role_name}", False, "No answers found")
                
                conn.close()
            
            except Exception as e:
                self.log_test(f"Security questions test {role_name}", False, str(e))
    
    def test_7_password_reset(self):
        """Test 7: Password reset functionality"""
        logger.info("\n" + "="*70)
        logger.info("TEST 7: Password Reset")
        logger.info("="*70)
        
        role_name = "Sales Associate"
        user_data = TEST_USERS[role_name]
        new_password = "NewPass@999"
        
        try:
            conn = get_postgres_connection(self.config)
            
            # Reset password
            result = reset_password_db(
                user_data["username"],
                role_name,
                new_password,
                conn
            )
            
            self.log_test(
                f"Reset password for {role_name}",
                result['success'],
                result['message'] if not result['success'] else ""
            )
            
            if result['success']:
                # Try login with new password
                login_result = authenticate_user_db(
                    user_data["username"],
                    new_password,
                    role_name,
                    conn
                )
                
                self.log_test(
                    "Login with new password",
                    login_result['authenticated']
                )
                
                # Reset back to original for cleanup
                reset_back = reset_password_db(
                    user_data["username"],
                    role_name,
                    user_data["password"],
                    conn
                )
                self.log_test("Reset password back to original", reset_back['success'])
            
            conn.close()
        
        except Exception as e:
            self.log_test("Password reset test", False, str(e))
    
    def test_8_database_isolation(self):
        """Test 8: Verify credentials are in correct databases only"""
        logger.info("\n" + "="*70)
        logger.info("TEST 8: Database Isolation Verification")
        logger.info("="*70)
        
        try:
            # Check Sales Associate is ONLY in PostgreSQL
            pg_conn = get_postgres_connection(self.config)
            pg_cursor = pg_conn.cursor()
            
            pg_cursor.execute(
                'SELECT COUNT(*) FROM fa25_ssc_users_sales_associate WHERE username = %s',
                (TEST_USERS["Sales Associate"]["username"],)
            )
            sales_in_pg = pg_cursor.fetchone()[0]
            pg_cursor.close()
            pg_conn.close()
            
            # Check Sales Associate is NOT in MySQL
            mysql_conn = get_mysql_connection(self.config)
            mysql_cursor = mysql_conn.cursor()
            
            try:
                mysql_cursor.execute(
                    'SELECT COUNT(*) FROM fa25_ssc_users_sales_associate WHERE username = %s',
                    (TEST_USERS["Sales Associate"]["username"],)
                )
                sales_in_mysql = mysql_cursor.fetchone()[0]
            except Exception:
                sales_in_mysql = 0  # Table doesn't exist in MySQL
            
            mysql_cursor.close()
            mysql_conn.close()
            
            self.log_test(
                "Sales Associate in PostgreSQL OLTP (count=1)",
                sales_in_pg == 1
            )
            
            self.log_test(
                "Sales Associate NOT in MySQL OLAP (count=0)",
                sales_in_mysql == 0
            )
            
            # Check Store Manager is ONLY in MySQL
            mysql_conn = get_mysql_connection(self.config)
            mysql_cursor = mysql_conn.cursor()
            
            mysql_cursor.execute(
                'SELECT COUNT(*) FROM fa25_ssc_users_store_manager WHERE username = %s',
                (TEST_USERS["Store Manager"]["username"],)
            )
            manager_in_mysql = mysql_cursor.fetchone()[0]
            mysql_cursor.close()
            mysql_conn.close()
            
            self.log_test(
                "Store Manager in MySQL OLAP (count=1)",
                manager_in_mysql == 1
            )
        
        except Exception as e:
            self.log_test("Database isolation test", False, str(e))
    
    def cleanup_all(self):
        """Clean up all test users"""
        logger.info("\n" + "="*70)
        logger.info("Cleanup: Removing Test Users")
        logger.info("="*70)
        
        for role_name, user_data in TEST_USERS.items():
            self.cleanup_user(user_data["username"], role_name)
            logger.info(f"Cleaned up {role_name} test user")
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("\n" + "="*70)
        logger.info("PERSISTENT USER AUTHENTICATION - COMPREHENSIVE TEST SUITE")
        logger.info("="*70)
        logger.info("Testing bcrypt-protected credentials in role-specific databases")
        
        try:
            self.test_1_signup_all_roles()
            self.test_2_login_all_roles()
            self.test_3_login_wrong_password()
            self.test_4_login_wrong_role()
            self.test_5_password_hashing()
            self.test_6_security_questions()
            self.test_7_password_reset()
            self.test_8_database_isolation()
        except Exception as e:
            logger.error(f"Test suite error: {e}")
        finally:
            self.cleanup_all()
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("TEST SUMMARY")
        logger.info("="*70)
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        logger.info("="*70)
        
        return self.failed == 0


if __name__ == "__main__":
    suite = AuthTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)



