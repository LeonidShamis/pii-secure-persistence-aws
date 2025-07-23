# Console Deployment Guide - FastAPI Backend

Complete AWS Console-only deployment guide for the PII Backend to AWS App Runner. No CLI commands required!

## Overview

This guide walks you through deploying the FastAPI backend using **only** the AWS Console web interface. Perfect for prototypes, learning, and when you prefer visual interfaces.

**What we'll create:**
- ECR repository for Docker images
- IAM roles for App Runner permissions
- App Runner service for hosting the API
- CloudWatch logs for monitoring

**Time required:** 30-45 minutes

## Prerequisites

- AWS Account with console access
- Docker installed locally (for building the image)
- PII Lambda function deployed (from Phase 3)
- Database setup completed (from Phase 1)

## Step 1: Prepare Docker Image Locally

### 1.1 Build Docker Image

Open terminal in your backend directory and run:

```bash
# Navigate to backend directory
cd /root/dev/ballers/pii-secure-persistence-aws/backend

# Build the Docker image
docker build -t pii-backend:latest .
```

**Expected output:** Successfully built image with final message showing image ID.

### 1.2 Save Docker Image to File

```bash
# Save the image to a tar file for upload
docker save pii-backend:latest -o pii-backend.tar
```

This creates `pii-backend.tar` file (~200-300MB) that we'll upload via console.

## Step 2: Create ECR Repository via Console

### 2.1 Navigate to Amazon ECR

1. **Open AWS Console** → Sign in to your account
2. **Search** for "ECR" in the top search bar
3. **Click** "Elastic Container Registry"
4. **Select** your region (e.g., US East 1) in top-right dropdown

### 2.2 Create Repository

1. **Click** "Create repository" button
2. **Repository settings:**
   - **Visibility**: Private
   - **Repository name**: `pii-backend`
   - **Tag immutability**: Disabled
   - **Scan on push**: Enabled
   - **Encryption**: AES-256 (default)
3. **Click** "Create repository"

**Result:** Repository created with URI like `123456789012.dkr.ecr.us-east-1.amazonaws.com/pii-backend`

### 2.3 Upload Image Using Console

1. **Click** on your `pii-backend` repository
2. **Click** "View push commands" button
3. **Copy** the "Retrieve authentication token" command and run it locally:

```bash
# This command is specific to your account - copy from console
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

4. **Tag and push** using commands from console:

```bash
# Tag image (copy exact command from console)
docker tag pii-backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/pii-backend:latest

