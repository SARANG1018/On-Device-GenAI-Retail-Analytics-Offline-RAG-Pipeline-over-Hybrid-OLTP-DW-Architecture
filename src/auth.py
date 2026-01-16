import bcrypt
import logging
import secrets
import string
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    try:
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Convert bytes to string for storage in database
        hashed_string = hashed.decode('utf-8')
        
        logger.debug("Password hashed successfully")
        return hashed_string
    
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        # Compare password with hash
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        is_match = bcrypt.checkpw(password_bytes, hashed_bytes)
        
        if is_match:
            logger.debug("Password verified successfully")
        else:
            logger.debug("Password verification failed - mismatch")
        
        return is_match
    
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


# Database-persistent authentication
# Password reset and security questions
SECURITY_QUESTIONS = [
    "What is your favorite color?",
    "What is your pet's name?",
    "What city were you born in?",
    "What is your mother's maiden name?",
    "What was the name of your first school?",
    "What is your favorite food?",
    "In what year were you born?"
]

SIGNUP_SECURITY_QUESTION_INDICES = [0, 2, 4, 6]




def validate_password_strength(password: str) -> dict:
    result = {
        'valid': False,
        'strength': 'weak',
        'requirements': [],
        'message': ''
    }
    
    try:
        # Minimum length
        if len(password) < 8:
            result['requirements'].append('At least 8 characters')
        
        # Uppercase letter
        if not any(c.isupper() for c in password):
            result['requirements'].append('At least one uppercase letter')
        
        # Lowercase letter
        if not any(c.islower() for c in password):
            result['requirements'].append('At least one lowercase letter')
        
        # Number
        if not any(c.isdigit() for c in password):
            result['requirements'].append('At least one number')
        
        # Special character
        special_chars = string.punctuation
        if not any(c in special_chars for c in password):
            result['requirements'].append('At least one special character (!@#$%^&*)')
        
        # Determine strength
        if len(result['requirements']) == 0:
            result['valid'] = True
            result['strength'] = 'strong'
            result['message'] = 'Password is strong'
        elif len(result['requirements']) <= 2:
            result['valid'] = True
            result['strength'] = 'medium'
            result['message'] = 'Password is medium strength'
        else:
            result['strength'] = 'weak'
            result['message'] = f"Password is weak: {', '.join(result['requirements'])}"
        
        return result
    
    except Exception as e:
        result['message'] = f"Error validating password: {str(e)}"
        logger.error(f"Error validating password: {e}")
        return result





# Security questions functionality




def get_signup_security_questions() -> list:
    try:
        questions = [
            (idx, SECURITY_QUESTIONS[idx])
            for idx in SIGNUP_SECURITY_QUESTION_INDICES
        ]
        logger.debug(f"Returning fixed signup security questions (4 questions)")
        return questions
    
    except Exception as e:
        logger.error(f"Error getting signup security questions: {e}")
        return []


def get_security_questions_for_user(username: str, num_questions: int = 3) -> list:
    try:
        import random
        
        # Always select from the fixed signup questions
        num_to_select = min(num_questions, len(SIGNUP_SECURITY_QUESTION_INDICES))
        
        if num_to_select <= 0:
            logger.warning(f"No signup questions available for password recovery")
            return []
        
        # Select random questions from the fixed signup questions
        selected_indices = random.sample(SIGNUP_SECURITY_QUESTION_INDICES, num_to_select)
        
        questions = [
            (idx, SECURITY_QUESTIONS[idx])
            for idx in selected_indices
        ]
        
        logger.debug(f"Selected {num_to_select} recovery questions for user '{username}' from fixed signup questions")
        return questions
    
    except Exception as e:
        logger.error(f"Error getting security questions for recovery: {e}")
        return []





# Role-based user storage functions

def get_user_table_name(role: str) -> str:
    role_to_table = {
        "Sales Associate": "fa25_ssc_users_sales_associate",
        "Store Manager": "fa25_ssc_users_store_manager",
        "Executive": "fa25_ssc_users_executive"
    }
    return role_to_table.get(role, "fa25_ssc_users_sales_associate")


