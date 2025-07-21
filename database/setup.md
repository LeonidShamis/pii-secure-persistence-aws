# Database Setup Guide

## Overview

This guide covers the setup of AWS RDS Aurora PostgreSQL for the PII Encryption System prototype. The database supports three-tier encryption levels and comprehensive audit logging.

## Prerequisites

- AWS CLI configured with appropriate permissions
- PostgreSQL client tools installed
- VPC and subnets configured for private database deployment

## Aurora PostgreSQL Configuration

### 1. Create Aurora Cluster

```bash
# Create Aurora PostgreSQL cluster with encryption at rest
aws rds create-db-cluster \
    --db-cluster-identifier pii-database-cluster \
    --engine aurora-postgresql \
    --engine-version 16.6 \
    --master-username postgres \
    --master-user-password [SECURE_PASSWORD] \
    --database-name pii_db \
    --storage-encrypted \
    --kms-key-id alias/aws/rds \
    --vpc-security-group-ids [SECURITY_GROUP_ID] \
    --db-subnet-group-name [SUBNET_GROUP_NAME] \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00" \
    --preferred-maintenance-window "sun:04:00-sun:05:00" \
    --enable-cloudwatch-logs-exports postgresql \
    --tags Key=Environment,Value=prototype Key=Project,Value=pii-encryption
```

### 2. Create Aurora Instance

```bash
# Create Aurora instance
aws rds create-db-instance \
    --db-instance-identifier pii-database-instance-1 \
    --db-instance-class db.t3.medium \
    --engine aurora-postgresql \
    --db-cluster-identifier pii-database-cluster \
    --publicly-accessible false \
    --tags Key=Environment,Value=prototype Key=Project,Value=pii-encryption
```

### 3. Security Configuration

#### Security Group Rules
```bash
# Create security group for database
aws ec2 create-security-group \
    --group-name pii-database-sg \
    --description "Security group for PII encryption database" \
    --vpc-id [VPC_ID]

# Allow PostgreSQL access from Lambda subnet only
aws ec2 authorize-security-group-ingress \
    --group-id [SECURITY_GROUP_ID] \
    --protocol tcp \
    --port 5432 \
    --source-group [LAMBDA_SECURITY_GROUP_ID]
```

#### DB Subnet Group
```bash
# Create DB subnet group for private subnets
aws rds create-db-subnet-group \
    --db-subnet-group-name pii-db-subnet-group \
    --db-subnet-group-description "Private subnets for PII database" \
    --subnet-ids [PRIVATE_SUBNET_1] [PRIVATE_SUBNET_2]
```

## Database Schema Deployment

### 1. Connect to Database

```bash
# Connect via bastion host or VPN
psql -h [AURORA_ENDPOINT] -U postgres -d pii_db
```

### 2. Execute Schema

```bash
# Execute the schema file
psql -h [AURORA_ENDPOINT] -U postgres -d pii_db -f schema.sql
```

### 3. Verify Installation

```sql
-- Check that all tables were created
\dt

-- Verify extensions
\dx

-- Check sample configuration
SELECT * FROM system_config;

-- Verify triggers
SELECT trigger_name, event_manipulation, event_object_table 
FROM information_schema.triggers 
WHERE trigger_schema = 'public';
```

## Database Schema Overview

### Core Tables

1. **`users`** - Main user data with mixed encryption levels
   - Level 1 fields: `email`, `first_name`, `last_name`, `phone` (clear text)
   - Level 2 fields: `address_encrypted`, `date_of_birth_encrypted`, `ip_address_encrypted` (KMS)
   - Level 3 fields: `ssn_encrypted`, `bank_account_encrypted`, `credit_card_encrypted` (double encrypted)

2. **`encryption_metadata`** - Key version tracking and encryption details
   - Supports key rotation with version tracking
   - Links encrypted fields to specific KMS keys and app key versions

3. **`encryption_audit`** - Comprehensive audit trail
   - All encryption/decryption operations logged
   - Compliance-ready (GDPR, CCPA, PCI DSS)
   - Performance and error tracking

4. **`key_rotation_log`** - Key rotation history
   - Tracks rotation events and impact
   - Supports rollback scenarios

5. **`system_config`** - System-wide configuration
   - Encryption settings and parameters
   - Key version management

### Indexes

