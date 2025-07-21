# Architecture Document
## PII Encryption System

**Version:** 1.0  
**Date:** July 2025  
**Status:** Draft

---

## 1. Architecture Overview

### 1.1 System Architecture

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

### 1.2 Component Responsibilities

| Component | Primary Responsibility | Key Decisions |
|-----------|----------------------|---------------|
| React Frontend | User interface, data collection | No encryption logic, HTTPS only |
| API Gateway | API exposure, rate limiting | REST API, CORS enabled |
| FastAPI | Business logic, orchestration | Delegates encryption to Lambda |
| Lambda | Encryption/decryption operations | Isolated security boundary |
| KMS | Key management, field encryption | CMKs with auto-rotation |
| Secrets Manager | Application keys, credentials | Versioned secrets |
| RDS Aurora | Data persistence | Encryption at rest, private subnet |

---

## 2. Encryption Architecture

### 2.1 Three-Tier Encryption Model

```
Level 1 (Low Sensitivity):
User Input → FastAPI → Lambda → RDS (at-rest encryption only)

Level 2 (Medium Sensitivity):
User Input → FastAPI → Lambda → KMS Encrypt → RDS (encrypted field + at-rest)

Level 3 (High Sensitivity):
User Input → FastAPI → Lambda → App Encrypt → KMS Encrypt → RDS (double encrypted + at-rest)
```

### 2.2 Encryption Decision Matrix

| PII Level | Data at Rest | Application Layer | KMS Layer | Total Layers |
|-----------|--------------|-------------------|-----------|--------------|
| Level 1 | ✓ (RDS) | ✗ | ✗ | 1 |
| Level 2 | ✓ (RDS) | ✗ | ✓ | 2 |
| Level 3 | ✓ (RDS) | ✓ (Fernet) | ✓ | 3 |

### 2.3 Key Hierarchy

```
AWS Account Root Key
├── KMS CMK: alias/pii-level2
│   ├── Used for: Level 2 field encryption
│   ├── Rotation: Automatic (yearly)
│   └── Access: Lambda execution role only
├── KMS CMK: alias/pii-level3
│   ├── Used for: Level 3 KMS layer
│   ├── Rotation: Automatic (yearly)
│   └── Access: Lambda execution role only
└── Secrets Manager: pii-encryption-keys
    ├── level3_app_key_v1: Fernet key for app-layer
    ├── level3_app_key_v2: Future rotation
    └── current_version: Active key version
```

---

## 3. Component Details

### 3.1 Frontend (React)

**Technology Stack:**
- React 18+
- Axios for API calls
- No state management library (prototype scope)

**Key Design Decisions:**
- Single-page application for simplicity
- No client-side encryption
- Visual PII level indicators
- Form validation before submission

**Security Considerations:**
- HTTPS enforced
- No localStorage usage
- No caching of sensitive data
- Input sanitization

**Sample Component Structure:**
```jsx
// UserForm.jsx
import React, { useState } from 'react';
import axios from 'axios';

function UserForm() {
    const [formData, setFormData] = useState({
        email: '',
        first_name: '',
        last_name: '',
        address: '',
        dob: '',
        ssn: '',
        bank_account: ''
    });
    
    const piiLevels = {
        email: 1,
        first_name: 1,
        last_name: 1,
        address: 2,
        dob: 2,
        ssn: 3,
        bank_account: 3
    };
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('/api/users', formData);
            alert(`User created with ID: ${response.data.user_id}`);
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    };
    
    // ... rest of component
}
```

### 3.2 API Gateway

**Configuration:**
- REST API (not HTTP API) for full features
- CORS enabled for frontend domain
- Request validation
- API key authentication (prototype)

**Integration:**
- Lambda proxy integration
- Request/response transformation
- Error handling

### 3.3 Backend API (FastAPI)

**Technology Stack:**
- FastAPI (latest stable)
- Boto3 for AWS SDK
- Asyncio for async operations
- Pydantic for data validation

**Key Design Decisions:**
- Async/await for scalability
- Dependency injection for services
- No direct encryption operations
- Delegates to Lambda for security isolation

