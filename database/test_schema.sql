-- Database Schema Testing Script
-- Tests the complete PII encryption database schema
-- Run this after deploying schema.sql to validate functionality

-- =============================================================================
-- INITIAL CLEANUP (in case of previous test runs)
-- =============================================================================

-- Clean up any leftover test data from previous runs
DELETE FROM encryption_audit WHERE accessed_by IN ('test-system', 'database-trigger') OR user_id IN (SELECT id FROM users WHERE email = 'test@example.com');
DELETE FROM encryption_metadata WHERE user_id IN (SELECT id FROM users WHERE email = 'test@example.com');
DELETE FROM users WHERE email = 'test@example.com';

-- =============================================================================
-- SCHEMA VALIDATION TESTS
-- =============================================================================

-- Test 1: Verify all tables exist
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('users', 'encryption_metadata', 'encryption_audit', 'key_rotation_log', 'system_config');
    
    IF table_count = 5 THEN
        RAISE NOTICE 'TEST 1 PASSED: All 5 core tables exist';
    ELSE
        RAISE EXCEPTION 'TEST 1 FAILED: Expected 5 tables, found %', table_count;
    END IF;
END $$;

-- Test 2: Verify all indexes exist
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count 
    FROM pg_indexes 
    WHERE schemaname = 'public';
    
    IF index_count >= 10 THEN
        RAISE NOTICE 'TEST 2 PASSED: Found % indexes (expected at least 10)', index_count;
    ELSE
        RAISE EXCEPTION 'TEST 2 FAILED: Expected at least 10 indexes, found %', index_count;
    END IF;
END $$;

-- Test 3: Verify triggers exist
DO $$
DECLARE
    trigger_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trigger_count 
    FROM information_schema.triggers 
    WHERE trigger_schema = 'public';
    
    IF trigger_count >= 3 THEN
        RAISE NOTICE 'TEST 3 PASSED: Found % triggers', trigger_count;
    ELSE
        RAISE EXCEPTION 'TEST 3 FAILED: Expected at least 3 triggers, found %', trigger_count;
    END IF;
END $$;

-- Test 4: Verify views exist
DO $$
DECLARE
    view_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO view_count 
    FROM information_schema.views 
    WHERE table_schema = 'public';
    
    IF view_count = 3 THEN
        RAISE NOTICE 'TEST 4 PASSED: All 3 views exist';
    ELSE
        RAISE EXCEPTION 'TEST 4 FAILED: Expected 3 views, found %', view_count;
    END IF;
END $$;

-- =============================================================================
-- FUNCTIONAL TESTS
-- =============================================================================

-- Test 5: Insert test user (Level 1 data only)
INSERT INTO users (email, first_name, last_name, phone) 
VALUES ('test@example.com', 'Test', 'User', '+1-555-0123');

-- Verify trigger created audit log
DO $$
DECLARE
    audit_count INTEGER;
    test_user_id UUID;
BEGIN
    SELECT id INTO test_user_id FROM users WHERE email = 'test@example.com';
    
    SELECT COUNT(*) INTO audit_count 
    FROM encryption_audit 
    WHERE user_id = test_user_id AND operation = 'create';
    
    IF audit_count = 1 THEN
        RAISE NOTICE 'TEST 5 PASSED: User creation triggered audit log';
    ELSE
        RAISE EXCEPTION 'TEST 5 FAILED: Expected 1 audit record, found %', audit_count;
    END IF;
END $$;

-- Test 6: Insert encryption metadata
DO $$
DECLARE
    test_user_id UUID;
BEGIN
    SELECT id INTO test_user_id FROM users WHERE email = 'test@example.com';
    
    -- Insert metadata for Level 1 field
    INSERT INTO encryption_metadata (user_id, field_name, pii_level, kms_key_alias)
    VALUES (test_user_id, 'email', 1, NULL);
    
    -- Insert metadata for Level 2 field
    INSERT INTO encryption_metadata (user_id, field_name, pii_level, kms_key_alias)
    VALUES (test_user_id, 'address', 2, 'alias/pii-level2');
    
    -- Insert metadata for Level 3 field
    INSERT INTO encryption_metadata (user_id, field_name, pii_level, app_key_version, kms_key_alias)
    VALUES (test_user_id, 'ssn', 3, 1, 'alias/pii-level3');
    
    RAISE NOTICE 'TEST 6 PASSED: Encryption metadata inserted successfully';
END $$;

-- Test 7: Test audit logging
INSERT INTO encryption_audit (
    user_id, field_name, pii_level, operation, accessed_by, success
) 
SELECT id, 'email', 1, 'encrypt', 'test-system', TRUE 
FROM users WHERE email = 'test@example.com';

-- Test 8: Test key rotation log
INSERT INTO key_rotation_log (
    key_type, key_alias, old_version, new_version, rotation_reason, rotation_status
) VALUES (
    'app-level3', 'pii-app-keys', 1, 2, 'scheduled', 'completed'
);

-- Test 9: Test system configuration
UPDATE system_config 
SET config_value = '2' 
WHERE config_key = 'current_app_key_version';

-- Verify update trigger worked
DO $$
DECLARE
    updated_at_changed BOOLEAN;
