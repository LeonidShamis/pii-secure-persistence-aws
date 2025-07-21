# PII Database Tools

Database utilities and testing tools for the PII encryption system.

## Setup

This directory is set up as a self-contained `uv` project with its own virtual environment and dependencies.

### Prerequisites

- Python 3.10+
- `uv` package manager
- PostgreSQL database (local or AWS Aurora)

### Installation

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to database directory
cd database/

# Install dependencies (automatically creates virtual environment)
uv sync
```

## Configuration

### Environment Variables

Copy the `.env.example` to `.env` and update with your database credentials:

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

### Environment Variables Reference

```bash
# Database Connection
DB_HOST=localhost                    # Database host
DB_PORT=5432                        # Database port
DB_NAME=pii_db                      # Database name
DB_USER=postgres                    # Database user
DB_PASSWORD=your_secure_password    # Database password
DB_SSLMODE=prefer                   # SSL mode (require for Aurora)

# Connection Pool Settings
DB_POOL_MIN_SIZE=1                  # Minimum pool connections
DB_POOL_MAX_SIZE=10                 # Maximum pool connections

# Test Configuration
TEST_CLEANUP=true                   # Clean up test data
TEST_VERBOSE=true                   # Verbose test output
ENVIRONMENT=development             # Environment name
```

## Files

- `schema.sql` - Complete database schema for PII encryption system
- `test_schema.sql` - SQL-based schema validation tests
- `test_connection.py` - Python database connectivity and functionality tests
- `run_tests.py` - Test runner script
- `.env` - Environment variables template
- `setup.md` - Detailed database setup guide

## Usage

### 1. Deploy Database Schema

```bash
# For local PostgreSQL
psql -U postgres -d pii_db -f schema.sql

# For AWS Aurora (via bastion/VPN)
psql -h your-aurora-endpoint -U postgres -d pii_db -f schema.sql
```

### 2. Run Database Tests

```bash
# Using uv (recommended)
uv run python test_connection.py

# Or using the runner script
uv run python run_tests.py

# Or using project scripts
uv run test-db
```

### 3. Run SQL Schema Tests

```bash
# Direct SQL tests
psql -U postgres -d pii_db -f test_schema.sql
```

## Test Coverage

The test suite validates:

### Schema Validation
- ✅ All required tables exist
- ✅ Indexes are properly created
- ✅ Triggers are functional
- ✅ Views are accessible

### Functional Tests
- ✅ Data insertion and retrieval
- ✅ Audit logging triggers
- ✅ Encryption metadata tracking
- ✅ System configuration management

### Constraint Tests
- ✅ PII level constraints (1, 2, 3)
- ✅ Operation type constraints
- ✅ Unique constraints
- ✅ Foreign key relationships

### Performance Tests
- ✅ Index usage validation
- ✅ Query execution plans
- ✅ Connection pooling

## Database Schema Overview

### Core Tables

1. **`users`** - Main user data with three PII encryption levels
2. **`encryption_metadata`** - Key version tracking and encryption details
3. **`encryption_audit`** - Comprehensive audit trail for compliance
4. **`key_rotation_log`** - Key rotation history and impact tracking
5. **`system_config`** - System-wide configuration settings

### PII Encryption Levels

- **Level 1 (Low)**: Clear text, RDS encryption only
  - Fields: `email`, `first_name`, `last_name`, `phone`
- **Level 2 (Medium)**: KMS field-level encryption
  - Fields: `address_encrypted`, `date_of_birth_encrypted`, `ip_address_encrypted`
- **Level 3 (High)**: Double encryption (Application + KMS)
  - Fields: `ssn_encrypted`, `bank_account_encrypted`, `credit_card_encrypted`

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   ```bash
   # Check if database is running
   pg_isready -h localhost -p 5432
   
   # Test connectivity
   psql -h localhost -U postgres -l
   ```

2. **Missing Extensions**
   ```sql
   -- Enable required extensions
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pgcrypto";
   ```

3. **Permission Denied**
   ```bash
   # Check database permissions
   psql -U postgres -c "\du"
   ```

### Environment Issues

```bash
# Check if .env is loaded
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'DB_HOST: {os.getenv(\"DB_HOST\")}')"

# Verify uv environment
uv run python --version
uv run pip list
```

## AWS Aurora Setup

For AWS Aurora PostgreSQL:

1. **Configure Security Groups**: Allow access from your IP/Lambda subnets
2. **Update .env**: Use Aurora endpoint and credentials
3. **Enable SSL**: Set `DB_SSLMODE=require`
4. **VPC Access**: Ensure network connectivity (VPN/bastion host)

See `setup.md` for detailed Aurora configuration steps.

## Development

### Adding New Tests

Add new test functions to `test_connection.py`:

```python
def test_new_functionality():
    """Test new database functionality"""
    # Your test implementation
    pass
```

### Database Migrations

For schema changes:

1. Update `schema.sql`
2. Add migration SQL to `migrations/` directory
3. Update tests in `test_schema.sql`
4. Test thoroughly before deployment

## Security Notes

- Never commit real credentials to version control
- Use separate `.env` files for different environments
- Regularly rotate database passwords
- Monitor connection logs for suspicious activity
- Use SSL/TLS for all database connections in production