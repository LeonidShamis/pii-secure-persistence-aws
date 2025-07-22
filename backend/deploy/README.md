# AWS App Runner Deployment Guide

This guide explains how to deploy the PII Backend FastAPI application to AWS App Runner, a fully managed containerized web service.

## Why App Runner?

App Runner is perfect for this prototype because it provides:
- **Fully managed service** - No servers to manage
- **Automatic scaling** - Scales from 0 to handle traffic spikes
- **Built-in load balancing** - No need for separate ALB
- **Cost-effective** - Pay only for running time, scales to zero
- **HTTPS by default** - Automatic SSL certificates
- **Simple deployment** - Container or source-based deployment

## Prerequisites

Before deploying, ensure you have:

1. **AWS CLI configured** with appropriate permissions
   ```bash
   aws configure  # Creates ~/.aws/credentials (never hardcode keys!)
   aws sts get-caller-identity  # Verify credentials
   ```

2. **Docker installed** for building and pushing images
   ```bash
   docker --version
   ```

3. **Terraform installed** (>= 1.0)
   ```bash
   terraform version
   ```

4. **PII Lambda function deployed** from the previous phase
   - Function name should match `lambda_function_name` in configuration

## Deployment Steps

### Step 1: Configure Deployment Settings

Copy and configure the Terraform variables:

```bash
cd deploy/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your settings:

```hcl
# AWS Configuration
aws_region = "us-east-1"
environment = "dev"

# API Configuration  
api_key = "your-super-secure-api-key-here"  # Generate a strong random key

# Container Configuration
container_image_uri = "123456789012.dkr.ecr.us-east-1.amazonaws.com/pii-backend:latest"

# Lambda Integration
lambda_function_name = "pii-encryption-handler"  # Your Lambda function name

# CORS Configuration
allowed_origins = [
  "https://your-frontend-domain.com",
  "https://localhost:3000"  # For local development
]
```

### Step 2: Build and Push Docker Image to ECR

Use the provided script to build and push your Docker image:

```bash
# From the backend root directory
cd deploy

# Push to ECR (creates repository if needed)
./push-to-ecr.sh us-east-1 pii-backend latest
```

This script will:
1. Create ECR repository if it doesn't exist
2. Build the Docker image
3. Authenticate with ECR
4. Push the image to ECR
5. Output the image URI for your terraform.tfvars

Copy the output image URI to your `terraform.tfvars` file.

### Step 3: Deploy with Terraform

Deploy the App Runner service:

```bash
# Plan the deployment (preview changes)
./deploy.sh plan

# Apply the deployment
./deploy.sh apply
```

The deployment creates:
- **App Runner service** with auto-scaling
- **IAM roles and policies** for Lambda access
- **Security configuration** with proper permissions
- **Health check configuration** using `/health` endpoint

### Step 4: Verify Deployment

After deployment, Terraform will output the App Runner service URL:

```bash
# Get the service URL
terraform output app_runner_service_url
```

Test the deployment:

```bash
# Health check
curl https://your-service-url.us-east-1.awsapprunner.com/health

