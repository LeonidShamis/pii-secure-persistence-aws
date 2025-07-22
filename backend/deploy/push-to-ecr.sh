#!/bin/bash

# Push Docker image to AWS ECR
# Usage: ./push-to-ecr.sh [region] [repository-name] [tag]

set -e

# Default values
REGION=${1:-us-east-1}
REPOSITORY=${2:-pii-backend}
TAG=${3:-latest}

echo "🚀 Pushing PII Backend to ECR"
echo "Region: $REGION"
echo "Repository: $REPOSITORY"
echo "Tag: $TAG"
echo

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $ACCOUNT_ID"

# ECR repository URL
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY"
echo "ECR URI: $ECR_URI"
echo

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository if needed..."
aws ecr describe-repositories --repository-names $REPOSITORY --region $REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $REPOSITORY --region $REGION

# Get ECR login token
echo "🔐 Authenticating with ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI

# Build Docker image
echo "🏗️  Building Docker image..."
cd "$(dirname "$0")/../.." # Go to backend root directory
docker build -t $REPOSITORY:$TAG .

# Tag for ECR
echo "🏷️  Tagging image for ECR..."
docker tag $REPOSITORY:$TAG $ECR_URI:$TAG

# Push to ECR
echo "⬆️  Pushing to ECR..."
docker push $ECR_URI:$TAG

echo
echo "✅ Successfully pushed to ECR!"
echo "Image URI: $ECR_URI:$TAG"
echo
echo "Use this URI in your terraform.tfvars:"
echo "container_image_uri = \"$ECR_URI:$TAG\""