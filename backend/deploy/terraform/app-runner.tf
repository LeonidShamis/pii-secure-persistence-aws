# AWS App Runner service for PII Backend API
# This deploys the FastAPI backend as a fully managed container service

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "api_key" {
  description = "API key for authentication"
  type        = string
  sensitive   = true
}

variable "lambda_function_name" {
  description = "Name of the PII encryption Lambda function"
  type        = string
  default     = "pii-encryption-handler"
}

variable "container_image_uri" {
  description = "Container image URI (ECR or Docker Hub)"
  type        = string
  # Example: 123456789012.dkr.ecr.us-east-1.amazonaws.com/pii-backend:latest
}

variable "allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]  # Allow all origins for prototype
}

# IAM Role for App Runner
resource "aws_iam_role" "apprunner_task_role" {
  name = "pii-backend-apprunner-task-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Environment = var.environment
    Service     = "pii-backend"
  }
}

# IAM Policy for Lambda invocation
resource "aws_iam_role_policy" "apprunner_lambda_policy" {
  name = "pii-backend-lambda-invoke-policy"
  role = aws_iam_role.apprunner_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${var.aws_region}:*:function:${var.lambda_function_name}"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Role for App Runner service (ECR access)
resource "aws_iam_role" "apprunner_access_role" {
  name = "pii-backend-apprunner-access-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Environment = var.environment
    Service     = "pii-backend"
  }
}

# Attach ECR access policy to App Runner access role
resource "aws_iam_role_policy_attachment" "apprunner_ecr_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
  role       = aws_iam_role.apprunner_access_role.name
}

# App Runner Service
resource "aws_apprunner_service" "pii_backend" {
  service_name = "pii-backend-${var.environment}"

  source_configuration {
    image_repository {
      image_identifier      = var.container_image_uri
      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          PII_ENVIRONMENT           = "production"
          PII_DEBUG                = "false"
          PII_API_KEY              = var.api_key
          PII_ALLOWED_ORIGINS      = jsonencode(var.allowed_origins)
          AWS_REGION               = var.aws_region
          PII_LAMBDA_FUNCTION_NAME = var.lambda_function_name
          PII_LAMBDA_TIMEOUT       = "30"
          PII_LAMBDA_RETRY_ATTEMPTS = "3"
          PII_LOG_LEVEL           = "INFO"
        }
      }
      image_repository_type = "ECR"
    }
    access_role_arn = aws_iam_role.apprunner_access_role.arn
  }

  instance_configuration {
    instance_role_arn = aws_iam_role.apprunner_task_role.arn
    cpu               = "0.25 vCPU"  # 0.25, 0.5, 1, 2 vCPU
    memory            = "0.5 GB"     # 0.5, 1, 2, 3, 4 GB
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.pii_backend.arn

  health_check_configuration {
    healthy_threshold   = 1
    interval            = 10
    path               = "/health"
    protocol           = "HTTP"
    timeout            = 5
    unhealthy_threshold = 5
  }

  tags = {
    Environment = var.environment
    Service     = "pii-backend"
    Purpose     = "PII encryption API"
  }
}

# Auto Scaling Configuration
resource "aws_apprunner_auto_scaling_configuration_version" "pii_backend" {
  auto_scaling_configuration_name = "pii-backend-autoscaling-${var.environment}"
  
  max_concurrency = 100  # Max requests per instance
  max_size        = 10   # Max instances
  min_size        = 1    # Min instances (set to 0 for cost savings)

  tags = {
    Environment = var.environment
    Service     = "pii-backend"
  }
}

# Custom Domain (optional)
# resource "aws_apprunner_custom_domain_association" "pii_backend" {
#   domain_name = "api.your-domain.com"
#   service_arn = aws_apprunner_service.pii_backend.arn
# }

# Outputs
output "app_runner_service_url" {
  description = "App Runner service URL"
  value       = "https://${aws_apprunner_service.pii_backend.service_url}"
}

output "app_runner_service_arn" {
  description = "App Runner service ARN"
  value       = aws_apprunner_service.pii_backend.arn
}

output "app_runner_service_id" {
  description = "App Runner service ID"
  value       = aws_apprunner_service.pii_backend.service_id
}