# PII Backend Deployment Overview

This document provides a complete overview of deploying the FastAPI backend to AWS for the PII Encryption System prototype.

## Deployment Options

### Option 1: Quick Manual Deployment (Recommended for Prototype)

Perfect for testing and prototyping:

1. **Build and Push Container**:
   ```bash
   cd backend/deploy
   ./quick-deploy.sh us-east-1 pii-backend latest
   ```

2. **Manual App Runner Setup**: Follow [console-deployment-guide.md](console-deployment-guide.md)
   - Uses AWS Console for IAM roles and App Runner service
   - Visual feedback, good for learning
   - Takes 20-30 minutes first time

3. **Test Deployment**: Use [TESTING-GUIDE.md](TESTING-GUIDE.md)

### Option 2: Terraform Automation (Production Ready)

For repeatable infrastructure:

1. **Build and Push Container**:
   ```bash
   ./push-to-ecr.sh us-east-1 pii-backend latest
   ```

2. **Configure Terraform**:
   ```bash
   cp terraform/terraform.tfvars.example terraform/terraform.tfvars
   # Edit with your settings
   ```

3. **Deploy with Terraform**:
   ```bash
   ./deploy.sh apply
   ```

## Architecture Overview

```
Internet → HTTPS → App Runner → Lambda → RDS Aurora
                      ↓           ↓         ↑
                  IAM Roles   KMS Keys  Database
                      ↓           ↓         ↑
                  ECR Image   Secrets   Encryption
```

### Components Created

| Component | Purpose | Configuration |
|-----------|---------|---------------|
| **ECR Repository** | Container storage | Private, scan on push |
| **App Runner Service** | Container hosting | 0.25 vCPU, 0.5GB RAM |
| **IAM Roles** | Security permissions | Least privilege access |
| **Auto Scaling** | Traffic handling | 1-10 instances, 100 req/instance |
| **Health Checks** | Service monitoring | `/health` endpoint |

## Environment Configuration

### Required Environment Variables

```bash
# Application
PII_ENVIRONMENT=production
PII_DEBUG=false
PII_API_KEY=your-secure-api-key

# AWS
AWS_REGION=us-east-1
PII_LAMBDA_FUNCTION_NAME=pii-encryption-handler

# Security
PII_ALLOWED_ORIGINS=["https://your-frontend.com"]
```

### Security Configuration

- **No hardcoded credentials** ✅
- **IAM roles for all access** ✅  
- **HTTPS only** ✅
- **API key authentication** ✅
- **Private container registry** ✅

## Cost Breakdown

### Monthly Costs (Prototype Usage)

| Service | Cost | Notes |
|---------|------|-------|
| App Runner | $5-15 | Scales to zero |
| ECR Storage | $1 | 1GB container images |
| Data Transfer | $1-5 | API requests |
| CloudWatch Logs | $0.50 | Application logs |
| **Total** | **$7-21** | Light development usage |

### Cost Optimization Tips

- Set **min instances to 0** for development
- Use **smallest instance size** (0.25 vCPU)
- **Delete when not testing** to avoid charges
- Monitor usage in AWS Cost Explorer

## Deployment Checklist

### Prerequisites
- [x] AWS CLI configured (`aws configure`)
- [x] Docker installed and running
- [x] PII Lambda function deployed (Phase 3)
- [x] Database setup completed (Phase 1)
- [x] Appropriate AWS permissions

### Deployment Steps
1. [x] **Build container**: `./quick-deploy.sh`
2. [x] **Create IAM roles**: Follow manual guide
3. [x] **Deploy App Runner**: Use AWS Console
4. [x] **Configure environment**: Set all required variables
5. [x] **Test endpoints**: Use testing guide

### Verification Steps
- [x] Health check returns 200 OK
- [x] Authentication works with API key
- [x] User CRUD operations functional
- [x] Lambda integration successful
- [x] Audit trail recording events
- [x] No errors in CloudWatch logs

## Common Issues and Solutions

### 1. "Lambda invocation failed"
**Symptoms**: API returns 500 errors, logs show Lambda failures
**Solutions**:
- Verify Lambda function name matches `PII_LAMBDA_FUNCTION_NAME`
- Check IAM role has `lambda:InvokeFunction` permission
- Ensure Lambda and App Runner in same region

### 2. "Container failed to start"
**Symptoms**: App Runner service fails to deploy
**Solutions**:
- Check ECR image was pushed successfully
- Verify IAM role can access ECR
- Review environment variables for typos

### 3. "Authentication failed"
**Symptoms**: 401/403 errors on API requests
**Solutions**:
- Verify API key matches environment variable
- Check `Authorization: Bearer your-key` header format
- Ensure API key is URL-safe (no special characters)

### 4. "Health check failing"
**Symptoms**: App Runner shows unhealthy status
**Solutions**:
- Check `/health` endpoint accessible
- Review application startup logs
- Verify Lambda connectivity from health check

### 5. "High response times"
**Symptoms**: API requests take >5 seconds
**Solutions**:
- Lambda cold start issue (normal for prototype)
- Increase App Runner instance count
- Consider Lambda provisioned concurrency (costs more)

## Monitoring and Debugging

### CloudWatch Logs
- **Application logs**: `/aws/apprunner/pii-backend-dev/application`
- **Service logs**: `/aws/apprunner/pii-backend-dev/service`

### Useful AWS CLI Commands
```bash
# View recent logs
aws logs tail /aws/apprunner/pii-backend-dev/application --follow

# Check service status
aws apprunner describe-service --service-arn <service-arn>

# View deployment history
aws apprunner list-operations --service-arn <service-arn>
```

### Debugging Steps
1. Check App Runner service status
2. Review application logs for errors
3. Test Lambda function separately
4. Verify database connectivity
5. Check IAM permissions

## Security Best Practices

### ✅ Implemented
- Container runs as non-root user
- No secrets in container image
- IAM roles with least privilege
- HTTPS termination at App Runner
- API key authentication
- Input validation with Pydantic
- Comprehensive audit logging

### 🔄 Recommended Additions
- **WAF**: Add Web Application Firewall for production
- **Rate limiting**: Implement request throttling
- **Monitoring**: Set up CloudWatch alarms
- **Backup**: Configure automated database backups
- **Secrets rotation**: Implement key rotation

## Next Steps

After successful deployment:

1. **Document your App Runner URL** for frontend integration
2. **Set up custom domain** (optional) for production
3. **Configure monitoring alerts** for service health
4. **Plan frontend deployment** (Phase 6)
5. **Consider CI/CD pipeline** for automated deployments

## Support Resources

- **AWS App Runner Documentation**: https://docs.aws.amazon.com/apprunner/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/
- **AWS ECR Documentation**: https://docs.aws.amazon.com/ecr/

## Quick Reference

### Essential URLs (replace with your values)
- **ECR Console**: https://console.aws.amazon.com/ecr/repositories
- **App Runner Console**: https://console.aws.amazon.com/apprunner/home
- **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups
- **Your API**: https://your-unique-id.us-east-1.awsapprunner.com

### Key Files
- **Manual Guide**: `console-deployment-guide.md` - Step-by-step AWS Console setup
- **Testing Guide**: `TESTING-GUIDE.md` - Comprehensive API testing
- **Terraform**: `terraform/` - Infrastructure as code
- **Scripts**: `*.sh` - Deployment automation