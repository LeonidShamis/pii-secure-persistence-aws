# AWS Lambda Console Setup Guide
## PII Encryption Handler Function - Detailed Manual Setup

This guide provides comprehensive, step-by-step instructions for manually creating and configuring the PII Encryption Lambda function through the AWS Console, including all necessary IAM roles, security groups, VPC configuration, and RDS connectivity.

## Prerequisites

Before starting, ensure you have completed:
- ✅ **Phase 1**: Database Foundation (RDS Aurora PostgreSQL with schema)
- ✅ **Phase 2**: AWS Security Infrastructure (KMS keys, Secrets Manager, IAM roles)
- ✅ **Phase 3**: Lambda code development (this guide deploys that code)

### Required Information
Gather the following information before starting:
- **VPC ID**: Where your RDS database is located
- **Private Subnet IDs**: At least 2 subnets in different AZs
- **RDS Security Group ID**: Security group attached to your RDS instance
- **RDS Endpoint**: Your Aurora PostgreSQL cluster endpoint
- **AWS Region**: Where all resources are located (e.g., us-east-1)

## Overview

The Lambda function `pii-encryption-handler` serves as the core encryption service with these capabilities:
- Three-tier PII classification and encryption
- Database operations (create, read, update, delete users)
- Health monitoring and audit trail
- Integration with KMS and Secrets Manager
- Secure VPC access to RDS database

---

## Step 1: Create Security Groups

We need to create security groups first to ensure proper network isolation between Lambda and RDS.

### 1.1 Create Lambda Security Group

#### Navigate to VPC Console
1. Go to **AWS Console** → **Services** → **VPC**
2. In the left navigation, click **Security Groups**
3. Click **Create security group**

#### Configure Lambda Security Group
1. **Security group name**: `pii-lambda-sg`
2. **Description**: `Security group for PII encryption Lambda function`
3. **VPC**: Select the VPC where your RDS database is located

#### Configure Outbound Rules
Click **Add rule** for each of the following outbound rules:

**Rule 1: HTTPS for AWS APIs**
- **Type**: HTTPS
- **Protocol**: TCP
- **Port range**: 443
- **Destination**: 0.0.0.0/0
- **Description**: Access to AWS APIs (KMS, Secrets Manager)

**Rule 2: DNS Resolution**
- **Type**: Custom TCP
- **Protocol**: TCP  
- **Port range**: 53
- **Destination**: 0.0.0.0/0
- **Description**: DNS resolution