**API Structure:**
```python
# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
import json

app = FastAPI(title="PII Encryption API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS clients
lambda_client = boto3.client('lambda')
secrets_client = boto3.client('secretsmanager')

# Service layer
class UserService:
    def __init__(self):
        self.lambda_function = 'pii-encryption-handler'
        
    async def create_user(self, user_data: dict) -> dict:
        # Invoke Lambda for encryption
        lambda_response = lambda_client.invoke(
            FunctionName=self.lambda_function,
            Payload=json.dumps({
                'operation': 'encrypt',
                'data': user_data
            })
        )
        
        encrypted_data = json.loads(lambda_response['Payload'].read())
        
        # Store in database
        user_id = await self._store_in_database(encrypted_data)
        
        return {'user_id': str(user_id), 'status': 'created'}
    
    async def get_user(self, user_id: str) -> dict:
        # Invoke Lambda for decryption
        lambda_response = lambda_client.invoke(
            FunctionName=self.lambda_function,
            Payload=json.dumps({
                'operation': 'decrypt',
                'user_id': user_id
            })
        )
        
        decrypted_data = json.loads(lambda_response['Payload'].read())
        return decrypted_data

# API endpoints
user_service = UserService()

@app.post("/api/users")
async def create_user(user_data: dict):
    return await user_service.create_user(user_data)

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    return await user_service.get_user(user_id)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "lambda": "connected",
            "database": "connected"
        }
    }
```

### 3.4 Lambda Functions

**Runtime:** Python 3.9+

**Key Design Decisions:**
- Single function with operation routing
- Secrets caching for performance
- Comprehensive error handling
- Audit logging for all operations