# Push image (copy exact command from console)  
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/pii-backend:latest
```

**Alternative: Console Upload (if CLI not available)**

If you cannot use CLI commands, AWS provides a console-based upload for smaller images:

1. **Go to** ECR Console → Your repository
2. **Click** "Upload image" (if available in your region)
3. **Select** the `pii-backend.tar` file
4. **Upload** (this may take 10-15 minutes for large images)

## Step 3: Create IAM Roles via Console

### 3.1 Create App Runner Access Role (ECR Access)

1. **Navigate to IAM Console:**
   - **Search** "IAM" in AWS Console
   - **Click** "Identity and Access Management"
   
2. **Create Role:**
   - **Click** "Roles" in left sidebar
   - **Click** "Create role"
   
3. **Select Trusted Entity:**
   - **Trusted entity type**: AWS service
   - **Use case**: Search for "App Runner"
   - **Select** "App Runner" from the list
   - **Click** "Next"
   
4. **Add Permissions:**
   - **Search** for "AWSAppRunnerServicePolicyForECRAccess"
   - **Check** the box next to this policy
   - **Click** "Next"
   
5. **Role Details:**
   - **Role name**: `pii-backend-apprunner-access-role`
   - **Description**: "Allows App Runner to access ECR repository"
   - **Click** "Create role"

### 3.2 Create App Runner Task Role (Lambda Access)

1. **Create another role** following same steps but:
   
2. **Select Trusted Entity:**
   - **Trusted entity type**: AWS service
   - **Use case**: Search for "App Runner"
   - **Select** "App Runner - Tasks" (different from above)
   - **Click** "Next"
   
3. **Skip Adding Policies** (we'll add custom policy)
   - **Click** "Next" without selecting any policies
   
4. **Role Details:**
   - **Role name**: `pii-backend-apprunner-task-role`
   - **Description**: "Allows App Runner tasks to invoke Lambda functions"
   - **Click** "Create role"

### 3.3 Add Custom Lambda Policy to Task Role

1. **Click** on `pii-backend-apprunner-task-role` from the roles list
2. **Click** "Add permissions" dropdown → "Create inline policy"
3. **Click** "JSON" tab
4. **Replace** the JSON with this policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": "arn:aws:lambda:us-east-1:*:function:pii-encryption-handler"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

**Important:** Replace `us-east-1` with your region and ensure `pii-encryption-handler` matches your Lambda function name.

5. **Click** "Next"
6. **Policy name**: `LambdaInvokePolicy`
7. **Click** "Create policy"

## Step 4: Create App Runner Service via Console

### 4.1 Navigate to App Runner

1. **Search** "App Runner" in AWS Console
2. **Click** "AWS App Runner"
3. **Make sure** you're in the correct region (same as ECR)

### 4.2 Create Service

1. **Click** "Create service"
2. **Source and deployment:**
   - **Repository type**: Container registry
   - **Provider**: Amazon ECR
   - **Container image URI**: `123456789012.dkr.ecr.us-east-1.amazonaws.com/pii-backend:latest`
   - **Deployment settings**: Manual deployment
   - **ECR access role**: Select `pii-backend-apprunner-access-role`
3. **Click** "Next"

### 4.3 Configure Service Settings

1. **Service name**: `pii-backend-dev`
2. **Virtual CPU and memory**:
   - **CPU**: 0.25 vCPU
   - **Memory**: 0.5 GB
3. **Port**: 8000 (FastAPI default)
4. **Environment variables** - Click "Add environment variable" for each:

| Name | Value |
|------|-------|
| `PII_ENVIRONMENT` | `production` |
| `PII_DEBUG` | `false` |
| `PII_API_KEY` | `your-super-secure-api-key-change-me` |
| `PII_ALLOWED_ORIGINS` | `["*"]` |
| `AWS_REGION` | `us-east-1` |
| `PII_LAMBDA_FUNCTION_NAME` | `pii-encryption-handler` |
| `PII_LAMBDA_TIMEOUT` | `30` |
| `PII_LAMBDA_RETRY_ATTEMPTS` | `3` |
| `PII_LOG_LEVEL` | `INFO` |

**Important:** 
- Generate a strong API key! Example: `pii-api-2025-7d8f9e2a1b3c4567890`
- `["*"]` allows all CORS origins for prototype development
- For production, replace with specific domains: `["https://your-frontend-domain.com"]`

5. **Service role**: Select `pii-backend-apprunner-task-role`
6. **Click** "Next"

### 4.4 Configure Auto Scaling

1. **Auto scaling**:
   - **Auto scaling configuration name**: `pii-backend-autoscaling`
   - **Max concurrency**: 100 (requests per instance)
   - **Max instances**: 10
   - **Min instances**: 1 (set to 0 for cost savings)
2. **Click** "Next"

### 4.5 Configure Health Check

1. **Health check configuration**:
   - **Protocol**: HTTP
   - **Path**: `/health`
   - **Interval**: 10 seconds
   - **Timeout**: 5 seconds
   - **Healthy threshold**: 1
   - **Unhealthy threshold**: 5
2. **Click** "Next"

### 4.6 Review and Create

1. **Review** all settings carefully
2. **Verify**:
   - Container image URI is correct
   - Environment variables are set
   - IAM roles are selected
   - Health check path is `/health`
3. **Click** "Create & deploy"

## Step 5: Monitor Deployment

### 5.1 Wait for Deployment

The deployment process takes **5-10 minutes**:

1. **App Runner Console** shows status: "Operation in progress"
2. **Activity** tab shows deployment steps
3. **Logs** tab shows real-time deployment logs
4. **Configuration** tab shows all settings

### 5.2 Get Service URL

Once deployment completes:

1. **Status** changes to "Running"
2. **Service URL** appears in the console
3. **Format**: `https://random-id.us-east-1.awsapprunner.com`
4. **Copy** this URL for testing

## Step 6: Test via Console and Browser

### 6.1 Test Health Endpoint

1. **Open** new browser tab
2. **Navigate** to: `https://your-app-runner-url.awsapprunner.com/health`
3. **Expected result**: JSON response showing healthy status