def register_user_db(username: str, password: str, role: str, conn) -> dict:
    result = {
        "success": False,
        "message": "",
        "username": username,
        "role": role
    }
    
    # Validate role
    valid_roles = ["Sales Associate", "Store Manager", "Executive"]
    if role not in valid_roles:
        result["message"] = f"Invalid role '{role}'. Valid roles: {', '.join(valid_roles)}"
        logger.warning(f"Registration failed: Invalid role '{role}'")
        return result
    
    try:
        # Validate username
        if not username or len(username) < 3:
            result["message"] = "Username must be at least 3 characters"
            logger.warning(f"Registration failed: Invalid username '{username}'")
            return result
        
        # Validate password strength
        strength_result = validate_password_strength(password)
        if strength_result['strength'] != 'strong':
            missing = ', '.join(strength_result['requirements'])
            result["message"] = f"Password is too weak. Missing: {missing}"
            logger.warning(f"Registration failed for '{username}': Weak password")
            return result
        
        table_name = get_user_table_name(role)
        cursor = conn.cursor()
        
        # Check if username already exists in this role's table
        cursor.execute(f'SELECT user_id FROM {table_name} WHERE username = %s', (username,))
        if cursor.fetchone():
            result["message"] = f"Username '{username}' already exists for role {role}"
            logger.warning(f"Registration failed: Username '{username}' already exists in {table_name}")
            cursor.close()
            return result
        
        # Hash password
        password_hash = hash_password(password)
        
        # Insert new user into role-specific table
        cursor.execute(
            f"""
            INSERT INTO {table_name} (username, password_hash, role)
            VALUES (%s, %s, %s)
            """,
            (username, password_hash, role)
        )
        
        # Get user_id - different handling for PostgreSQL vs MySQL
        if hasattr(conn, 'autocommit'):  # PostgreSQL
            conn.commit()
            cursor.execute(f'SELECT user_id FROM {table_name} WHERE username = %s', (username,))
            user_id = cursor.fetchone()[0]
        else:  # MySQL
            conn.commit()
            user_id = cursor.lastrowid
        
        result["success"] = True
        result["message"] = f"User '{username}' registered successfully as {role}"
        result["role"] = role
        
        logger.info(f"New user registered in DB: {username} (role: {role}, table: {table_name}, user_id: {user_id})")
        cursor.close()
        return result
    
    except Exception as e:
        conn.rollback()
        result["message"] = f"Registration error: {str(e)}"
        logger.error(f"Error registering user '{username}' in DB: {e}")
        return result


def authenticate_user_db(username: str, password: str, role: str, conn) -> dict:
    result = {
        "authenticated": False,
        "role": None,
        "message": "",
        "username": username
    }
    
    try:
        # Validate role
        valid_roles = ["Sales Associate", "Store Manager", "Executive"]
        if role not in valid_roles:
            result["message"] = f"Invalid role '{role}'"
            logger.warning(f"Login failed: Invalid role '{role}'")
            return result
        
        table_name = get_user_table_name(role)
        cursor = conn.cursor()
        
        # Query user from role-specific table
        cursor.execute(
            f"""
            SELECT user_id, username, password_hash, role 
            FROM {table_name} 
            WHERE username = %s AND is_active = TRUE
            """,
            (username,)
        )
        user_row = cursor.fetchone()
        cursor.close()
        
        if not user_row:
            result["message"] = f"User '{username}' not found in {role} database"
            logger.warning(f"Login failed: User '{username}' not found in {table_name}")
            return result
        
        user_id, db_username, stored_hash, db_role = user_row
        
        # Verify password
        if verify_password(password, stored_hash):
            result["authenticated"] = True
            result["role"] = db_role
            result["message"] = "Authentication successful"
            
            # Update last_login timestamp
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {table_name} SET last_login = NOW() WHERE user_id = %s",
                (user_id,)
            )
            conn.commit()
            cursor.close()
            
            logger.info(f"User '{username}' authenticated successfully from {table_name}")
        else:
            result["message"] = "Invalid password"
            logger.warning(f"Login failed for '{username}': Invalid password")
    
    except Exception as e:
        result["message"] = f"Authentication error: {str(e)}"
        logger.error(f"Error authenticating user '{username}': {e}")
    
    return result


def store_security_answers_db(username: str, role: str, answers: dict, conn) -> dict:
    result = {
        "success": False,
        "message": ""
    }
    
    try:
        table_name = get_user_table_name(role)
        cursor = conn.cursor()
        
        # Hash all answers
        hashed_answers = {}
        for idx, answer in answers.items():
            hashed_answers[str(idx)] = hash_password(answer)
        
        # Store as JSONB in database
        import json
        cursor.execute(
            f"""
            UPDATE {table_name}
            SET security_answers = %s
            WHERE username = %s
            """,
            (json.dumps(hashed_answers), username)
        )
        conn.commit()
        cursor.close()
        
        result["success"] = True
        result["message"] = f"Security answers stored for '{username}'"
        logger.info(f"Security answers stored for user '{username}' in {table_name}")
        return result
    
    except Exception as e:
        conn.rollback()
        result["message"] = f"Error storing security answers: {str(e)}"
        logger.error(f"Error storing security answers for '{username}': {e}")
        return result