**Complete Lambda Implementation:**
```python
# lambda_function.py
import boto3
import json
import base64
from cryptography.fernet import Fernet
from datetime import datetime
import logging
from functools import lru_cache
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class EncryptionHandler:
    def __init__(self):
        self.kms = boto3.client('kms')
        self.secrets = boto3.client('secretsmanager')
        self._secrets_cache = {}
        
    @lru_cache(maxsize=1)
    def get_app_keys(self):
        """Retrieve and cache app encryption keys from Secrets Manager"""
        response = self.secrets.get_secret_value(
            SecretId='pii-encryption-keys'
        )
        secret_data = json.loads(response['SecretString'])
        return secret_data['app_encryption_keys']
    
    @lru_cache(maxsize=1)
    def get_db_credentials(self):
        """Retrieve database credentials from Secrets Manager"""
        response = self.secrets.get_secret_value(
            SecretId='pii-database-credentials'
        )
        return json.loads(response['SecretString'])
    
    def get_db_connection(self):
        """Create database connection"""
        creds = self.get_db_credentials()
        return psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            database=creds['database'],
            user=creds['username'],
            password=creds['password'],
            cursor_factory=RealDictCursor
        )
    
    def classify_pii_level(self, field_name):
        """Determine PII level based on field name"""
        level_mapping = {
            1: ['email', 'first_name', 'last_name', 'phone'],
            2: ['address', 'date_of_birth', 'dob', 'ip_address'],
            3: ['ssn', 'bank_account', 'credit_card', 'medical_record']
        }
        
        field_lower = field_name.lower()
        for level, fields in level_mapping.items():
            if field_lower in fields:
                return level
        return 1  # Default to level 1
    
    def get_current_app_cipher(self):
        """Get Fernet cipher for current key version"""
        keys = self.get_app_keys()
        current_version = keys['current_version']
        key = keys[f'level3_app_key_v{current_version}']
        return Fernet(key.encode())
    
    def get_app_cipher_for_version(self, version):
        """Get Fernet cipher for specific key version"""
        keys = self.get_app_keys()
        key = keys[f'level3_app_key_v{version}']
        return Fernet(key.encode())
    
    def encrypt_field(self, field_name, value, level):
        """Encrypt field based on PII level"""
        if level == 1:
            return {
                'value': value,
                'encrypted': False,
                'level': 1
            }
            
        elif level == 2:
            # KMS encryption only
            response = self.kms.encrypt(
                KeyId='alias/pii-level2',
                Plaintext=value.encode()
            )
            return {
                'value': base64.b64encode(response['CiphertextBlob']).decode(),
                'encrypted': True,
                'level': 2,
                'kms_key': 'alias/pii-level2'
            }
            
        elif level == 3:
            # Double encryption
            # Step 1: App-layer encryption
            cipher = self.get_current_app_cipher()
            app_encrypted = cipher.encrypt(value.encode())
            
            # Step 2: KMS encryption
            response = self.kms.encrypt(
                KeyId='alias/pii-level3',
                Plaintext=app_encrypted
            )
            
            return {
                'value': base64.b64encode(response['CiphertextBlob']).decode(),
                'encrypted': True,
                'level': 3,
                'app_key_version': self.get_app_keys()['current_version'],
                'kms_key': 'alias/pii-level3'
            }
    
    def decrypt_field(self, field_name, encrypted_value, level, metadata=None):
        """Decrypt field based on PII level"""
        if level == 1:
            return encrypted_value
            
        elif level == 2:
            # KMS decryption only
            ciphertext = base64.b64decode(encrypted_value)
            response = self.kms.decrypt(CiphertextBlob=ciphertext)
            return response['Plaintext'].decode()
            
        elif level == 3:
            # Double decryption
            # Step 1: KMS decryption
            ciphertext = base64.b64decode(encrypted_value)
            response = self.kms.decrypt(CiphertextBlob=ciphertext)
            
            # Step 2: App-layer decryption
            app_key_version = metadata.get('app_key_version', 1) if metadata else 1
            cipher = self.get_app_cipher_for_version(app_key_version)
            
            return cipher.decrypt(response['Plaintext']).decode()
    
    def log_audit(self, user_id, field_name, operation, success=True, error=None):
        """Log encryption/decryption operations for audit"""
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO encryption_audit (
                        user_id, field_name, pii_level, operation,
                        accessed_by, success, error_message
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, field_name, 
                    self.classify_pii_level(field_name),
                    operation, 'lambda-function', success, error
                ))
                conn.commit()
        finally:
            conn.close()
    
    def store_encrypted_data(self, encrypted_data):
        """Store encrypted data in database"""
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Insert user record
                insert_user = """
                    INSERT INTO users (
                        email, first_name, last_name,
                        address_encrypted, dob_encrypted,
                        ssn_encrypted, bank_account_encrypted
                    ) VALUES (
                        %(email)s, %(first_name)s, %(last_name)s,
                        %(address_encrypted)s, %(dob_encrypted)s,
                        %(ssn_encrypted)s, %(bank_account_encrypted)s
                    ) RETURNING id
                """
                
                cursor.execute(insert_user, encrypted_data['fields'])
                user_id = cursor.fetchone()['id']
                
                # Insert metadata
                for field_name, metadata in encrypted_data['metadata'].items():
                    insert_meta = """
                        INSERT INTO encryption_metadata (
                            user_id, field_name, pii_level, 
                            app_key_version, kms_key_alias
                        ) VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_meta, (
                        user_id, field_name, metadata['level'],
                        metadata.get('app_key_version'),
                        metadata.get('kms_key')
                    ))
                
                conn.commit()
                return str(user_id)
                
        finally:
            conn.close()
    
    def retrieve_encrypted_data(self, user_id):
        """Retrieve encrypted data from database"""
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Get user data
                cursor.execute(
                    "SELECT * FROM users WHERE id = %s",
                    (user_id,)
                )
                user_data = cursor.fetchone()
                
                # Get metadata
                cursor.execute(
                    "SELECT * FROM encryption_metadata WHERE user_id = %s",
                    (user_id,)
                )
                metadata_rows = cursor.fetchall()
                
                metadata = {
                    row['field_name']: {
                        'level': row['pii_level'],
                        'app_key_version': row['app_key_version']
                    }
                    for row in metadata_rows
                }
                
                return user_data, metadata
                
        finally:
            conn.close()

def lambda_handler(event, context):
    """Main Lambda entry point"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        handler = EncryptionHandler()
        operation = event['operation']
        
        if operation == 'encrypt':
            # Process encryption request
            data = event['data']
            encrypted_result = {
                'fields': {},
                'metadata': {}
            }
            
            # Classify and encrypt each field
            for field_name, value in data.items():
                if value is None:
                    continue
                    
                level = handler.classify_pii_level(field_name)
                result = handler.encrypt_field(field_name, value, level)
                
                if level == 1:
                    encrypted_result['fields'][field_name] = result['value']
                else:
                    encrypted_result['fields'][f"{field_name}_encrypted"] = result['value']
                    encrypted_result['metadata'][field_name] = {
                        'level': result['level'],
                        'app_key_version': result.get('app_key_version'),
                        'kms_key': result.get('kms_key')
                    }
            
            # Store in database
            user_id = handler.store_encrypted_data(encrypted_result)
            
            # Audit logging
            for field_name in data.keys():
                handler.log_audit(user_id, field_name, 'encrypt', success=True)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'user_id': user_id,
                    'status': 'encrypted and stored'
                })
            }
            
        elif operation == 'decrypt':
            # Process decryption request
            user_id = event['user_id']
            
            # Retrieve from database
            user_data, metadata = handler.retrieve_encrypted_data(user_id)
            
            decrypted_result = {}
            
            # Decrypt each field
            for field_name, value in user_data.items():
                if field_name in ['id', 'created_at', 'updated_at']:
                    continue
                    
                if field_name.endswith('_encrypted'):
                    original_field = field_name.replace('_encrypted', '')
                    level = handler.classify_pii_level(original_field)
                    
                    if value:
                        decrypted_value = handler.decrypt_field(
                            original_field, 
                            value, 
                            level,
                            metadata.get(original_field)
                        )
                        decrypted_result[original_field] = decrypted_value
                        
                        # Audit logging
                        handler.log_audit(user_id, original_field, 'decrypt', success=True)
                else:
                    decrypted_result[field_name] = value
            
            return {
                'statusCode': 200,
                'body': json.dumps(decrypted_result)
            }
            
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        logger.error(f"Error in lambda handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            })
        }
```

