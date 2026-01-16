-- View user tables

USE awesome_inc_dw;

SELECT user_id, username, role, is_active, created_at 
FROM FA25_SSC_USERS_STORE_MANAGER 
ORDER BY created_at DESC;

SELECT user_id, username, role, is_active, created_at 
FROM FA25_SSC_USERS_EXECUTIVE 
ORDER BY created_at DESC;

SELECT token_id, user_id, created_at, expires_at 
FROM FA25_SSC_PASSWORD_RESET_TOKENS_MANAGER 
ORDER BY created_at DESC;

SELECT token_id, user_id, created_at, expires_at 
FROM FA25_SSC_PASSWORD_RESET_TOKENS_EXECUTIVE 
ORDER BY created_at DESC;
