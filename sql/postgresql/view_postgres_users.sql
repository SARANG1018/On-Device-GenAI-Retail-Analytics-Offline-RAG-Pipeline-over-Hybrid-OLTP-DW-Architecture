-- View user tables

SELECT user_id, username, role, is_active, created_at 
FROM FA25_SSC_USERS_SALES_ASSOCIATE 
ORDER BY created_at DESC;

SELECT token_id, user_id, created_at, expires_at 
FROM FA25_SSC_PASSWORD_RESET_TOKENS_SALES 
ORDER BY created_at DESC;
