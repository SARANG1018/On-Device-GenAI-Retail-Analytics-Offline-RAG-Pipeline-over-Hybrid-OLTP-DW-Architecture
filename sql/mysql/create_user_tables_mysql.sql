
-- Store Manager User Table (MySQL OLAP)
CREATE TABLE IF NOT EXISTS FA25_SSC_USERS_STORE_MANAGER (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Store Manager',
    security_answers JSON,  -- Stores hashed answers: {"0": "$2b$12$...", "2": "$2b$12$..."}
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Executive User Table (MySQL OLAP)
CREATE TABLE IF NOT EXISTS FA25_SSC_USERS_EXECUTIVE (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Executive',
    security_answers JSON,  -- Stores hashed answers: {"0": "$2b$12$...", "2": "$2b$12$..."}
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Password Reset Tokens Table for Store Manager (MySQL OLAP)
CREATE TABLE IF NOT EXISTS FA25_SSC_PASSWORD_RESET_TOKENS_MANAGER (
    token_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    INDEX idx_user_id (user_id),
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at),
    FOREIGN KEY (user_id) REFERENCES FA25_SSC_USERS_STORE_MANAGER(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Password Reset Tokens Table for Executive (MySQL OLAP)
CREATE TABLE IF NOT EXISTS FA25_SSC_PASSWORD_RESET_TOKENS_EXECUTIVE (
    token_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    INDEX idx_user_id (user_id),
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at),
    FOREIGN KEY (user_id) REFERENCES FA25_SSC_USERS_EXECUTIVE(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Password History Tables (MySQL OLAP)
CREATE TABLE FA25_SSC_PASSWORD_HISTORY_MANAGER (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    old_password_hash VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES FA25_SSC_USERS_STORE_MANAGER(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE FA25_SSC_PASSWORD_HISTORY_EXECUTIVE (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    old_password_hash VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES FA25_SSC_USERS_EXECUTIVE(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Comments
-- FA25_SSC_USERS_STORE_MANAGER: Stores Store Manager user credentials (bcrypt hashed passwords and security answers)
-- FA25_SSC_USERS_EXECUTIVE: Stores Executive user credentials (bcrypt hashed passwords and security answers)
-- FA25_SSC_PASSWORD_RESET_TOKENS_MANAGER: Stores temporary tokens for Store Manager password reset with expiration
-- FA25_SSC_PASSWORD_RESET_TOKENS_EXECUTIVE: Stores temporary tokens for Executive password reset with expiration
-- FA25_SSC_PASSWORD_HISTORY_MANAGER: Stores previous password hashes to prevent reuse for Store Manager
-- FA25_SSC_PASSWORD_HISTORY_EXECUTIVE: Stores previous password hashes to prevent reuse for Executive