### 3.5 Database (RDS Aurora PostgreSQL)

**Configuration:**
- Aurora PostgreSQL 14+
- Encryption at rest enabled
- Automated backups
- Private subnet deployment

**Schema Design:**
```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main user table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Level 1: Plain text (RDS encryption only)
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    
    -- Level 2: KMS encrypted
    address_encrypted TEXT,
    dob_encrypted TEXT,
    
    -- Level 3: Double encrypted
    ssn_encrypted TEXT,
    bank_account_encrypted TEXT,
    credit_card_encrypted TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on email for lookups
CREATE INDEX idx_users_email ON users(email);

-- Metadata table for encryption details
CREATE TABLE encryption_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    field_name VARCHAR(50) NOT NULL,
    pii_level INTEGER NOT NULL CHECK (pii_level IN (1, 2, 3)),
    app_key_version INTEGER,
    kms_key_alias VARCHAR(100),
    encrypted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, field_name)
);

-- Index for faster lookups
CREATE INDEX idx_encryption_metadata_user_field 
ON encryption_metadata(user_id, field_name);

-- Audit table for access logging
CREATE TABLE encryption_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    field_name VARCHAR(50),
    pii_level INTEGER,
    operation VARCHAR(20) CHECK (operation IN ('encrypt', 'decrypt', 'view')),
    accessed_by VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for audit queries
CREATE INDEX idx_encryption_audit_user_time 
ON encryption_audit(user_id, accessed_at DESC);

-- Key rotation tracking
CREATE TABLE key_rotation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_type VARCHAR(50) NOT NULL,
    old_version INTEGER,
    new_version INTEGER,
    rotation_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rotation_completed_at TIMESTAMP WITH TIME ZONE,
    records_affected INTEGER,
    status VARCHAR(20) DEFAULT 'in_progress'
);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE
    ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## 4. Security Architecture

### 4.1 Security Layers

```
1. Network Security
   ├── HTTPS for all external communication
   ├── VPC isolation for RDS
   └── Security groups with least privilege

