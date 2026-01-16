-- VERIFY CDC INDEXES ARE WORKING

-- Show all CDC indexes and their status
SELECT 
    schemaname,
    relname as table_name,
    indexrelname as index_name,
    idx_scan as scans_count,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE indexrelname LIKE 'idx_%tbl_last_dt'
ORDER BY relname;

-- Quick CDC query test (what ETL runs)
SELECT COUNT(*) as "Recent ORDER changes (last 24h)"
FROM "FA25_SSC_ORDER"
WHERE tbl_last_dt > NOW() - INTERVAL '24 hours';

SELECT COUNT(*) as "Recent ORDER_PRODUCT changes (last 24h)"
FROM "FA25_SSC_ORDER_PRODUCT"
WHERE tbl_last_dt > NOW() - INTERVAL '24 hours';

SELECT COUNT(*) as "Recent RETURN changes (last 24h)"
FROM "FA25_SSC_RETURN"
WHERE tbl_last_dt > NOW() - INTERVAL '24 hours';
