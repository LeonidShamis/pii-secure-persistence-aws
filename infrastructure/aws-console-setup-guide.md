# AWS Console Setup Guide
## PII Encryption System Manual Configuration

This guide provides step-by-step instructions for manually setting up AWS resources through the AWS Console, using the Terraform configurations as reference.

## Prerequisites

- AWS Account with appropriate permissions
- Access to AWS Console
- Understanding of AWS KMS, Secrets Manager, and IAM concepts

---

## Phase 2: AWS Security Infrastructure Setup

### Step 1: Create KMS Keys

#### 1.1 Create Level 2 KMS Key (Medium Sensitivity)

1. **Navigate to AWS Console > KMS > Customer managed keys**
2. **Click "Create key"**
3. **Configure key:**
   - Key type: `Symmetric`
   - Key usage: `Encrypt and decrypt`
   - Advanced options: Leave as default
4. **Add labels:**
   - Alias: `pii-level2`
   - Description: `PII Level 2 field encryption for medium sensitivity data`
5. **Define key administrative permissions:**
   - Add your IAM user/role as key administrator
6. **Define key usage permissions:**
   - Add Lambda execution role (will create in Step 3)
   - Allow operations: `Encrypt`, `Decrypt`, `ReEncrypt`, `GenerateDataKey`, `DescribeKey`
7. **Review and create**
8. **Add tags:**
   ```
   Name: pii-encryption-level2-key
   Environment: prototype
   PIILevel: 2
   Purpose: Field-level encryption for medium sensitivity PII
   Project: pii-encryption
   ```

#### 1.2 Create Level 3 KMS Key (High Sensitivity)

1. **Repeat the above process with these changes:**
   - Alias: `pii-level3`
   - Description: `PII Level 3 field encryption for high sensitivity data`
   - Tags:
     ```
     Name: pii-encryption-level3-key
     Environment: prototype
     PIILevel: 3
     Purpose: Double encryption for high sensitivity PII
     Project: pii-encryption
     ```

#### 1.3 Create RDS KMS Key (Database Encryption)

1. **Create another key:**
   - Alias: `pii-rds-encryption`
   - Description: `RDS Aurora encryption for PII database`
   - Key usage permissions: Add RDS service
   - Tags:
     ```
     Name: pii-encryption-rds-key
     Environment: prototype
     Purpose: RDS Aurora database encryption
     Project: pii-encryption
     ```

#### 1.4 Enable Automatic Key Rotation

For each KMS key:
1. Go to key details page
2. Click "Key rotation" tab
3. Enable "Automatically rotate this KMS key every year"

---

### Step 2: Create Secrets Manager Secrets

#### 2.1 Create Application Encryption Keys Secret

1. **Navigate to AWS Console > Secrets Manager**
2. **Click "Store a new secret"**
3. **Select "Other type of secret"**
4. **Secret key/value pairs:**
   ```json
   {
     "app_encryption_keys": {
       "level3_app_key_v1": "[GENERATE-32-BYTE-FERNET-KEY]",
       "current_version": 1
     }
   }
   ```
   
   **Generate Fernet Key:**
   ```python
   # Use this Python code to generate a Fernet key:
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   ```

5. **Secret name:** `pii-encryption-keys`
6. **Description:** `Application-layer encryption keys for Level 3 PII double encryption`
7. **Configure automatic rotation:**
   - Enable rotation: Yes
   - Rotation schedule: Every 90 days
8. **Add tags:**
   ```
   Name: pii-encryption-keys
   Environment: prototype
   Purpose: Application-layer encryption keys
   Project: pii-encryption
   ```

#### 2.2 Create Database Credentials Secret

1. **Store another secret:**
2. **Select "Credentials for RDS database"**
3. **Database details:**
   - User name: `postgres`
   - Password: `[GENERATE-SECURE-PASSWORD]`
   - Database: `pii_db`
4. **Secret name:** `pii-database-credentials`
5. **Description:** `Database credentials for PII encryption system`

---

### Step 3: Create IAM Roles and Policies

#### 3.1 Lambda Execution Role

