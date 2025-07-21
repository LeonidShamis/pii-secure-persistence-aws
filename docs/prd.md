# Product Requirements Document (PRD)
## PII Encryption System Prototype

**Version:** 1.0  
**Date:** July 2025  
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Purpose
This document defines the requirements for a prototype system that demonstrates secure storage and handling of Personally Identifiable Information (PII) using a tiered encryption approach on AWS infrastructure.

### 1.2 Scope
The prototype will showcase:
- Three-tier PII classification and encryption
- Integration with AWS services (RDS Aurora, KMS, Lambda, Secrets Manager)
- End-to-end data flow from user input to encrypted storage
- Secure retrieval and decryption of stored data
- Basic key rotation capabilities

### 1.3 Success Criteria
- Functional demonstration of different encryption levels for different PII types
- Successful encryption/decryption of data through the entire stack
- Clear visual representation of security measures
- Foundation for production-ready implementation

---

## 2. Business Requirements

### 2.1 Background
Organizations need to store sensitive personal information while:
- Complying with data protection regulations (GDPR, CCPA)
- Enabling secure data sharing with third-party services
- Maintaining query capabilities for non-sensitive fields
- Providing audit trails for data access

### 2.2 Objectives
1. **Demonstrate Security Best Practices**: Show proper handling of sensitive data
2. **Validate Architecture**: Prove the tiered encryption approach works
3. **Create Reusable Foundation**: Build components that can evolve to production
4. **Education**: Provide clear example of AWS security services integration

---

## 3. Functional Requirements

### 3.1 PII Classification System

#### 3.1.1 Level 1 - Low Sensitivity
- **Data Types**: Names, emails, phone numbers
- **Encryption**: RDS at-rest encryption only
- **Storage**: Clear text in database
- **Queryable**: Yes
- **Examples**: `first_name`, `last_name`, `email`, `phone`

#### 3.1.2 Level 2 - Medium Sensitivity
- **Data Types**: Addresses, dates of birth, IP addresses
- **Encryption**: Field-level encryption using AWS KMS CMK
- **Storage**: Encrypted blobs in database
- **Queryable**: No (optional: searchable hashes)
- **Examples**: `address`, `date_of_birth`, `ip_address`

#### 3.1.3 Level 3 - High Sensitivity
- **Data Types**: SSN, bank accounts, credit cards, health records
- **Encryption**: Double encryption (Application-layer + AWS KMS CMK)
- **Storage**: Double-encrypted blobs in database
- **Queryable**: No
- **Examples**: `ssn`, `bank_account`, `credit_card`, `medical_record`

### 3.2 User Interface Requirements

#### 3.2.1 Data Entry Form
- Single-page form with fields for all PII levels
- Visual indicators showing PII level for each field
- Real-time validation
- Clear labeling of security measures

#### 3.2.2 Data Display
- Retrieve and display decrypted data
- Show encryption status for each field
- Mask sensitive data (Level 3) by default
- Option to reveal masked data

#### 3.2.3 Visual Security Indicators
- Color coding: Green (L1), Orange (L2), Red (L3)
- Lock icons for encrypted fields
- Badges showing PII level

### 3.3 API Requirements

#### 3.3.1 Create User Endpoint
- **Method**: POST `/api/users`
- **Input**: JSON with user data
- **Process**: Classify and encrypt fields based on PII level
- **Output**: User ID and success status

#### 3.3.2 Retrieve User Endpoint
- **Method**: GET `/api/users/{user_id}`
- **Process**: Fetch and decrypt user data
- **Output**: JSON with decrypted user data

#### 3.3.3 Health Check Endpoint
- **Method**: GET `/api/health`
- **Output**: Status of all system components

### 3.4 Encryption Requirements

#### 3.4.1 Key Management
- AWS KMS Customer Managed Keys (CMK) for field encryption
- AWS Secrets Manager for application-layer keys
- Automatic key rotation enabled for KMS keys
- Version tracking for application keys

#### 3.4.2 Encryption Operations
- Transparent encryption/decryption via Lambda functions
- No encryption keys in application code
- Audit logging for all encryption operations
- Support for key version tracking

### 3.5 Data Storage Requirements

#### 3.5.1 Database Schema
- User table with mixed field types (clear and encrypted)
- Metadata table for encryption details
- Audit table for access logging
- Indexes for performance

#### 3.5.2 Field Storage
- Level 1: Standard columns with clear text
- Level 2: TEXT columns with encrypted data
- Level 3: TEXT columns with double-encrypted base64 data

---

## 4. Non-Functional Requirements

### 4.1 Security
- All data in transit must use TLS
- Database must be in private subnet
- IAM roles with least privilege principle
- No hardcoded credentials or keys
- Encryption keys never exposed to frontend

### 4.2 Performance
- Sub-second response time for single record operations
- Support for future batch operations
- Efficient key caching in Lambda