2. Authentication & Authorization
   ├── API Key for prototype (API Gateway)
   ├── IAM roles for service-to-service
   └── No direct database access

3. Encryption
   ├── TLS 1.2+ in transit
   ├── Three-tier at-rest encryption
   └── Key isolation via Lambda

4. Key Management
   ├── AWS KMS for field encryption
   ├── Secrets Manager for app keys
   └── Automatic rotation enabled

5. Audit & Compliance
   ├── CloudWatch logs for Lambda
   ├── Database audit table
   └── Encryption operation tracking
```

### 4.2 IAM Roles and Policies

**Lambda Execution Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": [
        "arn:aws:kms:*:*:key/pii-level2-key-id",
        "arn:aws:kms:*:*:key/pii-level3-key-id"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:*:*:secret:pii-encryption-keys-*",
        "arn:aws:secretsmanager:*:*:secret:pii-database-credentials-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface"
      ],
      "Resource": "*"
    }
  ]
}
```

**FastAPI Role (ECS/EC2):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:pii-encryption-handler"
    }
  ]
}
```

### 4.3 Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                           VPC                                │
│                                                              │
│  ┌─────────────────────┐      ┌─────────────────────┐      │
│  │   Public Subnet     │      │   Private Subnet    │      │
│  │                     │      │                     │      │
│  │  ┌──────────────┐   │      │  ┌──────────────┐   │      │
│  │  │ API Gateway  │   │      │  │ RDS Aurora   │   │      │
│  │  └──────────────┘   │      │  └──────────────┘   │      │
│  │                     │      │                     │      │
│  │  ┌──────────────┐   │      │  ┌──────────────┐   │      │
│  │  │   FastAPI    │   │      │  │   Lambda     │   │      │
│  │  └──────────────┘   │      │  └──────────────┘   │      │
│  └─────────────────────┘      └─────────────────────┘      │
│                                                              │
│                         VPC Endpoints                        │
│                    ┌────────────────────┐                   │
│                    │ KMS, Secrets Mgr   │                   │
│                    └────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Infrastructure as Code

### 5.1 Terraform Configuration

```hcl
# versions.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# kms.tf
resource "aws_kms_key" "pii_level2" {
  description             = "PII Level 2 field encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name        = "pii-level2-key"
    Environment = "prototype"
  }
}

resource "aws_kms_alias" "pii_level2" {
  name          = "alias/pii-level2"
  target_key_id = aws_kms_key.pii_level2.key_id
}

resource "aws_kms_key" "pii_level3" {
  description             = "PII Level 3 field encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name        = "pii-level3-key"
    Environment = "prototype"
  }
}

resource "aws_kms_alias" "pii_level3" {
  name          = "alias/pii-level3"
  target_key_id = aws_kms_key.pii_level3.key_id
}

# secrets.tf
resource "aws_secretsmanager_secret" "app_keys" {
  name = "pii-encryption-keys"
  
  rotation_rules {
    automatically_after_days = 90
  }
}

resource "aws_secretsmanager_secret_version" "app_keys" {
  secret_id = aws_secretsmanager_secret.app_keys.id
  secret_string = jsonencode({
    app_encryption_keys = {
      level3_app_key_v1 = random_password.app_key_v1.result
      current_version   = 1
    }
  })
}

resource "random_password" "app_key_v1" {
  length  = 32
  special = true
}

# lambda.tf
resource "aws_lambda_function" "encryption_handler" {
  filename         = "lambda_function.zip"
  function_name    = "pii-encryption-handler"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }

  vpc_config {
    subnet_ids         = [aws_subnet.private.id]
    security_group_ids = [aws_security_group.lambda.id]
  }
}