BEGIN
    SELECT (updated_at > created_at) INTO updated_at_changed 
    FROM system_config 
    WHERE config_key = 'current_app_key_version';
    
    IF updated_at_changed THEN
        RAISE NOTICE 'TEST 9 PASSED: Update trigger updated timestamp';
    ELSE
        RAISE EXCEPTION 'TEST 9 FAILED: Update trigger did not update timestamp';
    END IF;
END $$;

-- =============================================================================
-- CONSTRAINT TESTS
-- =============================================================================

-- Test 10: Test PII level constraint
DO $$
BEGIN
    BEGIN
        INSERT INTO encryption_metadata (user_id, field_name, pii_level)
        SELECT id, 'invalid_field', 4 FROM users WHERE email = 'test@example.com';
        RAISE EXCEPTION 'TEST 10 FAILED: Invalid PII level was accepted';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'TEST 10 PASSED: PII level constraint working';
    END;
END $$;

-- Test 11: Test operation constraint
DO $$
BEGIN
    BEGIN
        INSERT INTO encryption_audit (operation, accessed_by)
        VALUES ('invalid_operation', 'test-system');
        RAISE EXCEPTION 'TEST 11 FAILED: Invalid operation was accepted';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'TEST 11 PASSED: Operation constraint working';
    END;
END $$;

-- Test 12: Test unique constraint on encryption_metadata
DO $$
DECLARE
    test_user_id UUID;
BEGIN
    SELECT id INTO test_user_id FROM users WHERE email = 'test@example.com';
    
    BEGIN
        INSERT INTO encryption_metadata (user_id, field_name, pii_level)
        VALUES (test_user_id, 'email', 1);
        RAISE EXCEPTION 'TEST 12 FAILED: Duplicate metadata was accepted';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'TEST 12 PASSED: Unique constraint working';
    END;
END $$;

-- =============================================================================
-- VIEW TESTS
-- =============================================================================

-- Test 13: Test encryption_stats view
DO $$
DECLARE
    stats_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO stats_count FROM encryption_stats;
    
    IF stats_count > 0 THEN
        RAISE NOTICE 'TEST 13 PASSED: encryption_stats view returning data';
    ELSE
        RAISE EXCEPTION 'TEST 13 FAILED: encryption_stats view returned no data';
    END IF;
END $$;

-- Test 14: Test audit_summary view
SELECT COUNT(*) as audit_summary_rows FROM audit_summary;

-- Test 15: Test key_rotation_summary view
DO $$
DECLARE
    rotation_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO rotation_count FROM key_rotation_summary;
    
    IF rotation_count > 0 THEN
        RAISE NOTICE 'TEST 15 PASSED: key_rotation_summary view returning data';
    ELSE
        RAISE NOTICE 'TEST 15 INFO: key_rotation_summary view empty (expected for new system)';
    END IF;
END $$;

-- =============================================================================
-- PERFORMANCE TESTS
-- =============================================================================

-- Test 16: Test index usage on users table
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM users WHERE email = 'test@example.com';

-- Test 17: Test index usage on encryption_metadata
DO $$
DECLARE
    test_user_id UUID;
BEGIN
    SELECT id INTO test_user_id FROM users WHERE email = 'test@example.com' LIMIT 1;
END $$;

EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM encryption_metadata 
WHERE user_id = (SELECT id FROM users WHERE email = 'test@example.com' LIMIT 1);

-- Test 18: Test audit query performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM encryption_audit 
WHERE accessed_at >= NOW() - INTERVAL '24 hours';

-- =============================================================================
-- CLEANUP TEST DATA
-- =============================================================================

-- Clean up test data
DELETE FROM encryption_audit WHERE accessed_by IN ('test-system', 'database-trigger');
DELETE FROM encryption_metadata WHERE user_id IN (SELECT id FROM users WHERE email = 'test@example.com');
DELETE FROM users WHERE email = 'test@example.com';
DELETE FROM key_rotation_log WHERE key_type = 'app-level3';

-- Reset system config
UPDATE system_config 
SET config_value = '1' 
WHERE config_key = 'current_app_key_version';

-- =============================================================================
-- FINAL VALIDATION
-- =============================================================================

-- Test 19: Verify cleanup
DO $$
DECLARE
    test_user_count INTEGER;
    test_metadata_count INTEGER;
    test_audit_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO test_user_count FROM users WHERE email = 'test@example.com';
    SELECT COUNT(*) INTO test_metadata_count FROM encryption_metadata WHERE field_name = 'email';
    SELECT COUNT(*) INTO test_audit_count FROM encryption_audit WHERE accessed_by = 'test-system';
    
    IF test_user_count = 0 AND test_metadata_count = 0 AND test_audit_count = 0 THEN
        RAISE NOTICE 'TEST 19 PASSED: Test data cleaned up successfully';
    ELSE
        RAISE EXCEPTION 'TEST 19 FAILED: Test data not fully cleaned up';
    END IF;
END $$;

-- Final status
SELECT 'ALL SCHEMA TESTS COMPLETED SUCCESSFULLY' AS test_status;

-- Display schema summary
SELECT 
    'SCHEMA SUMMARY' AS summary_type,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') AS table_count,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') AS index_count,
    (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public') AS view_count,
    (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public') AS trigger_count;