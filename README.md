# Personally Identifiable Information (PII) tiered data protection using AWS services

> **✅ PROTOTYPE COMPLETE** - This project has successfully completed all planned phases and demonstrates a working three-tier PII encryption system. Ready for production implementation planning.

A defensive security system prototype demonstrating secure storage and handling of Personally Identifiable Information (PII) using a tiered encryption approach on AWS infrastructure.

## ✅ Project Status - COMPLETED PROTOTYPE

**All 7 phases completed (100% progress) - PROTOTYPE COMPLETE ✅**
- ✅ **Phase 1**: Database Foundation (Complete)
- ✅ **Phase 2**: AWS Security Infrastructure (Complete)
- ✅ **Phase 3**: Lambda Encryption Service (Complete)
- ✅ **Phase 4**: FastAPI Backend with App Runner (Complete)
- ✅ **Phase 5**: API Gateway (Complete - replaced by App Runner)
- ✅ **Phase 6**: React Frontend (Complete)
- ✅ **Phase 7**: Integration Testing & Validation (Complete)

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
┌─────────────────┐    HTTPS    ┌─────────────────┐    Invoke    ┌─────────────────┐
│   React SPA     │◄──────────►│  AWS App Runner │◄────────────►│ Lambda Function │
│   (Frontend)    │             │   (FastAPI)     │              │  (Encryption)   │
└─────────────────┘             └─────────────────┘              └────────┬────────┘
        │                                │                                 │
        │ Visual Security                │ Business Logic                  │ Security Boundary
        │ • Color coding                 │ • API endpoints                 │ • PII classification
        │ • Data masking                 │ • Request validation            │ • Multi-tier encryption
        │ • Progressive disclosure       │ • CORS & authentication        │ • Key management
        │                                │                                 │
        │                       ┌────────▼────────┐                ┌──────▼──────┐
        │                       │  RDS Aurora     │                │   AWS KMS   │
        │                       │  PostgreSQL     │                │ Secrets Mgr │
        │                       │  (Encrypted)    │                │             │
        └───────────────────────└─────────────────┘                └─────────────┘
              Audit Trail &              Data Storage                Key Management
            Compliance Logging
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
- App Runner: Production container hosting with auto-scaling

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
├── lambda/                       # Lambda encryption service
│   ├── src/pii_encryption_lambda/  # Complete 3-tier encryption
│   ├── pyproject.toml           # Python dependencies (uv)
│   ├── deploy.py                # AWS deployment script
│   └── README.md                # Lambda documentation
├── backend/                      # FastAPI REST API
│   ├── src/pii_backend/         # FastAPI application
│   ├── deploy/                  # AWS App Runner deployment
│   ├── Dockerfile               # Production container
│   ├── pyproject.toml           # Python dependencies (uv)
│   └── README.md                # Backend documentation
├── frontend/                     # React SPA with PII indicators
│   ├── src/components/          # UserForm, UserDisplay, UserList, PIIField
│   ├── src/services/           # API integration service
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.js          # Vite build configuration
│   └── README.md               # Frontend documentation
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
- **Database Foundation**: Complete PostgreSQL schema with three-tier encryption support
- **AWS Security Infrastructure**: KMS keys, Secrets Manager, IAM roles with least privilege
- **Lambda Encryption Service**: Complete 3-tier encryption with audit logging and key rotation
- **FastAPI Backend**: REST API with 9 endpoints, async Lambda integration, production deployment
- **AWS App Runner Deployment**: Production-ready container hosting with auto-scaling
- **Security & Authentication**: API key auth, CORS, comprehensive error handling
- **Infrastructure as Code**: Terraform deployment automation and Docker containerization
- **React Frontend**: Complete SPA with visual PII indicators, user listing, data masking, and test data generation

### Documentation Complete ✅
- Manual Testing Validation Report with complete requirements coverage
- Security & Compliance Summary documenting enterprise-grade security architecture
- Production Testing Strategy for real deployment scenarios
- Final Project Summary with comprehensive overview and recommendations

### Ready for Production 🚀
- Complete architecture and implementation guidance
- Comprehensive testing strategies and quality assurance frameworks
- Security best practices and compliance-ready features
- Proven patterns for enterprise deployment

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
- App Runner: $5-15 (scales to zero)
- RDS Aurora: ~$60
- **Total: ~$70-80/month**

## Contributing

This prototype has been completed successfully. See [Implementation Plan](docs/implementation-plan.md) for development history and [Project Completion Summary](docs/project-completion-summary.md) for comprehensive overview.

## Documentation

### Core Documentation
- [Product Requirements Document](docs/prd.md) - Complete project requirements
- [Architecture Guide](docs/architecture.md) - Detailed technical architecture
- [Implementation Plan](docs/implementation-plan.md) - Development progress tracking
- [Infrastructure Setup](infrastructure/README.md) - AWS infrastructure configuration

### Phase 7 Completion Documentation
- [Manual Testing Validation Report](docs/testing-validation-report.md) - Complete requirements validation
- [Security & Compliance Summary](docs/security-compliance-summary.md) - Enterprise security architecture
- [Production Testing Strategy](docs/production-testing-strategy.md) - Production deployment testing framework
- [Project Completion Summary](docs/project-completion-summary.md) - Final project overview and recommendations

## License

This project is for educational and demonstration purposes.