### 4.3 Scalability
- Architecture must support horizontal scaling
- Lambda functions for elastic compute
- RDS Aurora for database scaling

### 4.4 Maintainability
- Clear separation of concerns
- Modular design for easy updates
- Comprehensive logging
- Infrastructure as Code ready

### 4.5 Compliance Readiness
- Audit trail for all data access
- Support for crypto-shredding
- Key rotation capabilities
- Data residency controls

---

## 5. Technical Requirements

### 5.1 Frontend
- React-based single-page application
- No local storage of sensitive data
- HTTPS only
- Modern browser support

### 5.2 Backend API
- Python FastAPI framework
- Async/await support
- JSON request/response
- Boto3 for AWS integration

### 5.3 Encryption Service
- AWS Lambda functions (Python 3.9+)
- Cryptography library for app-layer encryption
- AWS SDK for KMS operations
- Secrets Manager integration

### 5.4 Database
- AWS RDS Aurora PostgreSQL
- Encryption at rest enabled
- Automated backups
- Private subnet deployment

### 5.5 AWS Services
- **KMS**: 2 CMKs minimum (Level 2 and Level 3)
- **Secrets Manager**: Application keys and DB credentials
- **Lambda**: Encryption/decryption functions
- **API Gateway**: REST API exposure
- **IAM**: Role-based access control

---

## 6. Constraints

### 6.1 Prototype Limitations
- Single-region deployment
- Basic error handling
- Limited to single-record operations
- No production-grade monitoring
- Simplified authentication

### 6.2 Technology Constraints
- AWS services only
- PostgreSQL for database
- Python for backend services
- React for frontend

---

## 7. Assumptions

1. AWS account with appropriate permissions available
2. Development environment with AWS CLI configured
3. Basic understanding of AWS services
4. No requirement for backwards compatibility
5. English-only interface
6. Single tenant system

---

## 8. Dependencies

### 8.1 External Dependencies
- AWS service availability
- Internet connectivity for users
- Modern web browser

### 8.2 Internal Dependencies
- Proper IAM role configuration
- VPC and networking setup
- SSL certificates for HTTPS (unless handled by other service, e.g. Cloudflare)

---

## 9. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| AWS service limits | High | Low | Request limit increases early |
| Key rotation complexity | Medium | Medium | Implement version tracking |
| Lambda cold starts | Low | High | Accept for prototype |
| Cost overruns | Medium | Low | Use AWS Free Tier where possible |

---

## 10. Success Metrics

### 10.1 Functional Metrics
- All three encryption levels working correctly
- Successful round-trip encryption/decryption
- No exposed sensitive data
- All API endpoints functional

### 10.2 Technical Metrics
- < 1 second response time
- Zero hardcoded credentials
- 100% of sensitive fields encrypted
- Successful key rotation demonstration

---

## 11. Future Considerations

### 11.1 Production Enhancements
- Multi-AZ / Multi-region deployment
- Advanced monitoring and alerting
- Batch processing capabilities
- API rate limiting
- Advanced authentication (Cognito)

### 11.2 Additional Features
- Search capabilities for encrypted fields
- Data export with encryption
- Compliance reporting
- Third-party service integration
- Field-level access controls

---

## 12. Acceptance Criteria

1. **Data Entry**: User can input all PII types through web form
2. **Encryption**: System correctly classifies and encrypts based on PII level
3. **Storage**: Encrypted data stored in RDS Aurora
4. **Retrieval**: System can fetch and decrypt data on demand
5. **Security**: No plaintext sensitive data in logs or frontend
6. **Key Management**: Demonstrate key rotation without data loss
7. **Audit**: Basic audit trail for data access

---

## Appendix A: Sample Data Fields

| Field Name | PII Level | Encryption Method | Example Value |
|------------|-----------|-------------------|---------------|
| email | 1 | RDS at-rest only | john@example.com |
| first_name | 1 | RDS at-rest only | John |
| last_name | 1 | RDS at-rest only | Doe |
| phone | 1 | RDS at-rest only | +1-555-0123 |
| address | 2 | KMS field-level | 123 Main St, City |
| date_of_birth | 2 | KMS field-level | 1990-01-01 |
| ip_address | 2 | KMS field-level | 192.168.1.1 |
| ssn | 3 | Double encryption | 123-45-6789 |
| bank_account | 3 | Double encryption | 1234567890 |
| credit_card | 3 | Double encryption | 4111-1111-1111-1111 |

---

## Appendix B: Compliance Mapping

| Requirement | GDPR | CCPA | PCI DSS |
|-------------|------|------|---------|
| Encryption at rest | ✓ | ✓ | ✓ |
| Encryption in transit | ✓ | ✓ | ✓ |
| Access controls | ✓ | ✓ | ✓ |
| Audit logging | ✓ | ✓ | ✓ |
| Data minimization | ✓ | ✓ | N/A |
| Right to deletion | ✓ | ✓ | N/A |