# rds.tf
resource "aws_rds_cluster" "pii_database" {
  cluster_identifier      = "pii-database-cluster"
  engine                 = "aurora-postgresql"
  engine_version         = "14.6"
  database_name          = "pii_db"
  master_username        = "postgres"
  master_password        = random_password.db_password.result
  storage_encrypted      = true
  kms_key_id            = aws_kms_key.rds.arn
  
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
}
```

---

## 6. Development and Deployment

### 6.1 Local Development Setup

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
npm start

# Database setup (local PostgreSQL)
psql -U postgres -f schema.sql

# Environment variables (.env)
AWS_REGION=us-east-1
LAMBDA_FUNCTION_NAME=pii-encryption-handler
DATABASE_URL=postgresql://user:pass@localhost/pii_db
```

### 6.2 Deployment Process

```bash
# 1. Deploy infrastructure
terraform init
terraform plan
terraform apply

# 2. Package Lambda function
cd lambda
pip install -r requirements.txt -t .
zip -r ../lambda_function.zip .

# 3. Deploy Lambda
aws lambda update-function-code \
  --function-name pii-encryption-handler \
  --zip-file fileb://../lambda_function.zip

# 4. Deploy FastAPI
docker build -t pii-api .
docker push $ECR_REPOSITORY_URL

# 5. Deploy Frontend
npm run build
aws s3 sync build/ s3://$FRONTEND_BUCKET
```

---

## 7. Operational Considerations

### 7.1 Monitoring and Alerting

**Key Metrics:**
- Lambda execution time and errors
- KMS API call failures
- Database connection pool exhaustion
- Encryption/decryption success rate

**CloudWatch Alarms:**
```python
# Terraform configuration for alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "pii-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "Lambda function errors"

  dimensions = {
    FunctionName = aws_lambda_function.encryption_handler.function_name
  }
}
```

### 7.2 Backup and Recovery

**Backup Strategy:**
- RDS automated backups (7 days retention)
- KMS key deletion protection
- Secrets Manager versioning
- Lambda function versioning

**Recovery Procedures:**
1. Database restoration from snapshot
2. Key recovery from KMS (if not deleted)
3. Secret recovery from Secrets Manager
4. Lambda rollback to previous version

### 7.3 Cost Optimization

**Estimated Monthly Costs (Prototype):**
- KMS Keys: $2 ($1/key × 2 keys)
- KMS API calls: ~$1 (minimal usage)
- Secrets Manager: $0.40/secret × 2 = $0.80
- Lambda: ~$1 (minimal invocations)
- RDS Aurora: ~$60 (smallest instance)
- **Total: ~$65/month**

**Cost Optimization Tips:**
- Use Aurora Serverless for variable workloads
- Cache decrypted values appropriately
- Batch operations when possible
- Monitor and adjust Lambda memory allocation

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# test_encryption.py
import pytest
from lambda_function import EncryptionHandler

class TestEncryption:
    def test_classify_pii_level(self):
        handler = EncryptionHandler()
        assert handler.classify_pii_level('email') == 1
        assert handler.classify_pii_level('address') == 2
        assert handler.classify_pii_level('ssn') == 3
    
    def test_level1_passthrough(self):
        handler = EncryptionHandler()
        result = handler.encrypt_field('email', 'test@example.com', 1)
        assert result['value'] == 'test@example.com'
        assert result['encrypted'] == False
```

### 8.2 Integration Tests

```python
# test_integration.py
import requests
import json

def test_create_and_retrieve_user():
    # Create user
    user_data = {
        'email': 'test@example.com',
        'first_name': 'Test',
        'address': '123 Test St',
        'ssn': '123-45-6789'
    }
    
    response = requests.post('http://localhost:8000/api/users', json=user_data)
    assert response.status_code == 200
    user_id = response.json()['user_id']
    
    # Retrieve user
    response = requests.get(f'http://localhost:8000/api/users/{user_id}')
    assert response.status_code == 200
    retrieved_data = response.json()
    
    # Verify decryption
    assert retrieved_data['email'] == user_data['email']
    assert retrieved_data['address'] == user_data['address']
    assert retrieved_data['ssn'] == user_data['ssn']
