
-- SIMPLE TRIGGER TEST

-- Insert a new SEGMENT and check if tbl_last_dt is auto-set
BEGIN;

-- Insert with tbl_last_dt = old date (trigger should override it)
INSERT INTO "FA25_SSC_SEGMENT" (segment_id, segment_name, tbl_last_dt) 
VALUES ('TRIGGER_TEST', 'Test Segment', '1900-01-01'::timestamp)
RETURNING segment_id, segment_name, tbl_last_dt;

-- Clean up
DELETE FROM "FA25_SSC_SEGMENT" WHERE segment_id = 'TRIGGER_TEST';

COMMIT;
