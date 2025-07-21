-- PII Encryption System Database Schema
-- PostgreSQL 16+ with AWS Aurora
-- This schema supports three-tier PII encryption levels

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- MAIN USERS TABLE
-- Supports mixed encryption levels:
-- Level 1: Clear text (RDS at-rest encryption only)
-- Level 2: KMS encrypted fields (stored as encrypted blobs)
-- Level 3: Double encrypted fields (App + KMS, stored as encrypted blobs)
-- =============================================================================

CREATE TABLE users (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- LEVEL 1 FIELDS (Low Sensitivity - Clear Text)
    -- Only protected by RDS at-rest encryption
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    
    -- LEVEL 2 FIELDS (Medium Sensitivity - KMS Encrypted)
    -- Field-level encryption using AWS KMS Customer Managed Keys
    address_encrypted TEXT,
    date_of_birth_encrypted TEXT,
    ip_address_encrypted TEXT,
    
    -- LEVEL 3 FIELDS (High Sensitivity - Double Encrypted)
    -- Application-layer encryption + AWS KMS encryption
    ssn_encrypted TEXT,
    bank_account_encrypted TEXT,
    credit_card_encrypted TEXT,
    
    -- System timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient email lookups (Level 1 queryable field)
CREATE INDEX idx_users_email ON users(email);

-- Index for timestamp-based queries
CREATE INDEX idx_users_created_at ON users(created_at);

-- =============================================================================
-- ENCRYPTION METADATA TABLE
-- Tracks encryption details for key version management and audit
-- =============================================================================

CREATE TABLE encryption_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    field_name VARCHAR(50) NOT NULL,
    pii_level INTEGER NOT NULL CHECK (pii_level IN (1, 2, 3)),
    
    -- Key version tracking for rotation support
    app_key_version INTEGER, -- For Level 3 application-layer keys
    kms_key_alias VARCHAR(100), -- KMS key used for encryption
    
    -- Encryption algorithm details
    encryption_algorithm VARCHAR(50) DEFAULT 'AES-256-GCM',
    
    -- Timestamps
    encrypted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one metadata record per user-field combination
    UNIQUE(user_id, field_name)
);

-- Index for efficient metadata lookups
CREATE INDEX idx_encryption_metadata_user_field ON encryption_metadata(user_id, field_name);
CREATE INDEX idx_encryption_metadata_level ON encryption_metadata(pii_level);

-- =============================================================================
-- ENCRYPTION AUDIT TABLE
-- Comprehensive audit trail for all encryption/decryption operations
-- Supports compliance requirements (GDPR, CCPA, PCI DSS)
-- =============================================================================

CREATE TABLE encryption_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Reference data
    user_id UUID REFERENCES users(id),
    field_name VARCHAR(50),
    pii_level INTEGER,
    
    -- Operation details
    operation VARCHAR(20) NOT NULL CHECK (operation IN ('encrypt', 'decrypt', 'view', 'create', 'update', 'delete')),
    accessed_by VARCHAR(255) NOT NULL, -- Service or user identifier
    
    -- Request context
    ip_address VARCHAR(45), -- IPv4 or IPv6
    user_agent TEXT,
    request_id VARCHAR(100), -- For request correlation
    
    -- Operation result
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- Performance tracking
    operation_duration_ms INTEGER,
    
    -- Compliance fields
    data_classification VARCHAR(20),
    retention_policy VARCHAR(50),
    
    -- Timestamp
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for audit queries and compliance reporting
CREATE INDEX idx_encryption_audit_user_time ON encryption_audit(user_id, accessed_at DESC);
CREATE INDEX idx_encryption_audit_operation ON encryption_audit(operation);
CREATE INDEX idx_encryption_audit_success ON encryption_audit(success);
CREATE INDEX idx_encryption_audit_pii_level ON encryption_audit(pii_level);
CREATE INDEX idx_encryption_audit_accessed_by ON encryption_audit(accessed_by);

-- =============================================================================
-- KEY ROTATION LOG TABLE
-- Tracks key rotation events for compliance and operational purposes
-- =============================================================================

CREATE TABLE key_rotation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Key details
    key_type VARCHAR(50) NOT NULL, -- 'kms-level2', 'kms-level3', 'app-level3'
    key_alias VARCHAR(100),
    
    -- Rotation details
    old_version INTEGER,
    new_version INTEGER,
    rotation_reason VARCHAR(100), -- 'scheduled', 'security-incident', 'manual'
    
    -- Rotation process
    rotation_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rotation_completed_at TIMESTAMP WITH TIME ZONE,
    rotation_status VARCHAR(20) DEFAULT 'in_progress' CHECK (rotation_status IN ('in_progress', 'completed', 'failed', 'rolled_back')),
    
    -- Impact tracking
    records_affected INTEGER DEFAULT 0,
    fields_affected TEXT[], -- Array of field names affected
    
    -- Error handling
    error_message TEXT,
    rollback_completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    initiated_by VARCHAR(255),
    rotation_method VARCHAR(50) -- 'automatic', 'manual'
);

-- Index for rotation history queries
CREATE INDEX idx_key_rotation_log_key_type ON key_rotation_log(key_type);
CREATE INDEX idx_key_rotation_log_status ON key_rotation_log(rotation_status);
CREATE INDEX idx_key_rotation_log_started_at ON key_rotation_log(rotation_started_at DESC);

-- =============================================================================
-- SYSTEM CONFIGURATION TABLE
-- Stores system-wide encryption configuration and settings
-- =============================================================================

CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) DEFAULT 'string' CHECK (config_type IN ('string', 'integer', 'boolean', 'json')),
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default configuration values
INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
('current_app_key_version', '1', 'integer', 'Current version of application encryption keys'),
('encryption_enabled', 'true', 'boolean', 'Global encryption enablement flag'),
('audit_retention_days', '2555', 'integer', 'Audit log retention period (7 years)'),
('max_failed_decryption_attempts', '5', 'integer', 'Maximum failed decryption attempts before alerting'),
('key_rotation_schedule_days', '90', 'integer', 'Automatic key rotation schedule in days');

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for system_config table
CREATE TRIGGER update_system_config_updated_at 
    BEFORE UPDATE ON system_config 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically log user operations
CREATE OR REPLACE FUNCTION log_user_operation()
RETURNS TRIGGER AS $$
BEGIN
    -- Log user creation
    IF TG_OP = 'INSERT' THEN
        INSERT INTO encryption_audit (
            user_id, operation, accessed_by, success, 
            data_classification, accessed_at
        ) VALUES (
            NEW.id, 'create', 'database-trigger', TRUE,
            'mixed-pii', NOW()
        );
        RETURN NEW;
    END IF;
    
    -- Log user updates
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO encryption_audit (
            user_id, operation, accessed_by, success,
            data_classification, accessed_at
        ) VALUES (
            NEW.id, 'update', 'database-trigger', TRUE,
            'mixed-pii', NOW()
        );
        RETURN NEW;
    END IF;
    
    -- Log user deletion
    IF TG_OP = 'DELETE' THEN
        INSERT INTO encryption_audit (
            user_id, operation, accessed_by, success,
            data_classification, accessed_at
        ) VALUES (
            OLD.id, 'delete', 'database-trigger', TRUE,
            'mixed-pii', NOW()
        );
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Trigger for automatic audit logging on user operations
-- Note: DELETE must be BEFORE to ensure user_id still exists for foreign key
CREATE TRIGGER log_user_operations_insert_update
    AFTER INSERT OR UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION log_user_operation();

CREATE TRIGGER log_user_operations_delete
    BEFORE DELETE ON users
    FOR EACH ROW
    EXECUTE FUNCTION log_user_operation();

-- =============================================================================
-- VIEWS FOR REPORTING AND ANALYTICS
-- =============================================================================

-- View for encryption statistics
CREATE VIEW encryption_stats AS
SELECT 
    pii_level,
    COUNT(*) as field_count,
    COUNT(DISTINCT user_id) as users_with_level,
    AVG(EXTRACT(EPOCH FROM (NOW() - encrypted_at))) as avg_age_seconds
FROM encryption_metadata 
GROUP BY pii_level;

-- View for audit summary
CREATE VIEW audit_summary AS
SELECT 
    DATE(accessed_at) as audit_date,
    operation,
    pii_level,
    COUNT(*) as operation_count,
    COUNT(CASE WHEN success = FALSE THEN 1 END) as failed_count,
    AVG(operation_duration_ms) as avg_duration_ms
FROM encryption_audit 
WHERE accessed_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(accessed_at), operation, pii_level
ORDER BY audit_date DESC;

-- View for key rotation history
CREATE VIEW key_rotation_summary AS
SELECT 
    key_type,
    COUNT(*) as total_rotations,
    COUNT(CASE WHEN rotation_status = 'completed' THEN 1 END) as successful_rotations,
    COUNT(CASE WHEN rotation_status = 'failed' THEN 1 END) as failed_rotations,
    MAX(rotation_completed_at) as last_successful_rotation,
    SUM(records_affected) as total_records_affected
FROM key_rotation_log
GROUP BY key_type;

-- =============================================================================
-- SECURITY AND PERMISSIONS
-- =============================================================================

-- Create application-specific roles
CREATE ROLE pii_app_read;
CREATE ROLE pii_app_write;
CREATE ROLE pii_app_audit;

-- Grant read permissions
GRANT SELECT ON users, encryption_metadata, system_config TO pii_app_read;
GRANT SELECT ON encryption_stats, audit_summary, key_rotation_summary TO pii_app_read;

-- Grant write permissions
GRANT SELECT, INSERT, UPDATE ON users, encryption_metadata TO pii_app_write;
GRANT SELECT, UPDATE ON system_config TO pii_app_write;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pii_app_write;

-- Grant audit permissions
GRANT SELECT, INSERT ON encryption_audit, key_rotation_log TO pii_app_audit;
GRANT SELECT ON audit_summary, key_rotation_summary TO pii_app_audit;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE users IS 'Main user table supporting three-tier PII encryption levels';
COMMENT ON COLUMN users.email IS 'Level 1: Clear text, RDS encryption only';
COMMENT ON COLUMN users.address_encrypted IS 'Level 2: KMS encrypted field';
COMMENT ON COLUMN users.ssn_encrypted IS 'Level 3: Double encrypted (App + KMS)';

COMMENT ON TABLE encryption_metadata IS 'Tracks encryption details and key versions for each user field';
COMMENT ON TABLE encryption_audit IS 'Comprehensive audit trail for compliance (GDPR, CCPA, PCI DSS)';
COMMENT ON TABLE key_rotation_log IS 'Tracks key rotation events and impact';
COMMENT ON TABLE system_config IS 'System-wide encryption configuration settings';

-- =============================================================================
-- SAMPLE DATA FOR TESTING (Optional - Remove in production)
-- =============================================================================

-- Insert sample configuration for development
-- REMOVE THIS SECTION FOR PRODUCTION DEPLOYMENT
/*
INSERT INTO users (email, first_name, last_name, phone) VALUES 
('test@example.com', 'Test', 'User', '+1-555-0123');

INSERT INTO encryption_metadata (user_id, field_name, pii_level, kms_key_alias) 
SELECT id, 'email', 1, NULL FROM users WHERE email = 'test@example.com';
*/

-- Schema creation completed
SELECT 'PII Encryption System database schema created successfully' AS status;