# API root endpoint  
curl https://your-service-url.us-east-1.awsapprunner.com/
```

## Configuration Options

### Auto Scaling

The default configuration is optimized for prototypes:
- **Min instances**: 1 (set to 0 to reduce costs)
- **Max instances**: 10
- **Max concurrency**: 100 requests per instance

Adjust in `app-runner.tf`:
```hcl
resource "aws_apprunner_auto_scaling_configuration_version" "pii_backend" {
  max_concurrency = 100
  max_size        = 10
  min_size        = 0    # Set to 0 for cost savings
}
```

### Instance Configuration

Default resources:
- **CPU**: 0.25 vCPU (can be 0.25, 0.5, 1, 2)
- **Memory**: 0.5 GB (can be 0.5, 1, 2, 3, 4)

Adjust based on your load requirements:
```hcl
instance_configuration {
  cpu    = "0.5 vCPU"
  memory = "1 GB"
}
```

### Environment Variables

Environment variables are configured in the Terraform file and injected at runtime:
- `PII_ENVIRONMENT`: Application environment (production)
- `PII_API_KEY`: Authentication key
- `AWS_REGION`: AWS region for Lambda calls
- `PII_LAMBDA_FUNCTION_NAME`: Lambda function name
- And more...

## Custom Domain (Optional)

To use a custom domain, uncomment and configure:

```hcl
resource "aws_apprunner_custom_domain_association" "pii_backend" {
  domain_name = "api.your-domain.com"
  service_arn = aws_apprunner_service.pii_backend.arn
}
```

You'll also need to:
1. Own the domain
2. Create DNS records as instructed by App Runner
3. Validate domain ownership

## Monitoring and Logs

App Runner automatically creates CloudWatch logs:
- **Application logs**: `/aws/apprunner/pii-backend-dev/application`
- **Service logs**: `/aws/apprunner/pii-backend-dev/service`

Access logs in AWS Console:
1. Go to CloudWatch → Log groups
2. Find your App Runner log groups
3. View real-time logs and errors

## Cost Optimization

To minimize costs for prototypes:

1. **Set min_size to 0** in auto-scaling configuration
2. **Use smallest instance size** (0.25 vCPU, 0.5 GB)
3. **Monitor usage** in AWS Cost Explorer
4. **Destroy when not needed**: `./deploy.sh destroy`

Estimated costs for light usage:
- **App Runner**: ~$5-20/month depending on usage
- **Data transfer**: ~$1-5/month
- **Lambda invocations**: Covered by free tier initially

## Troubleshooting

### Common Issues

**Image pull errors**:
- Verify ECR permissions and image URI
- Check that image exists in ECR
- Ensure App Runner access role has ECR permissions

**Lambda invocation failures**:
- Verify Lambda function name matches configuration
- Check IAM policies for Lambda invoke permissions
- Ensure Lambda function exists in the same region

**Health check failures**:
- Verify `/health` endpoint responds correctly
- Check application logs for startup errors
- Ensure correct port configuration (8000)

### Debugging

View real-time logs:
```bash
# Get service logs
aws logs tail /aws/apprunner/pii-backend-dev/application --follow

# Get deployment events  
aws apprunner describe-service --service-arn $(terraform output -raw app_runner_service_arn)
```

## Updating the Application

To update the deployed application:

1. **Build new image**:
   ```bash
   ./push-to-ecr.sh us-east-1 pii-backend v2
   ```

2. **Update terraform.tfvars** with new image URI

3. **Apply changes**:
   ```bash
   ./deploy.sh apply
   ```

App Runner will automatically deploy the new version with zero downtime.

## Cleanup

To completely remove the infrastructure:

```bash
./deploy.sh destroy
```

This will delete:
- App Runner service
- Auto-scaling configuration
- IAM roles and policies
- CloudWatch log groups (retention policy dependent)

## Security Considerations

### AWS Credentials (NEVER HARDCODE!)

✅ **Correct approaches:**
- **Local development**: `aws configure` creates `~/.aws/credentials`
- **App Runner**: IAM roles (automatic, no credentials needed)
- **Docker**: Volume mount `~/.aws` directory

❌ **NEVER do this:**
```bash
# DON'T hardcode credentials in environment files
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### Other Security Best Practices

- **API keys**: Use strong, randomly generated API keys
- **IAM policies**: Follow least privilege principle
- **HTTPS**: App Runner provides HTTPS by default
- **Environment variables**: Sensitive data is encrypted at rest
- **VPC**: App Runner runs in AWS-managed VPC by default
- **Lambda permissions**: Scoped to specific Lambda function

### AWS Credential Chain

The AWS SDK automatically finds credentials in this order:
1. Environment variables (if set)
2. `~/.aws/credentials` file (recommended for local dev)
3. `~/.aws/config` file
4. IAM instance profile (for EC2)
5. **IAM roles for App Runner** (production recommended)

The deployment follows AWS security best practices for containerized web applications.