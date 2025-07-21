# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **PII Encryption System Prototype** that demonstrates secure storage and handling of Personally Identifiable Information (PII) using a tiered encryption approach on AWS infrastructure. This is a defensive security system designed to protect sensitive data.

## Architecture

### Three-Tier PII Classification System

- **Level 1 (Low Sensitivity)**: Names, emails, phone numbers - RDS at-rest encryption only
- **Level 2 (Medium Sensitivity)**: Addresses, dates of birth, IP addresses - Field-level encryption using AWS KMS CMK
- **Level 3 (High Sensitivity)**: SSN, bank accounts, credit cards - Double encryption (Application-layer + AWS KMS CMK)

### Technology Stack

**Frontend:**
- React 18+ single-page application
- No client-side encryption (security isolation)
- Visual PII level indicators

**Backend API:**
- Python FastAPI framework with async/await
- Boto3 for AWS integration
- Delegates encryption to Lambda functions

**Encryption Service:**
- AWS Lambda functions (Python 3.9+)
- Cryptography library for app-layer encryption
- AWS SDK for KMS operations

**Database:**
- AWS RDS Aurora PostgreSQL with encryption at rest
- Mixed schema: plaintext + encrypted fields
- Audit logging for all operations

**AWS Services:**
- KMS: Customer Managed Keys with auto-rotation
- Secrets Manager: Application keys and credentials
- API Gateway: REST API exposure

## Key Security Principles

1. **Encryption keys never exposed to frontend**
2. **No hardcoded credentials anywhere**
3. **Database deployed in private subnet**
4. **IAM roles with least privilege principle**
5. **Comprehensive audit logging**
6. **Lambda provides security isolation boundary**

## Development Commands

Since this is currently a documentation-only repository (no implementation files yet), the following commands would be used once the implementation begins:

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start  # Typically runs on port 3000
```

### Lambda Development
```bash
cd lambda
pip install -r requirements.txt -t .
zip -r ../lambda_function.zip .
```

### Infrastructure Deployment
```bash
terraform init
terraform plan
terraform apply
```

### Testing
```bash
# Backend tests
pytest backend/tests/

# Integration tests
pytest tests/integration/

# Security tests
pytest tests/security/
```

## Architecture Patterns

### Encryption Flow
```
User Input → FastAPI → Lambda → KMS/Secrets Manager → RDS Aurora
```

### Data Classification Decision Matrix
- Check field name against classification mapping in Lambda
- Apply appropriate encryption level automatically
- Store metadata for decryption operations

### Key Management Hierarchy
- AWS Account Root Key
  - KMS CMK: alias/pii-level2 (Level 2 field encryption)
  - KMS CMK: alias/pii-level3 (Level 3 KMS layer)
  - Secrets Manager: pii-encryption-keys (Level 3 app layer)

## Important Implementation Notes

### Security Boundaries
- **Frontend**: No encryption logic, HTTPS only, no sensitive data caching
- **FastAPI**: Business logic only, delegates all encryption to Lambda
- **Lambda**: Isolated encryption operations, secrets caching, audit logging
- **Database**: Mixed plaintext/encrypted storage with comprehensive metadata

### Database Schema Pattern
- Level 1 fields: Standard columns (email, first_name, last_name)
- Level 2 fields: TEXT columns with _encrypted suffix (address_encrypted)
- Level 3 fields: TEXT columns with _encrypted suffix (ssn_encrypted)
- Separate encryption_metadata table for key versions and algorithms
- Audit table for compliance and monitoring

### Error Handling
- Lambda functions include comprehensive error handling
- No sensitive information in error messages
- Audit logging for both successful and failed operations
- Graceful degradation when encryption services unavailable

## Compliance Considerations

This system is designed to support:
- **GDPR**: Right to deletion, data minimization, encryption requirements
- **CCPA**: Data protection and access controls
- **PCI DSS**: Encryption of cardholder data (for credit card fields)

The audit trail supports compliance reporting and crypto-shredding capabilities.

## Local Development Setup

When implementing this system:

1. Set up local PostgreSQL with the provided schema
2. Configure AWS CLI with appropriate permissions
3. Set environment variables for local development
4. Use LocalStack for local AWS service emulation during development
5. Implement proper secret management even in development

## Cost Optimization

Estimated monthly costs for prototype:
- KMS Keys: $2
- KMS API calls: ~$1
- Secrets Manager: $0.80
- Lambda: ~$1
- RDS Aurora: ~$60
- **Total: ~$65/month**

Use Aurora Serverless and appropriate Lambda memory sizing for cost optimization.