**Rule 3: RDS Database Access**
- **Type**: PostgreSQL
- **Protocol**: TCP
- **Port range**: 5432
- **Destination**: Custom → Select the RDS security group (we'll configure this next)
- **Description**: Access to RDS PostgreSQL database

5. **Inbound rules**: Leave empty (Lambda doesn't need inbound access)
6. Click **Create security group**
7. **Note the Security Group ID**: `sg-xxxxxxxxx` (you'll need this later)

### 1.2 Update RDS Security Group

#### Navigate to RDS Security Group
1. In VPC Console → **Security Groups**
2. Find your RDS security group (check your RDS instance for the attached security group)
3. Click on the security group ID

#### Add Inbound Rule for Lambda
1. Click **Edit inbound rules**
2. Click **Add rule**
3. Configure the new rule:
   - **Type**: PostgreSQL
   - **Protocol**: TCP
   - **Port range**: 5432
   - **Source**: Custom → Select `pii-lambda-sg` (the Lambda security group we just created)
   - **Description**: Allow access from PII Lambda function
4. Click **Save rules**

---

## Step 2: Create Lambda Execution Role with Detailed Permissions

### 2.1 Navigate to IAM Console
1. Go to **AWS Console** → **Services** → **IAM**
2. Click **Roles** in the left navigation
3. Click **Create role**

### 2.2 Configure Trust Relationship
1. **Select trusted entity**: AWS service
2. **Use case**: Lambda
3. Click **Next**

### 2.3 Create Custom Policy for PII Lambda Function

Before attaching policies to the role, we need to create a comprehensive custom policy.

#### Create the Custom Policy
1. Open a new tab and go to **IAM** → **Policies**
2. Click **Create policy**
3. Click **JSON** tab
4. **Clear all existing content** and paste the following comprehensive policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CloudWatchLogsPermissions",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams"
            ],
            "Resource": [
                "arn:aws:logs:*:*:log-group:/aws/lambda/pii-encryption-handler",
                "arn:aws:logs:*:*:log-group:/aws/lambda/pii-encryption-handler:*"
            ]
        },
        {
            "Sid": "VPCPermissions",
            "Effect": "Allow",
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface",
                "ec2:AttachNetworkInterface",
                "ec2:DetachNetworkInterface",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeSubnets",
                "ec2:DescribeVpcs"
            ],
            "Resource": "*"
        },
        {
            "Sid": "KMSKeyPermissions",
            "Effect": "Allow",
            "Action": [
                "kms:Encrypt",
                "kms:Decrypt",
                "kms:DescribeKey",
                "kms:GenerateDataKey",
                "kms:CreateGrant"
            ],
            "Resource": [
                "arn:aws:kms:*:*:key/*"
            ],
            "Condition": {
                "StringLike": {
                    "kms:ViaService": [
                        "secretsmanager.*.amazonaws.com",
                        "lambda.*.amazonaws.com"
                    ]
                }
            }
        },
        {
            "Sid": "KMSAliasPermissions", 
            "Effect": "Allow",
            "Action": [
                "kms:Encrypt",
                "kms:Decrypt", 
                "kms:DescribeKey",
                "kms:GenerateDataKey"
            ],
            "Resource": "*",
            "Condition": {
                "ForAnyValue:StringEquals": {
                    "kms:ResourceAliases": [
                        "alias/pii-level2",
                        "alias/pii-level3"
                    ]
                }
            }
        },
        {
            "Sid": "SecretsManagerPermissions",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": [
                "arn:aws:secretsmanager:*:*:secret:pii-encryption-keys-*",
                "arn:aws:secretsmanager:*:*:secret:pii-database-credentials-*"
            ]
        },
        {
            "Sid": "STSPermissions",
            "Effect": "Allow", 
            "Action": [
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

5. Click **Next: Tags** (optionally add tags)
6. Click **Next: Review**
7. **Name**: `PIIEncryptionLambdaCustomPolicy`
8. **Description**: `Comprehensive permissions for PII encryption Lambda function including VPC, KMS, Secrets Manager, and CloudWatch access`
9. Click **Create policy**

### 2.4 Attach Policies to Role

#### Return to Role Creation
1. Go back to the **Create role** tab
2. In the **Add permissions** section, search for and select the following policies:

**Policy 1: Custom Policy (Required)**
- Search for: `PIIEncryptionLambdaCustomPolicy`
- ✅ Select the checkbox

**Policy 2: Basic Execution (Backup - in case custom policy doesn't cover everything)**
- Search for: `AWSLambdaBasicExecutionRole`
- ✅ Select the checkbox

**Policy 3: VPC Access (Backup - in case custom policy doesn't cover everything)**
- Search for: `AWSLambdaVPCAccessExecutionRole` 
- ✅ Select the checkbox

3. Click **Next**

### 2.5 Complete Role Creation
1. **Role name**: `PIIEncryptionLambdaExecutionRole`
2. **Description**: `Execution role for PII encryption Lambda function with VPC, KMS, and Secrets Manager access`
3. **Review the summary** to ensure all 3 policies are attached
4. Click **Create role**

### 2.6 Verify Role Creation and Note ARN
1. Click on the newly created role `PIIEncryptionLambdaExecutionRole`
2. **Copy the Role ARN** from the Summary section:
   ```
   arn:aws:iam::YOUR-ACCOUNT-ID:role/PIIEncryptionLambdaExecutionRole
   ```
3. **Verify Attached Policies** - You should see:
   - ✅ PIIEncryptionLambdaCustomPolicy
   - ✅ AWSLambdaBasicExecutionRole  
   - ✅ AWSLambdaVPCAccessExecutionRole

### 2.7 Test Role Permissions (Optional Verification)
1. Click on **Trust relationships** tab
2. Verify the trust policy allows Lambda service:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

## Step 3: Create Lambda Deployment Package

### 3.1 Prepare Development Environment

#### From Your Local Machine
Ensure you have the Lambda code from Phase 3:

```bash
cd /path/to/pii-secure-persistence-aws/lambda

# Verify you have the correct files
ls -la
# Should see: src/, deploy.py, test_lambda.py, pyproject.toml, etc.
```

#### Install Dependencies and Create Package
```bash
# Ensure uv environment is active
uv sync

# Create deployment package (this will take a few minutes)
uv run python deploy.py --package-only

# Verify the package was created
ls -la *.zip
# Should see: pii-encryption-lambda.zip
```

### 3.2 Package Size and Contents Verification

#### Check Package Size
```bash
# Check file size (should be under 50MB for direct upload)
ls -lh pii-encryption-lambda.zip
# Expected size: ~15-25MB
```

#### Verify Package Contents (Optional)
```bash
# Extract to temporary directory to verify contents
mkdir temp_verify
cd temp_verify
unzip ../pii-encryption-lambda.zip
ls -la

# Should contain:
# - lambda_function.py (main handler)
# - pii_encryption_lambda/ (our source code)
# - boto3/ cryptography/ psycopg2/ (dependencies)
# - Various .dist-info/ directories

cd ..
rm -rf temp_verify
```

### 3.3 Upload Package to AWS (Alternative Methods)

If the package is too large for direct upload, use S3:

#### Option A: Direct Upload (< 50MB)
Use the package directly in the Lambda console (covered in next step)

#### Option B: S3 Upload (if package > 50MB)
```bash
# Upload to S3 bucket (replace with your bucket name)
aws s3 cp pii-encryption-lambda.zip s3://your-deployment-bucket/lambda/

# Note the S3 URL for later use
```

---

## Step 4: Create Lambda Function with Detailed Configuration

### 4.1 Navigate to Lambda Console
1. Go to **AWS Console** → **Services** → **Lambda**
2. Ensure you're in the correct region (same as your RDS database)
3. Click **Create function**

### 4.2 Configure Function Creation
1. **Function option**: Author from scratch
2. **Function name**: `pii-encryption-handler`
3. **Runtime**: Python 3.10 (recommended) or Python 3.11
4. **Architecture**: x86_64
5. **Execution role**: Use an existing role
6. **Existing role**: `PIIEncryptionLambdaExecutionRole` (created in Step 2)

**Advanced Settings (Expand this section):**
7. **Code signing**: Disabled
8. **Dead letter queue**: Disabled (for now)
9. **VPC**: No VPC (we'll configure this later)
10. **File systems**: None
11. **Monitoring**: Enable AWS X-Ray tracing: Active
12. Click **Create function**

### 4.3 Upload Deployment Package

#### Method 1: Direct Upload (Recommended if < 50MB)
1. In the **Code** tab, locate the **Code source** section
2. Click **Upload from** dropdown → **.zip file**
3. Click **Upload** button
4. Select your `pii-encryption-lambda.zip` file
5. Click **Save**
6. **Wait for upload to complete** (you'll see a success message)

#### Method 2: S3 Upload (if package > 50MB)
1. In the **Code** tab, click **Upload from** → **Amazon S3 location**
2. **Amazon S3 link URL**: Enter your S3 URL from step 3.3
3. Click **Save**

### 4.4 Verify Code Upload
1. In the code editor, you should see:
   - `lambda_function.py` at the root level
   - Various dependency folders
2. Click on `lambda_function.py` to verify it contains the import statement:
   ```python
   from pii_encryption_lambda.lambda_function import lambda_handler
   ```

### 4.5 Configure Basic Function Settings

#### General Configuration
1. Go to **Configuration** tab
2. Click **General configuration** → **Edit**
3. Configure the following:
   - **Description**: `PII encryption service with three-tier security levels`
   - **Handler**: `lambda_function.lambda_handler` (verify this is correct)
   - **Timeout**: 5 minutes (300 seconds) - increased for database operations
   - **Memory**: 512 MB - increased for encryption operations
   - **Ephemeral storage**: 512 MB (default)
4. Click **Save**

#### Environment Variables
1. Click **Environment variables** → **Edit**
2. Click **Add environment variable** for each:

**Variable 1:**
- **Key**: `AWS_REGION`
- **Value**: `us-east-1` (or your actual region)

**Variable 2:**
- **Key**: `LOG_LEVEL`
- **Value**: `INFO`

**Variable 3 (Optional for debugging):**
- **Key**: `PYTHONPATH`
- **Value**: `/var/runtime:/var/task:/opt/python`

3. Click **Save**

---

## Step 5: Configure VPC Access for Database

### 5.1 Get Required Information First

Before configuring VPC, gather this information:

#### Find Your RDS Information
1. Go to **RDS Console** → **Databases**
2. Click on your PII database cluster
3. **Note down:**
   - **VPC ID**: (e.g., vpc-0123456789abcdef0)
   - **Subnet group**: (e.g., pii-db-subnet-group)
   - **Security groups**: (e.g., sg-rds123456)
   - **Endpoint**: (e.g., pii-cluster.cluster-xyz.us-east-1.rds.amazonaws.com)

#### Find Your Private Subnets
1. Go to **VPC Console** → **Subnets**
2. Filter by your VPC ID
3. Look for subnets tagged as "private" or subnets that have:
   - **Route table**: Routes to NAT Gateway (not Internet Gateway)
   - **Available IPs**: Should have available capacity
4. **Select at least 2 subnets in different Availability Zones**
5. **Note down the Subnet IDs**: (e.g., subnet-0123456, subnet-0789abc)

### 5.2 Configure Lambda VPC Settings

#### Navigate to VPC Configuration
1. In your Lambda function, go to **Configuration** tab
2. Click **VPC** in the left sidebar
3. Click **Edit**

#### Configure VPC Settings
1. **VPC**: Select the VPC where your RDS database is located
   - Choose the VPC ID you noted from RDS configuration
   
2. **Subnets**: Select **private subnets only**
   - ✅ Select subnet-0123456 (AZ: us-east-1a) - Private
   - ✅ Select subnet-0789abc (AZ: us-east-1b) - Private
   - **Do NOT select public subnets** (for security)
   
3. **Security groups**: Select the Lambda security group we created
   - ✅ Select `pii-lambda-sg` (created in Step 1.1)
   - **Remove any default security groups**

4. Click **Save**

#### Verify VPC Configuration
After saving, you should see:
- **VPC**: Your RDS VPC
- **Subnets**: 2+ private subnets in different AZs
- **Security groups**: pii-lambda-sg
- **Status**: "VPC configuration updated successfully"

### 5.3 Verify Network Connectivity

#### Test Database Connectivity (Coming in Step 6)
The VPC configuration will be verified when we test the Lambda function.

#### Common VPC Issues and Solutions

**Issue 1: "ENI (Elastic Network Interface) creation failed"**
- **Cause**: Insufficient IPs in selected subnets
- **Solution**: Choose subnets with more available IPs or larger CIDR blocks

**Issue 2: "Lambda function timeout in VPC"**
- **Cause**: No internet access for AWS API calls
- **Solution**: Ensure private subnets route to NAT Gateway, not Internet Gateway

**Issue 3: "Cannot resolve DNS names"**
- **Cause**: VPC doesn't have DNS resolution enabled
- **Solution**: Go to VPC settings and enable DNS resolution and DNS hostnames

### 5.4 Verify RDS Security Group (Double-Check)

#### Confirm RDS Allows Lambda Access
1. Go to **RDS Console** → **Databases** → Your PII database
2. Click **Connectivity & security** tab
3. Click on the **VPC security groups** link
4. Verify **Inbound rules** include:
   - **Type**: PostgreSQL
   - **Port**: 5432  
   - **Source**: `pii-lambda-sg` (your Lambda security group)
   - **Description**: Allow access from PII Lambda function

#### If the Rule is Missing
1. Click **Edit inbound rules**
2. Click **Add rule**
3. Configure:
   - **Type**: PostgreSQL
   - **Port**: 5432
   - **Source**: Custom → `pii-lambda-sg`
   - **Description**: Allow access from PII Lambda function
4. Click **Save rules**

---

## Step 6: Comprehensive Lambda Function Testing

### 6.1 Create Test Events for All Operations

#### Navigate to Test Configuration
1. In your Lambda function, go to **Test** tab
2. Click **Create new test event**

#### Test Event 1: Health Check
1. **Event name**: `health-check`
2. **Event JSON**:
```json
{
  "operation": "health"
}
```
3. Click **Save**

#### Test Event 2: Create User (Level 1, 2, 3 Fields)
1. Click **Create new test event**
2. **Event name**: `create-user-test`
3. **Event JSON**:
```json
{
  "operation": "create_user",
  "data": {
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1-555-0123",
    "address": "123 Main Street, Anytown, USA",
    "date_of_birth": "1990-01-01",
    "ssn": "123-45-6789",
    "bank_account": "1234567890"
  }
}
```
4. Click **Save**

#### Test Event 3: List Users
1. Click **Create new test event**
2. **Event name**: `list-users`
3. **Event JSON**:
```json
{
  "operation": "list_users",
  "limit": 10,
  "offset": 0
}
```
4. Click **Save**

#### Test Event 4: Get User (Placeholder)
1. Click **Create new test event**
2. **Event name**: `get-user-test`
3. **Event JSON** (you'll update user_id after creating a user):
```json
{
  "operation": "get_user",
  "user_id": "REPLACE-WITH-ACTUAL-USER-ID"
}
```
4. Click **Save**

#### Test Event 5: Audit Trail
1. Click **Create new test event**
2. **Event name**: `audit-trail`
3. **Event JSON**:
```json
{
  "operation": "audit_trail",
  "limit": 20
}
```
4. Click **Save**

### 6.2 Run Tests in Order and Verify Results

#### Test 1: Health Check (Critical)
1. Select **health-check** event
2. Click **Test**
3. **Wait for execution** (first run may take 30-60 seconds due to cold start)

**Expected Success Response:**
```json
{
  "statusCode": 200,
  "body": "{
    \"health\": {
      \"lambda\": \"healthy\",
      \"kms\": \"healthy\",
      \"secrets_manager\": \"healthy\",
      \"database\": \"healthy\",
      \"database_schema\": \"healthy\"
    },
    \"timestamp\": \"2025-07-21T...\",
    \"success\": true
  }"
}
```

**If Health Check Fails:**
- **KMS Error**: Check IAM permissions for KMS aliases
- **Secrets Manager Error**: Verify secrets exist and IAM permissions
- **Database Error**: Check VPC configuration, security groups, and database credentials
- **Schema Error**: Verify database schema was created in Phase 1

#### Test 2: Create User (Encryption Test)
1. Select **create-user-test** event
2. Click **Test**

**Expected Success Response:**
```json
{
  "statusCode": 200,
  "body": "{
    \"user_id\": \"550e8400-e29b-41d4-a716-446655440000\",
    \"success\": true,
    \"processed_fields\": 8,
    \"message\": \"User created and encrypted successfully\"
  }"
}
```

**Copy the user_id from the response** - you'll need it for the next test.

#### Test 3: Update Get User Test Event
1. Select **get-user-test** event
2. Click **Actions** → **Edit**
3. Replace `REPLACE-WITH-ACTUAL-USER-ID` with the user_id from step 6.2
4. Click **Save changes**

#### Test 4: Get User (Decryption Test)
1. Select **get-user-test** event
2. Click **Test**

**Expected Success Response:**
```json
{
  "statusCode": 200,
  "body": "{
    \"user_id\": \"550e8400-e29b-41d4-a716-446655440000\",
    \"data\": {
      \"email\": \"john.doe@example.com\",
      \"first_name\": \"John\",
      \"last_name\": \"Doe\",
      \"phone\": \"+1-555-0123\",
      \"address\": \"123 Main Street, Anytown, USA\",
      \"date_of_birth\": \"1990-01-01\",
      \"ssn\": \"123-45-6789\",
      \"bank_account\": \"1234567890\"
    },
    \"success\": true,
    \"processed_fields\": 6
  }"
}
```

**Verify Encryption Levels:**
- All fields should be returned in plaintext (Lambda decrypted them)
- Data should match exactly what was submitted in create-user-test

#### Test 5: List Users
1. Select **list-users** event
2. Click **Test**

**Expected Success Response:**
```json
{
  "statusCode": 200,
  "body": "{
    \"users\": [
      {
        \"id\": \"550e8400-e29b-41d4-a716-446655440000\",
        \"email\": \"john.doe@example.com\",
        \"first_name\": \"John\",
        \"last_name\": \"Doe\",
        \"created_at\": \"2025-07-21T...\",
        \"updated_at\": \"2025-07-21T...\"
      }
    ],
    \"pagination\": {
      \"total\": 1,
      \"limit\": 10,
      \"offset\": 0,
      \"has_more\": false
    },
    \"success\": true
  }"
}
```

#### Test 6: Audit Trail
1. Select **audit-trail** event  
2. Click **Test**

**Expected Success Response:**
```json
{
  "statusCode": 200,
  "body": "{
    \"audit_records\": [
      {
        \"id\": \"...\",
        \"user_id\": \"550e8400-e29b-41d4-a716-446655440000\",
        \"field_name\": \"ssn\",
        \"pii_level\": 3,
        \"operation\": \"decrypt\",
        \"accessed_by\": \"lambda-encryption-service\",
        \"success\": true,
        \"accessed_at\": \"2025-07-21T...\"
      },
      ...
    ],
    \"total\": 16,
    \"success\": true
  }"
}
```

### 6.3 Monitor Function Performance and Logs

#### View CloudWatch Logs
1. Go to **Monitor** tab
2. Click **View CloudWatch logs**
3. Click on the latest log stream
4. **Review logs for:**
   - No error messages
   - Successful AWS API calls
   - Database connection success
   - Encryption/decryption operations

#### Check Function Metrics
1. In **Monitor** tab, review:
   - **Duration**: Should be < 30 seconds for all operations
   - **Memory usage**: Should be under allocated memory
   - **Error rate**: Should be 0%
   - **Throttles**: Should be 0

#### Expected Log Entries (Sample)
```
[INFO] Lambda invoked with event: {"operation": "health"}
[INFO] Successfully retrieved application encryption keys
[INFO] Successfully connected to database
[INFO] Database schema validation: {'overall': True, ...}
```

### 6.4 Database Verification

#### Connect to Your RDS Database
Using your preferred PostgreSQL client:

```sql
-- Check that user was created
SELECT id, email, first_name, last_name, created_at 
FROM users 
ORDER BY created_at DESC 
LIMIT 5;

-- Verify encryption levels in database
SELECT 
    id,
    email,                    -- Level 1: plaintext
    first_name,              -- Level 1: plaintext
    address_encrypted,       -- Level 2: encrypted blob
    ssn_encrypted           -- Level 3: double encrypted blob
FROM users 
WHERE email = 'john.doe@example.com';

-- Check encryption metadata
SELECT 
    field_name, 
    pii_level, 
    app_key_version, 
    kms_key_alias,
    encrypted_at
FROM encryption_metadata 
WHERE user_id = 'YOUR-USER-ID';

-- Check audit trail
SELECT 
    field_name,
    pii_level,
    operation,
    accessed_by,
    success,
    accessed_at
FROM encryption_audit 
WHERE user_id = 'YOUR-USER-ID'
ORDER BY accessed_at DESC;
```

#### Verify Encryption is Working
- **Level 1 fields** (email, first_name): Should be plaintext in database
- **Level 2 fields** (address): Should be encrypted blobs in `*_encrypted` columns
- **Level 3 fields** (ssn): Should be double-encrypted blobs in `*_encrypted` columns
- **Metadata table**: Should have entries for Level 2 and 3 fields
- **Audit table**: Should have entries for all encrypt/decrypt operations

---

## Step 7: Configure Function Monitoring and Optimization

### 7.1 Configure CloudWatch Alarms

#### Create Error Rate Alarm
1. Go to **Configuration** → **Monitoring and operations tools**  
2. Click **Create alarm**
3. **Alarm name**: `pii-lambda-error-rate`
4. **Metric**: Error rate
5. **Threshold**: Greater than 5%
6. **Evaluation periods**: 2 consecutive periods
7. **Period**: 5 minutes
8. Click **Create alarm**

#### Create Duration Alarm  
1. Click **Create alarm**
2. **Alarm name**: `pii-lambda-duration`
3. **Metric**: Duration
4. **Threshold**: Greater than 25,000 ms (25 seconds)
5. **Evaluation periods**: 3 consecutive periods
6. **Period**: 5 minutes
7. Click **Create alarm**

#### Create Throttle Alarm
1. Click **Create alarm**
2. **Alarm name**: `pii-lambda-throttles`
3. **Metric**: Throttles
4. **Threshold**: Greater than 0
5. **Evaluation periods**: 1 period
6. **Period**: 1 minute
7. Click **Create alarm**

### 7.2 Configure Concurrency Settings

#### Set Reserved Concurrency (Optional)
1. Go to **Configuration** → **Concurrency**
2. Click **Edit**
3. **Reserved concurrency**: 10 (prevents runaway costs in prototype)
4. **Provisioned concurrency**: 1 (optional - reduces cold starts)
5. Click **Save**

### 7.3 Enable Enhanced Monitoring

#### X-Ray Tracing
1. Go to **Configuration** → **Monitoring and operations tools**
2. **AWS X-Ray**: Active tracing enabled
3. **Sampling rate**: 0.1 (10% of requests)
4. Click **Save**

#### Application Insights
1. **Application insights**: Enable
2. **Log level**: INFO
3. **Application log level**: WARN
4. Click **Save**

---

## Step 8: Comprehensive Troubleshooting Guide

### 8.1 Common Deployment Issues

#### Issue 1: "Unable to import module 'lambda_function'"
**Symptoms:**
- Import error in Lambda logs
- Function fails immediately

**Causes & Solutions:**
1. **Incorrect handler path**
   - **Fix**: Verify handler is `lambda_function.lambda_handler`
   - **Check**: Configuration → General configuration → Handler

2. **Missing main handler file**
   - **Fix**: Ensure `lambda_function.py` exists at zip root level
   - **Check**: Re-create deployment package

3. **Python version mismatch**
   - **Fix**: Ensure package created with Python 3.10/3.11
   - **Check**: Runtime setting in function configuration

#### Issue 2: "Task timed out after X seconds"
**Symptoms:**
- Function execution stops abruptly
- No response returned

**Causes & Solutions:**
1. **Timeout too low**
   - **Fix**: Increase to 300 seconds (5 minutes)
   - **Location**: Configuration → General configuration → Timeout

2. **Cold start delays**
   - **Fix**: Enable provisioned concurrency
   - **Location**: Configuration → Concurrency

3. **Database connection hangs**
   - **Fix**: Check VPC/security group configuration
   - **Debug**: Review CloudWatch logs for connection attempts

#### Issue 3: VPC/Network Issues
**Symptoms:**
- "Unable to connect to database"
- "DNS resolution failed"
- Timeout errors

**Diagnosis Steps:**
1. **Check VPC Configuration**
   ```
   Lambda → Configuration → VPC
   - Verify correct VPC selected
   - Ensure 2+ private subnets in different AZs
   - Confirm security group attached
   ```

2. **Verify Security Groups**
   ```
   VPC Console → Security Groups
   Lambda SG Outbound Rules:
   - HTTPS (443) to 0.0.0.0/0 ✓
   - PostgreSQL (5432) to RDS SG ✓
   - DNS (53) to 0.0.0.0/0 ✓
   
   RDS SG Inbound Rules:
   - PostgreSQL (5432) from Lambda SG ✓
   ```

3. **Check Route Tables**
   ```
   VPC Console → Route Tables
   Private Subnet Routes:
   - 10.0.0.0/16 → local ✓
   - 0.0.0.0/0 → NAT Gateway ✓ (NOT Internet Gateway)
   ```

### 8.2 AWS Service Integration Issues

#### Issue 4: KMS Access Denied
**Symptoms:**
- "AccessDenied" errors in logs
- "User is not authorized to perform kms:Encrypt"

**Solutions:**
1. **Check KMS Key Policies**
   ```
   KMS Console → Customer managed keys
   - Select pii-level2 key
   - Key policy should allow Lambda execution role
   ```

2. **Verify IAM Permissions**
   ```
   IAM Console → Roles → PIIEncryptionLambdaExecutionRole
   - Check PIIEncryptionLambdaCustomPolicy attached
   - Verify KMS permissions in policy
   ```

3. **Test KMS Access**
   ```
   AWS CLI:
   aws kms describe-key --key-id alias/pii-level2
   aws kms describe-key --key-id alias/pii-level3
   ```

#### Issue 5: Secrets Manager Access Denied
**Symptoms:**
- "AccessDenied" when retrieving secrets
- "Secret not found" errors

**Solutions:**
1. **Verify Secret Names**
   ```
   Secrets Manager Console:
   - pii-encryption-keys ✓
   - pii-database-credentials ✓
   ```

2. **Check Secret ARNs in IAM Policy**
   ```
   Policy should include:
   arn:aws:secretsmanager:*:*:secret:pii-encryption-keys-*
   arn:aws:secretsmanager:*:*:secret:pii-database-credentials-*
   ```

3. **Test Secret Access**
   ```
   AWS CLI:
   aws secretsmanager get-secret-value --secret-id pii-encryption-keys
   ```

#### Issue 6: Database Connection Issues
**Symptoms:**
- "Connection refused"
- "Host unreachable"
- "Authentication failed"

**Diagnosis & Solutions:**
1. **Test Network Connectivity**
   ```
   Create test Lambda with:
   import socket
   import psycopg2
   
   # Test port connectivity
   sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   result = sock.connect_ex(('your-rds-endpoint', 5432))
   print(f"Port 5432 connection result: {result}")  # 0 = success
   ```

2. **Verify Database Credentials**
   ```
   Check Secrets Manager secret content:
   {
     "host": "pii-cluster.cluster-xyz.us-east-1.rds.amazonaws.com",
     "port": 5432,
     "database": "pii_db",
     "username": "postgres",
     "password": "your-password"
   }
   ```

3. **Check RDS Status**
   ```
   RDS Console → Databases
   - Status: Available ✓
   - VPC: Same as Lambda ✓
   - Security group: Allows Lambda access ✓
   ```

### 8.3 Performance Issues

#### Issue 7: High Memory Usage
**Symptoms:**
- Function runs out of memory
- Slow performance

**Solutions:**
1. **Increase Memory Allocation**
   - **Current**: 512 MB
   - **Recommended**: 1024 MB for heavy encryption
   - **Location**: Configuration → General configuration

2. **Monitor Memory Usage**
   ```
   CloudWatch Metrics:
   - AWS/Lambda → MemoryUtilization
   - Aim for < 80% average usage
   ```

#### Issue 8: Cold Start Performance
**Symptoms:**
- First invocation takes 30+ seconds
- Intermittent slow responses

**Solutions:**
1. **Enable Provisioned Concurrency**
   ```
   Configuration → Concurrency
   - Provisioned concurrency: 1-2 instances
   ```

2. **Optimize Dependencies**
   ```
   Only include necessary packages in deployment
   Consider layers for common dependencies
   ```

### 8.4 Data and Encryption Issues

#### Issue 9: Encryption/Decryption Failures
**Symptoms:**
- "Decryption failed" errors
- Corrupted data returned

**Solutions:**
1. **Check Key Versions**
   ```
   Verify encryption_metadata table:
   - app_key_version matches current version
   - kms_key_alias is correct
   ```

2. **Test Encryption Roundtrip**
   ```
   Create test with simple data:
   {"operation": "create_user", "data": {"email": "test@example.com"}}
   ```

#### Issue 10: Database Schema Issues
**Symptoms:**
- "Column does not exist" errors
- "Table not found" errors

**Solutions:**
1. **Verify Schema Creation**
   ```sql
   -- Check if tables exist
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public';
   
   -- Should return: users, encryption_metadata, encryption_audit
   ```

2. **Re-run Schema Creation**
   ```
   Re-execute Phase 1 database schema from:
   /database/schema.sql
   ```

---

## Step 9: Security Validation Checklist

### 9.1 Pre-Production Security Review

#### IAM Security ✓
- [ ] **Least Privilege**: Role only has necessary permissions
- [ ] **No Wildcards**: Specific resource ARNs where possible
- [ ] **Time-bound**: No permanent access keys
- [ ] **Audit Trail**: CloudTrail enabled for IAM changes

#### Network Security ✓
- [ ] **Private Subnets**: Lambda deployed in private subnets only
- [ ] **Security Groups**: Minimal required ports open
- [ ] **No Public Access**: Database not publicly accessible
- [ ] **Encryption in Transit**: All connections use TLS

#### Data Security ✓
- [ ] **No Hardcoded Secrets**: All secrets in Secrets Manager
- [ ] **Log Sanitization**: No PII in CloudWatch logs
- [ ] **Encryption at Rest**: All data encrypted when stored
- [ ] **Key Rotation**: Automatic rotation enabled

#### Access Control ✓
- [ ] **Service-to-Service**: No human access to encryption functions
- [ ] **Audit Logging**: All operations logged
- [ ] **Error Handling**: No sensitive data in error messages
- [ ] **Monitoring**: Alerts configured for suspicious activity

### 9.2 Compliance Validation

#### GDPR Compliance ✓
- [ ] **Data Minimization**: Only necessary PII collected
- [ ] **Encryption**: Strong encryption for all sensitive data
- [ ] **Right to Deletion**: Crypto-shredding capability implemented
- [ ] **Audit Trail**: Complete record of data processing

#### Security Standards ✓
- [ ] **SOC 2**: Controls for security and availability
- [ ] **ISO 27001**: Information security management
- [ ] **NIST**: Cybersecurity framework compliance

---

## Step 10: Performance Optimization and Monitoring

### 10.1 Performance Tuning

#### Memory Optimization
**Initial Settings:**
- Memory: 512 MB
- Timeout: 300 seconds

**Monitor and Adjust:**
```
CloudWatch Metrics to Watch:
- Duration: Aim for < 30 seconds
- Memory Utilization: Keep < 80%
- Error Rate: Target 0%
- Throttles: Should be 0
```

#### Connection Management
**Database Connections:**
- Connection pooling implemented in code
- Reuse connections across invocations
- Close connections properly

**AWS Service Clients:**
- Boto3 clients cached
- Secrets cached with TTL
- KMS operations batched when possible

### 10.2 Cost Monitoring

#### Lambda Costs
```
Expected Monthly Costs (Prototype):
- Requests: 1M/month × $0.20/1M = $0.20
- Duration: 30s avg × 1M × $0.0000166667 = $5.00
- Total Lambda: ~$5.20/month
```

#### Associated Costs
```
- KMS API calls: ~$1/month
- Secrets Manager: $0.80/month
- CloudWatch Logs: ~$0.50/month
- Total Infrastructure: ~$2.30/month
```

---

## Conclusion and Next Steps

### ✅ Lambda Function Deployment Complete

You have successfully deployed the PII Encryption Lambda function with:

1. **✅ Security**: Comprehensive IAM roles, VPC isolation, encryption
2. **✅ Functionality**: Three-tier PII encryption system
3. **✅ Integration**: KMS, Secrets Manager, RDS connectivity
4. **✅ Monitoring**: CloudWatch alarms and X-Ray tracing
5. **✅ Testing**: Complete test suite with all operations validated

### 🚀 Ready for Phase 4

The Lambda function is now ready to serve as the encryption backend for:
- **FastAPI Backend** (Phase 4)
- **API Gateway** (Phase 5)  
- **React Frontend** (Phase 6)

### 📝 Documentation

Save the following for Phase 4 development:
- **Lambda ARN**: `arn:aws:lambda:region:account:function:pii-encryption-handler`
- **Function Name**: `pii-encryption-handler`
- **Test Events**: Created and validated
- **Performance Metrics**: Baseline established

### 🔄 Next Actions

1. **Proceed to Phase 4**: FastAPI Backend implementation
2. **Monitor Performance**: Review CloudWatch metrics weekly
3. **Security Review**: Schedule periodic security audits
4. **Cost Optimization**: Monitor and adjust resources as needed

The PII encryption service is now production-ready and secure! 🔒