1. **Navigate to AWS Console > IAM > Roles**
2. **Click "Create role"**
3. **Trusted entity:** AWS service > Lambda
4. **Permissions policies:** Start with `AWSLambdaVPCExecutionRole`
5. **Role name:** `pii-encryption-lambda-execution-role`
6. **Role description:** `Execution role for PII encryption Lambda function`

#### 3.2 Custom Policy for Lambda

1. **Create custom policy:**
   - Policy name: `PIIEncryptionLambdaPolicy`
   - Policy document:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "kms:Encrypt",
           "kms:Decrypt",
           "kms:ReEncrypt*",
           "kms:GenerateDataKey*",
           "kms:DescribeKey"
         ],
         "Resource": [
           "arn:aws:kms:*:*:key/[LEVEL2-KEY-ID]",
           "arn:aws:kms:*:*:key/[LEVEL3-KEY-ID]"
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
       }
     ]
   }
   ```

2. **Attach policy to Lambda role**

#### 3.3 FastAPI Role

1. **Create role:**
   - Trusted entity: EC2 (or ECS if using containers)
   - Role name: `pii-encryption-fastapi-role`
2. **Create custom policy:**
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

---

### Step 4: Update KMS Key Policies

After creating IAM roles, update KMS key policies to grant access:

#### 4.1 Update Level 2 KMS Key Policy

1. **Go to KMS > Customer managed keys > pii-level2**
2. **Click "Key policy" tab**
3. **Add statement:**
   ```json
   {
     "Sid": "AllowLambdaAccess",
     "Effect": "Allow",
     "Principal": {
       "AWS": "arn:aws:iam::[ACCOUNT-ID]:role/pii-encryption-lambda-execution-role"
     },
     "Action": [
       "kms:Encrypt",
       "kms:Decrypt",
       "kms:ReEncrypt*",
       "kms:GenerateDataKey*",
       "kms:DescribeKey"
     ],
     "Resource": "*"
   }
   ```

#### 4.2 Update Level 3 KMS Key Policy

Repeat the same process for the Level 3 key.

---

### Step 5: Verification and Testing

#### 5.1 Test KMS Key Access

Using AWS CLI or console:
```bash
# Test Level 2 key
aws kms encrypt --key-id alias/pii-level2 --plaintext "test data"

# Test Level 3 key  
aws kms encrypt --key-id alias/pii-level3 --plaintext "test data"
```

#### 5.2 Test Secrets Manager Access

```bash
# Test application keys secret
aws secretsmanager get-secret-value --secret-id pii-encryption-keys

# Test database credentials
aws secretsmanager get-secret-value --secret-id pii-database-credentials
```

#### 5.3 Verify IAM Permissions

Use [IAM Policy Simulator](https://policysim.aws.amazon.com/) to test the created policies against the expected actions.

---

## Resource Summary

After completing this setup, you should have:

### KMS Keys
- ✅ `alias/pii-level2` - Level 2 PII encryption
- ✅ `alias/pii-level3` - Level 3 PII encryption  
- ✅ `alias/pii-rds-encryption` - Database encryption

### Secrets Manager
- ✅ `pii-encryption-keys` - Application encryption keys
- ✅ `pii-database-credentials` - Database credentials

### IAM Roles
- ✅ `pii-encryption-lambda-execution-role` - Lambda function role
- ✅ `pii-encryption-fastapi-role` - FastAPI application role

### Security Features
- ✅ Automatic key rotation enabled
- ✅ Least privilege IAM policies
- ✅ Proper resource tagging
- ✅ Secure credential management

---

## Next Steps

1. **Document Resource ARNs:** Note down all the created resource ARNs for Lambda configuration
2. **Test Access:** Verify all permissions are working correctly
3. **Proceed to Phase 3:** Lambda encryption service implementation
4. **Security Review:** Validate all security configurations meet requirements

## Important Notes

- Replace `[ACCOUNT-ID]`, `[LEVEL2-KEY-ID]`, etc. with actual values
- Store all ARNs and identifiers securely for Lambda configuration
- Regularly review and audit IAM permissions
- Monitor KMS key usage and costs
- Enable CloudTrail for audit logging of key usage