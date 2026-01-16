
-- Drop existing tables if they exist (for migration/reset)
DROP TABLE IF EXISTS FA25_SSC_PASSWORD_RESET_TOKENS_SALES CASCADE;
DROP TABLE IF EXISTS FA25_SSC_USERS_SALES_ASSOCIATE CASCADE;

-- Sales Associate User Table (PostgreSQL OLTP)
CREATE TABLE FA25_SSC_USERS_SALES_ASSOCIATE (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Sales Associate',
    security_answers JSONB,  -- Stores hashed answers: {"0": "$2b$12$...", "2": "$2b$12$..."}
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Index for faster lookups
CREATE INDEX idx_FA25_SSC_users_sales_associate_username ON FA25_SSC_USERS_SALES_ASSOCIATE(username);
CREATE INDEX idx_FA25_SSC_users_sales_associate_is_active ON FA25_SSC_USERS_SALES_ASSOCIATE(is_active);

-- Password Reset Tokens Table (PostgreSQL OLTP)
CREATE TABLE FA25_SSC_PASSWORD_RESET_TOKENS_SALES (
    token_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES FA25_SSC_USERS_SALES_ASSOCIATE(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE
);

-- Index for token lookups
CREATE INDEX idx_FA25_SSC_password_reset_tokens_sales_user_id ON FA25_SSC_PASSWORD_RESET_TOKENS_SALES(user_id);
CREATE INDEX idx_FA25_SSC_password_reset_tokens_sales_token_hash ON FA25_SSC_PASSWORD_RESET_TOKENS_SALES(token_hash);
CREATE INDEX idx_FA25_SSC_password_reset_tokens_sales_expires_at ON FA25_SSC_PASSWORD_RESET_TOKENS_SALES(expires_at);

-- Password History Table (PostgreSQL OLTP)
CREATE TABLE FA25_SSC_PASSWORD_HISTORY_SALES (
    history_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES FA25_SSC_USERS_SALES_ASSOCIATE(user_id) ON DELETE CASCADE,
    old_password_hash VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for history lookups
CREATE INDEX idx_FA25_SSC_password_history_sales_user_id ON FA25_SSC_PASSWORD_HISTORY_SALES(user_id);


-- Comments
COMMENT ON TABLE FA25_SSC_USERS_SALES_ASSOCIATE IS 'Stores Sales Associate user credentials (bcrypt hashed passwords and security answers)';
COMMENT ON COLUMN FA25_SSC_USERS_SALES_ASSOCIATE.security_answers IS 'JSON object with bcrypt-hashed security question answers: {question_index: hashed_answer}';
COMMENT ON TABLE FA25_SSC_PASSWORD_RESET_TOKENS_SALES IS 'Stores temporary tokens for password reset requests with expiration';
COMMENT ON TABLE FA25_SSC_PASSWORD_HISTORY_SALES IS 'Stores previous password hashes to prevent reuse';
