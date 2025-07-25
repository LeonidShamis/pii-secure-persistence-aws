# PII Encryption Lambda Function

This directory contains the AWS Lambda function that provides the core encryption services for the PII secure persistence system.

## Overview

The Lambda function implements a three-tier PII encryption system:

- **Level 1 (Low Sensitivity)**: Names, emails, phone numbers - RDS at-rest encryption only
- **Level 2 (Medium Sensitivity)**: Addresses, dates of birth, IP addresses - Field-level encryption using AWS KMS CMK
- **Level 3 (High Sensitivity)**: SSN, bank accounts, credit cards - Double encryption (Application-layer + AWS KMS CMK)

## Project Structure

```
lambda/
   src/pii_encryption_lambda/
      __init__.py              # Package initialization
      lambda_function.py       # Main Lambda handler and encryption logic
      database_operations.py   # Database CRUD operations
   deploy.py                    # Deployment script
   test_lambda.py              # Unit and integration tests
   pyproject.toml              # Python dependencies (uv format)
   README.md                   # This file
```

## Features

### Encryption Operations
- **Automatic PII Classification**: Fields are automatically classified into security levels
- **Three-Tier Encryption**: Different encryption methods based on sensitivity
- **Key Management**: Integration with AWS KMS and Secrets Manager
- **Audit Logging**: Comprehensive audit trail for all operations

### Database Operations
- **Create User**: Encrypt and store user data
- **Retrieve User**: Fetch and decrypt user data
- **List Users**: List users with basic information (no sensitive data)
- **Delete User**: Crypto-shredding with complete data deletion
- **Audit Trail**: Retrieve encryption/decryption audit logs

### Health Monitoring
- **System Health**: Check status of all components (KMS, Secrets Manager, Database)
- **Schema Validation**: Verify database schema integrity

## API Operations

The Lambda function supports the following operations:

### 1. Create User
```json
{
  "operation": "create_user",
  "data": {
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "address": "123 Main St",
    "date_of_birth": "1990-01-01",
    "ssn": "123-45-6789",
    "bank_account": "1234567890"
  }
}
```

### 2. Get User
```json
{
  "operation": "get_user",
  "user_id": "user-uuid"
}
```

### 3. List Users
```json
{
  "operation": "list_users",
  "limit": 100,
  "offset": 0
}
```

### 4. Delete User
```json
{
  "operation": "delete_user",
  "user_id": "user-uuid"
}
```

### 5. Health Check
```json
{
  "operation": "health"
}
```

### 6. Audit Trail
```json
{
  "operation": "audit_trail",
  "user_id": "user-uuid",
  "limit": 100
}
```

## Development Setup

### 1. Install Dependencies
```bash
cd lambda
uv sync
```

### 2. Database Schema Introspection (if schema changes)
```bash
# Introspect current database schema and regenerate Lambda code
python introspect_schema.py
```

### 3. Create Deployment Package
```bash
# Create deployment package with current working Lambda function
python create_final_package.py
```

This generates: `pii-encryption-lambda-FINAL-FIXED.zip`

### 4. Debug Database Issues
```bash
# Check what's actually stored in database
python debug_user_data.py
```

## Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- Lambda function created in AWS (see infrastructure setup)
- KMS keys and Secrets Manager secrets configured
- RDS database with proper schema

### Deploy to AWS
1. **Build Package**: Run `python create_final_package.py`
2. **Upload to Lambda**: Upload `pii-encryption-lambda-FINAL-FIXED.zip` via AWS Console or CLI
3. **Test**: Use test events in `test_events/` folder

### Manual AWS CLI Deployment
```bash
# Update function code
aws lambda update-function-code \
  --function-name pii-encryption-handler \
  --zip-file fileb://pii-encryption-lambda-FINAL-FIXED.zip
```

## Performance Considerations

### Optimization Features
- Connection pooling for database connections
- Secrets caching to reduce API calls
- LRU caching for application keys
- Efficient encryption/decryption algorithms

### Memory Usage
- Default: 256MB (adjustable based on workload)
- Monitor CloudWatch metrics for optimization

## Testing

### Unit Tests
```bash
python test_lambda.py
```

### Integration Tests
Integration tests require:
- AWS credentials configured
- Test AWS environment with all resources
- Test database with proper schema

### Manual Testing
Generate test events and use AWS Lambda console or CLI:
```bash
python test_lambda.py --generate-events
aws lambda invoke --function-name pii-encryption-handler --payload file://test_events/health_check.json response.json
```