```json
{
  "success": true,
  "status": "healthy",
  "components": {
    "backend": "healthy",
    "lambda": {
      "lambda": "healthy",
      "kms": "healthy",
      "secrets_manager": "healthy",
      "database": "healthy"
    }
  },
  "timestamp": "2025-07-23T01:06:00.125899",
  "error": null
}
```

### 6.2 Test Root Endpoint

1. **Navigate** to: `https://your-app-runner-url.awsapprunner.com/`
2. **Expected result**: API information

```json
{
  "success": true,
  "message": "PII Secure Persistence API",
  "data": {
    "version": "1.0.0",
    "status": "healthy",
    "documentation": "/docs"
  },
  "error": null
}
```

### 6.3 Test with Browser Extensions (Optional)

For testing authenticated endpoints, use browser extensions like:
- **Postman** (Chrome extension)
- **RESTClient** (Firefox extension)
- **Advanced REST Client** (Chrome)

**Test authenticated endpoint:**
- **URL**: `https://your-app-runner-url.awsapprunner.com/users`
- **Method**: GET
- **Header**: `Authorization: Bearer your-super-secure-api-key-change-me`

## Step 7: View Logs via Console

### 7.1 App Runner Logs

1. **App Runner Console** → Your service
2. **Click** "Logs" tab
3. **View** real-time application logs
4. **Look for** any errors or warnings

### 7.2 CloudWatch Logs

1. **Navigate** to CloudWatch Console
2. **Click** "Log groups" in left sidebar
3. **Find** log group: `/aws/apprunner/pii-backend-dev/application`
4. **Click** on log group to view detailed logs
5. **Use** filter patterns to search for specific messages

## Step 8: Testing with curl (Optional)

If you have curl available, test the API:

```bash
# Set your URL and API key
export APP_RUNNER_URL="https://your-unique-id.us-east-1.awsapprunner.com"
export API_KEY="your-super-secure-api-key-change-me"

# Test health endpoint
curl "$APP_RUNNER_URL/health"

# Test authenticated endpoint
curl -H "Authorization: Bearer $API_KEY" "$APP_RUNNER_URL/users"

# Create a test user
curl -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "first_name": "Test", "last_name": "User"}' \
  "$APP_RUNNER_URL/users"
```

## Troubleshooting via Console

### Common Issues

**1. Service fails to start**
- **Check**: App Runner → Logs tab for startup errors
- **Verify**: Environment variables are set correctly
- **Confirm**: IAM roles have correct permissions

**2. Health check failing**
- **Check**: `/health` endpoint works in browser
- **Verify**: Port 8000 is configured correctly
- **Review**: Application logs for connection errors

**3. Lambda invocation errors**
- **Verify**: Lambda function name matches environment variable
- **Check**: IAM task role has Lambda invoke permissions
- **Confirm**: Lambda function exists in same region

**4. Authentication errors**
- **Verify**: API key matches environment variable exactly
- **Check**: Authorization header format: `Bearer your-key`
- **Confirm**: No extra spaces or characters in API key

### Debugging Steps

1. **App Runner Console** → Service → Logs tab
2. **CloudWatch Console** → Log groups → Application logs
3. **Lambda Console** → Test your function independently
4. **IAM Console** → Verify role permissions
5. **ECR Console** → Confirm image was pushed successfully

## Success Checklist

✅ **Deployment successful when:**
- App Runner service shows "Running" status
- Health endpoint returns 200 OK
- Root endpoint returns API information
- Authenticated endpoints work with API key
- No errors in application logs
- CloudWatch logs show successful Lambda connections

## Cleanup (When Done Testing)

To avoid ongoing charges:

1. **App Runner Console** → Your service → Actions → "Delete service"
2. **ECR Console** → Your repository → Delete repository
3. **IAM Console** → Delete the two roles created
4. **CloudWatch** → Delete log groups (optional)

## Cost Estimation

**Monthly costs for this prototype:**
- **App Runner**: $5-15 (scales to zero when idle)
- **ECR Storage**: $1 (container images)
- **Data Transfer**: $1-5 (API requests)
- **CloudWatch Logs**: $0.50 (log storage)
- **Total**: ~$7-21/month for development use

## Next Steps

1. **Document your App Runner URL** - you'll need it for frontend integration
2. **Test all API endpoints** using the testing guide
3. **Set up monitoring alerts** for production use
4. **Plan frontend deployment** to connect to this API
5. **Consider custom domain** for production deployment

Congratulations! Your FastAPI backend is now deployed and running on AWS using only the console! 🎉