# KMS Keys for PII Encryption System
# Use this as reference for manual AWS console setup

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Variables for customization
variable "environment" {
  description = "Environment name (e.g., prototype, dev, prod)"
  type        = string
  default     = "prototype"
}

variable "project_name" {
  description = "Project name for resource tagging"
  type        = string
  default     = "pii-encryption"
}

# KMS Key for Level 2 PII Encryption (Medium Sensitivity)
# Manual Setup: AWS Console > KMS > Customer managed keys > Create key
resource "aws_kms_key" "pii_level2" {
  description             = "PII Level 2 field encryption for medium sensitivity data"
  deletion_window_in_days = 10
  enable_key_rotation     = true
  multi_region           = false

  # Key usage and specifications
  key_usage = "ENCRYPT_DECRYPT"
  key_spec  = "SYMMETRIC_DEFAULT"

  # Key policy (least privilege)
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Lambda Function Access"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_execution.arn
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "lambda.${data.aws_region.current.name}.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-level2-key"
    Environment = var.environment
    PIILevel    = "2"
    Purpose     = "Field-level encryption for medium sensitivity PII"
    Project     = var.project_name
  }
}

# KMS Key Alias for Level 2
resource "aws_kms_alias" "pii_level2" {
  name          = "alias/pii-level2"
  target_key_id = aws_kms_key.pii_level2.key_id
}

# KMS Key for Level 3 PII Encryption (High Sensitivity)
# Manual Setup: AWS Console > KMS > Customer managed keys > Create key
resource "aws_kms_key" "pii_level3" {
  description             = "PII Level 3 field encryption for high sensitivity data"
  deletion_window_in_days = 10
  enable_key_rotation     = true
  multi_region           = false

  # Key usage and specifications
  key_usage = "ENCRYPT_DECRYPT"
  key_spec  = "SYMMETRIC_DEFAULT"

  # Key policy (least privilege)
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Lambda Function Access"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_execution.arn
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "lambda.${data.aws_region.current.name}.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-level3-key"
    Environment = var.environment
    PIILevel    = "3"
    Purpose     = "Double encryption for high sensitivity PII"
    Project     = var.project_name
  }
}

# KMS Key Alias for Level 3
resource "aws_kms_alias" "pii_level3" {
  name          = "alias/pii-level3"
  target_key_id = aws_kms_key.pii_level3.key_id
}

# Additional KMS Key for RDS Aurora encryption (optional)
resource "aws_kms_key" "rds_encryption" {
  description             = "RDS Aurora encryption for PII database"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow RDS Service Access"
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-rds-key"
    Environment = var.environment
    Purpose     = "RDS Aurora database encryption"
    Project     = var.project_name
  }
}

resource "aws_kms_alias" "rds_encryption" {
  name          = "alias/pii-rds-encryption"
  target_key_id = aws_kms_key.rds_encryption.key_id
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# IAM Role for Lambda (will be referenced by the KMS policies)
# This is a placeholder - actual IAM role defined in iam-roles.tf
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-lambda-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Outputs for reference
output "kms_level2_key_id" {
  description = "KMS Key ID for Level 2 PII encryption"
  value       = aws_kms_key.pii_level2.key_id
}

output "kms_level2_key_arn" {
  description = "KMS Key ARN for Level 2 PII encryption"
  value       = aws_kms_key.pii_level2.arn
}

output "kms_level3_key_id" {
  description = "KMS Key ID for Level 3 PII encryption"
  value       = aws_kms_key.pii_level3.key_id
}

output "kms_level3_key_arn" {
  description = "KMS Key ARN for Level 3 PII encryption"
  value       = aws_kms_key.pii_level3.arn
}

output "kms_rds_key_id" {
  description = "KMS Key ID for RDS encryption"
  value       = aws_kms_key.rds_encryption.key_id
}

output "kms_aliases" {
  description = "KMS Key aliases for easy reference"
  value = {
    level2 = aws_kms_alias.pii_level2.name
    level3 = aws_kms_alias.pii_level3.name
    rds    = aws_kms_alias.rds_encryption.name
  }
}