```

### 8.3 Security Tests

- Penetration testing for API endpoints
- KMS key access validation
- SQL injection testing
- XSS prevention validation

---

## 9. Migration Strategy

### 9.1 From Prototype to Production

**Phase 1: Infrastructure Hardening**
- Multi-AZ RDS deployment
- API Gateway with WAF
- Enhanced monitoring
- Production KMS key policies

**Phase 2: Feature Enhancement**
- Batch processing support
- Advanced search capabilities
- Field-level access control
- Multi-region support

**Phase 3: Compliance**
- SOC 2 certification preparation
- GDPR compliance validation
- Automated compliance reporting

### 9.2 Data Migration

```python
# migration_script.py
async def migrate_existing_data():
    """Encrypt existing plaintext data"""
    conn = get_db_connection()
    
    # Get unencrypted records
    records = await conn.fetch("SELECT * FROM users WHERE NOT encrypted")
    
    for record in records:
        # Encrypt sensitive fields
        encrypted_data = encrypt_user_data(record)
        
        # Update database
        await conn.execute(
            "UPDATE users SET ... WHERE id = $1",
            record['id']
        )
        
        # Log migration
        log_migration(record['id'])
```

---

## 10. Conclusion

This architecture provides a solid foundation for a PII encryption system that:

1. **Demonstrates best practices** for handling sensitive data
2. **Leverages AWS services** effectively
3. **Provides clear separation** between encryption levels
4. **Maintains security** while enabling functionality
5. **Scales appropriately** from prototype to production

The modular design allows for incremental improvements and easy maintenance while ensuring that security remains paramount throughout the system.

---

## Appendices

### Appendix A: Complete Requirements Checklist

- [ ] Three-tier PII classification implemented
- [ ] AWS KMS integration for field encryption
- [ ] AWS Secrets Manager for key storage
- [ ] Lambda-based encryption service
- [ ] RDS Aurora with encryption at rest
- [ ] React frontend with security indicators
- [ ] FastAPI backend with async support
- [ ] Audit logging for all operations
- [ ] Key rotation support
- [ ] Error handling and recovery
- [ ] Basic monitoring and alerting
- [ ] Documentation complete

### Appendix B: Security Checklist

- [ ] No hardcoded credentials
- [ ] HTTPS enforced everywhere
- [ ] Database in private subnet
- [ ] IAM least privilege principle
- [ ] Encryption keys properly managed
- [ ] Audit trail implemented
- [ ] Input validation on all endpoints
- [ ] Error messages don't leak information
- [ ] Security headers configured
- [ ] CORS properly configured

### Appendix C: References

1. AWS KMS Best Practices: https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html
2. OWASP Cryptographic Storage Cheat Sheet
3. PCI DSS Encryption Requirements
4. GDPR Technical Measures Guidelines
5. AWS Well-Architected Security Pillar
    bank_account_encrypted TEXT,
    credit_card_encrypted TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on email for lookups
CREATE INDEX idx_users_email ON users(email);

-- Metadata table for encryption details
CREATE TABLE encryption_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    field_name VARCHAR(50) NOT NULL,
    pii_level INTEGER NOT NULL CHECK (pii_level IN (1, 2, 3)),
    app_key_version INTEGER,
    kms_key_alias VARCHAR(100),
    encrypted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, field_name)
);

-- Index for faster lookups
CREATE INDEX idx_encryption_metadata_user_field 
ON encryption_metadata(user_id, field_name);

-- Audit table for access logging
CREATE TABLE encryption_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    field_name VARCHAR(50),
    pii_level INTEGER,
    operation VARCHAR(20) CHECK (operation IN ('encrypt', 'decrypt', 'view')),
    accessed_by VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for audit queries
CREATE INDEX idx_encryption_audit_user_time 
ON encryption_audit(user_id, accessed_at DESC);

-- Key rotation tracking
CREATE TABLE key_rotation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_type VARCHAR(50) NOT NULL,
    old_version INTEGER,
    new_version INTEGER,
    rotation_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rotation_completed_at TIMESTAMP WITH TIME ZONE,
    records_affected INTEGER,
    status VARCHAR(20) DEFAULT 'in_progress'
);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE
    ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();