- **Performance**: `idx_users_email`, `idx_users_created_at`
- **Metadata**: `idx_encryption_metadata_user_field`, `idx_encryption_metadata_level`
- **Audit**: `idx_encryption_audit_user_time`, `idx_encryption_audit_operation`
- **Rotation**: `idx_key_rotation_log_key_type`, `idx_key_rotation_log_status`

### Views

- **`encryption_stats`** - Encryption level statistics
- **`audit_summary`** - Daily audit operation summary
- **`key_rotation_summary`** - Key rotation history summary

## Security Features

### Database-Level Security

1. **Encryption at Rest**: AWS KMS encryption enabled
2. **Network Isolation**: Private subnet deployment
3. **Access Control**: Security groups with minimal access
4. **Audit Logging**: Comprehensive operation tracking

### Application-Level Security

1. **Role-Based Access**: Separate roles for read/write/audit operations
2. **Least Privilege**: Minimal permissions for each role
3. **Automatic Logging**: Triggers for all user operations

### Compliance Features

1. **Audit Trail**: Complete operation history with timestamps
2. **Data Classification**: PII level tracking
3. **Retention Policies**: Configurable audit retention
4. **Key Management**: Rotation tracking and versioning

## Connection Configuration

### For Lambda Functions

```python
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Create database connection for Lambda"""
    return psycopg2.connect(
        host='[AURORA_ENDPOINT]',
        port=5432,
        database='pii_db',
        user='postgres',
        password='[PASSWORD_FROM_SECRETS_MANAGER]',
        cursor_factory=RealDictCursor,
        connect_timeout=10,
        sslmode='require'
    )
```

### For FastAPI Application

```python
import asyncpg

async def create_db_pool():
    """Create async connection pool for FastAPI"""
    return await asyncpg.create_pool(
        host='[AURORA_ENDPOINT]',
        port=5432,
        database='pii_db',
        user='postgres',
        password='[PASSWORD_FROM_SECRETS_MANAGER]',
        min_size=1,
        max_size=10,
        ssl='require'
    )
```

## Monitoring and Maintenance

### CloudWatch Metrics

Monitor these key metrics:
- DatabaseConnections
- CPUUtilization
- FreeableMemory
- ReadLatency / WriteLatency
- DatabaseErrors

### Audit Queries

```sql
-- Daily encryption operations
SELECT 
    DATE(accessed_at) as date,
    operation,
    COUNT(*) as count
FROM encryption_audit 
WHERE accessed_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(accessed_at), operation
ORDER BY date DESC;

-- Failed operations
SELECT * FROM encryption_audit 
WHERE success = FALSE 
AND accessed_at >= NOW() - INTERVAL '24 hours';

-- Key rotation status
SELECT * FROM key_rotation_summary;
```

## Backup and Recovery

### Automated Backups

- **Retention**: 7 days (configurable)
- **Window**: 03:00-04:00 UTC
- **Point-in-Time Recovery**: Enabled

### Manual Snapshots

```bash
# Create manual snapshot
aws rds create-db-cluster-snapshot \
    --db-cluster-identifier pii-database-cluster \
    --db-cluster-snapshot-identifier pii-db-manual-snapshot-$(date +%Y%m%d)
```

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Verify security group rules
   - Check VPC routing
   - Confirm subnet configuration

2. **Permission Denied**
   - Verify IAM roles
   - Check database user permissions
   - Confirm SSL configuration

3. **Performance Issues**
   - Monitor CloudWatch metrics
   - Check connection pool settings
   - Review query performance

### Useful Commands

```sql
-- Check active connections
SELECT * FROM pg_stat_activity;

-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public';

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes;
```

## Cost Optimization

### For Prototype

- Use `db.t3.medium` instance for basic workloads
- Enable storage autoscaling
- Monitor usage and adjust as needed

### For Production

- Consider Aurora Serverless for variable workloads
- Implement read replicas for read-heavy operations
- Use Reserved Instances for predictable workloads

## Next Steps

After database setup:

1. **Test Connectivity**: Verify database access from application subnets
2. **Load Test Data**: Insert sample records to validate schema
3. **Configure Monitoring**: Set up CloudWatch alarms
4. **Document Passwords**: Store credentials in AWS Secrets Manager
5. **Security Review**: Verify all security configurations