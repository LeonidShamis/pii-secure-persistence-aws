# Personally Identifiable Information (PII) tiered data protection using AWS services

> **⚠️ WORK IN PROGRESS (WIP)** - This project is currently under active development. The implementation is not complete and should not be used in production environments.

A defensive security system prototype demonstrating secure storage and handling of Personally Identifiable Information (PII) using a tiered encryption approach on AWS infrastructure.

## 🚧 Current Status

**Phase 2 of 7 phases completed**
- ✅ **Phase 1**: Database Foundation (Complete)
- ✅ **Phase 2**: AWS Security Infrastructure (Complete)
- 🔄 **Phase 3**: Lambda Encryption Service (Next)

See [Implementation Plan](docs/implementation-plan.md) for detailed progress.

## Overview

This project implements a three-tier PII classification and encryption system designed to protect sensitive personal data while maintaining compliance with regulations like GDPR, CCPA, and PCI DSS.

### Three-Tier PII Classification

- **Level 1 (Low Sensitivity)**: Names, emails, phone numbers
  - Encryption: RDS at-rest encryption only
  - Storage: Clear text in database
  - Examples: `first_name`, `last_name`, `email`

- **Level 2 (Medium Sensitivity)**: Addresses, dates of birth, IP addresses  
  - Encryption: Field-level encryption using AWS KMS CMK
  - Storage: Encrypted blobs in database
  - Examples: `address`, `date_of_birth`, `ip_address`

- **Level 3 (High Sensitivity)**: SSN, bank accounts, credit cards
  - Encryption: Double encryption (Application-layer + AWS KMS CMK)
  - Storage: Double-encrypted blobs in database
  - Examples: `ssn`, `bank_account`, `credit_card`

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   React SPA     │  HTTPS  │   API Gateway   │  Invoke │  Lambda Function│
│   (Frontend)    ├────────►│  (REST API)     ├────────►│  (Encryption)   │
└─────────────────┘         └─────────────────┘         └────────┬────────┘
                                     │                            │
                                     │                   ┌────────┴────────┐
                            ┌────────▼────────┐          │                 │
                            │   FastAPI       │    ┌─────▼─────┐   ┌──────▼──────┐
                            │   (Backend)     │    │  AWS KMS  │   │  Secrets    │
                            └────────┬────────┘    │           │   │  Manager    │
                                     │             └───────────┘   └─────────────┘
                            ┌────────▼────────┐
                            │  RDS Aurora     │
                            │  PostgreSQL     │
                            │  (Encrypted)    │
                            └─────────────────┘
```

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
- AWS RDS Aurora PostgreSQL 16+ with encryption at rest
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

## Project Structure

```
├── docs/                          # Project documentation
│   ├── prd.md                    # Product Requirements Document
│   ├── architecture.md           # Detailed architecture guide
│   └── implementation-plan.md    # Implementation progress tracking
├── database/                     # Database schema and setup
│   ├── schema.sql               # Complete PostgreSQL schema
│   └── setup.md                 # Database setup instructions
├── infrastructure/               # AWS infrastructure setup
│   ├── generate-keys.py         # Key generation utilities
│   ├── aws-console-setup-guide.md  # Manual AWS setup guide
│   └── README.md                # Infrastructure documentation
├── lambda/                       # (Coming in Phase 3)
├── backend/                      # (Coming in Phase 4)
└── frontend/                     # (Coming in Phase 5)
```

## Quick Start

### Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured
- Python 3.9+ with `uv` package manager
- PostgreSQL client for database operations

### 1. Generate Encryption Keys

```bash
cd infrastructure
uv run generate-keys.py
```

### 2. Set Up AWS Infrastructure

Follow the step-by-step AWS Console setup guide:

```bash
cat infrastructure/aws-console-setup-guide.md
```

This creates:
- KMS keys for Level 2 and Level 3 encryption
- Secrets Manager for application keys
- IAM roles with proper permissions

### 3. Deploy Database Schema

```bash
cat database/setup.md
```

## Development Status

### Completed ✅
- Complete database schema with three-tier encryption support
- Comprehensive AWS infrastructure setup guide
- Key generation utilities
- Project documentation and architecture

### In Progress 🔄
- Lambda encryption service implementation

### Planned 📋
- FastAPI backend implementation
- React frontend with visual PII indicators
- Integration testing
- Security validation

## Security Considerations

This is a **defensive security system** designed to:
- Protect sensitive personal information
- Demonstrate security best practices
- Support compliance requirements
- Provide audit capabilities

**Important**: This prototype is for educational and demonstration purposes. Production deployments require additional security hardening.

## Compliance Support

The system is designed to support:
- **GDPR**: Right to deletion, data minimization, encryption requirements
- **CCPA**: Data protection and access controls  
- **PCI DSS**: Encryption of cardholder data (for credit card fields)

## Cost Estimates

Estimated monthly AWS costs for prototype:
- KMS Keys: $2
- KMS API calls: ~$1
- Secrets Manager: $0.80
- Lambda: ~$1
- RDS Aurora: ~$60
- **Total: ~$65/month**

## Contributing

This is a work-in-progress prototype. See [Implementation Plan](docs/implementation-plan.md) for current development priorities.

## Documentation

- [Product Requirements Document](docs/prd.md) - Complete project requirements
- [Architecture Guide](docs/architecture.md) - Detailed technical architecture
- [Implementation Plan](docs/implementation-plan.md) - Development progress tracking
- [Infrastructure Setup](infrastructure/README.md) - AWS infrastructure configuration

## License

This project is for educational and demonstration purposes.