def get_security_answers_db(username: str, role: str, conn) -> dict:
    try:
        table_name = get_user_table_name(role)
        cursor = conn.cursor()
        
        cursor.execute(
            f"""
            SELECT security_answers 
            FROM {table_name}
            WHERE username = %s
            """,
            (username,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result and result[0]:
            import json
            answers = result[0]
            # Handle both JSON strings (MySQL) and dict/JSONB (PostgreSQL)
            if isinstance(answers, str):
                return json.loads(answers)
            elif isinstance(answers, dict):
                return answers
            else:
                return {}
        return {}
    
    except Exception as e:
        logger.error(f"Error retrieving security answers for '{username}': {e}")
        return {}


def reset_password_db(username: str, role: str, new_password: str, conn) -> dict:
    result = {
        "success": False,
        "message": ""
    }
    
    try:
        import uuid
        from datetime import datetime, timedelta
        
        # Validate password strength
        strength_result = validate_password_strength(new_password)
        if strength_result['strength'] != 'strong':
            missing = ', '.join(strength_result['requirements'])
            result["message"] = f"New password is too weak. Missing: {missing}"
            logger.warning(f"Password reset failed for '{username}': Weak password")
            return result
        
        table_name = get_user_table_name(role)
        new_password_hash = hash_password(new_password)
        
        cursor = conn.cursor()
        
        # Get user_id and current password first
        cursor.execute(f'SELECT user_id, password_hash FROM {table_name} WHERE username = %s', (username,))
        user_result = cursor.fetchone()
        if not user_result:
            result["message"] = f"User '{username}' not found"
            cursor.close()
            return result
        
        user_id = user_result[0]
        current_password_hash = user_result[1]
        
        # Check if new password matches current password
        if verify_password(new_password, current_password_hash):
            result["message"] = "❌ New password cannot be the same as your current password"
            cursor.close()
            return result
        
        # Determine history table name
        if role == "Sales Associate":
            history_table = "fa25_ssc_password_history_sales"
        elif role == "Store Manager":
            history_table = "fa25_ssc_password_history_manager"
        else:  # Executive
            history_table = "fa25_ssc_password_history_executive"
        
        # Check if new password was used before (in history)
        cursor.execute(f'SELECT old_password_hash FROM {history_table} WHERE user_id = %s ORDER BY changed_at DESC LIMIT 5', (user_id,))
        history_rows = cursor.fetchall()
        
        for (old_hash,) in history_rows:
            if verify_password(new_password, old_hash):
                result["message"] = "❌ You cannot reuse a previously used password. Please choose a different password"
                cursor.close()
                return result
        
        # Password is valid and new - proceed with update
        # Store current password in history before updating
        cursor.execute(
            f"""
            INSERT INTO {history_table} (user_id, old_password_hash)
            VALUES (%s, %s)
            """,
            (user_id, current_password_hash)
        )
        
        # Update password
        cursor.execute(
            f"""
            UPDATE {table_name}
            SET password_hash = %s
            WHERE username = %s
            """,
            (new_password_hash, username)
        )
        
        # Create token record in password reset tokens table
        token_string = str(uuid.uuid4())
        token_hash = hash_password(token_string)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Determine token table name
        if role == "Sales Associate":
            token_table = "fa25_ssc_password_reset_tokens_sales"
        elif role == "Store Manager":
            token_table = "fa25_ssc_password_reset_tokens_manager"
        else:  # Executive
            token_table = "fa25_ssc_password_reset_tokens_executive"
        
        cursor.execute(
            f"""
            INSERT INTO {token_table} (user_id, token_hash, expires_at, used)
            VALUES (%s, %s, %s, TRUE)
            """,
            (user_id, token_hash, expires_at)
        )
        
        conn.commit()
        cursor.close()
        
        result["success"] = True
        result["message"] = f"Password reset successfully for '{username}'"
        logger.info(f"Password reset in DB for user '{username}' in {table_name}")
        return result
    
    except Exception as e:
        conn.rollback()
        result["message"] = f"Error resetting password: {str(e)}"
        logger.error(f"Error resetting password for '{username}': {e}")
        return result


# Password history check

def check_password_history(username: str, role: str, new_password: str, conn) -> dict:
    result = {"is_reused": False, "message": "Password not in history"}
    
    try:
        cursor = conn.cursor()
        
        # Determine table names based on role
        if role == "Sales Associate":
            history_table = "fa25_ssc_password_history_sales"
            user_table = "fa25_ssc_users_sales_associate"
            user_id_col = "user_id"
        elif role == "Store Manager":
            history_table = "fa25_ssc_password_history_manager"
            user_table = "fa25_ssc_users_store_manager"
            user_id_col = "user_id"
        else:  # Executive
            history_table = "fa25_ssc_password_history_executive"
            user_table = "fa25_ssc_users_executive"
            user_id_col = "user_id"
        
        # Get user ID
        cursor.execute(f"SELECT {user_id_col} FROM {user_table} WHERE username = %s", (username,))
        user_record = cursor.fetchone()
        
        if not user_record:
            cursor.close()
            return result
        
        user_id = user_record[0]
        
        # Get last 5 password hashes from history
        cursor.execute(
            f"""
            SELECT old_password_hash FROM {history_table}
            WHERE user_id = %s
            ORDER BY changed_at DESC
            LIMIT 5
            """,
            (user_id,)
        )
        
        history_records = cursor.fetchall()
        cursor.close()
        
        # Check if new password matches any old password
        if history_records:
            logger.debug(f"Found {len(history_records)} old password hashes for user '{username}'")
        for record in history_records:
            old_hash = record[0]
            if verify_password(new_password, old_hash):
                result["is_reused"] = True
                result["message"] = "Password was recently used"
                logger.warning(f"Password reuse attempt for user '{username}'")
                return result
        
        logger.debug(f"Password check complete for user '{username}' - not reused")
        return result
    
    except Exception as e:
        logger.error(f"Error checking password history for '{username}': {e}")
        return result


logger.info("Auth module loaded")


