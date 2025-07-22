#!/bin/bash
# Quick Deploy Script for PII Backend to AWS
# This script automates the ECR push process for manual App Runner deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION=${1:-us-east-1}
REPOSITORY_NAME=${2:-pii-backend}
TAG=${3:-latest}

echo -e "${BLUE}🚀 PII Backend Quick Deploy to AWS${NC}"
echo "Region: $REGION"
echo "Repository: $REPOSITORY_NAME" 
echo "Tag: $TAG"
echo ""

# Verify prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install and configure AWS CLI${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure'${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites checked${NC}"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME"

echo ""
echo -e "${BLUE}📦 ECR Configuration:${NC}"
echo "Account ID: $ACCOUNT_ID"
echo "ECR URI: $ECR_URI:$TAG"
echo ""

# Create ECR repository if it doesn't exist
echo -e "${YELLOW}🏗️  Creating ECR repository if needed...${NC}"
aws ecr describe-repositories --repository-names $REPOSITORY_NAME --region $REGION 2>/dev/null || {
    echo "Creating repository $REPOSITORY_NAME..."
    aws ecr create-repository \
        --repository-name $REPOSITORY_NAME \
        --region $REGION \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
    echo -e "${GREEN}✅ Repository created${NC}"
}

# Authenticate Docker with ECR
echo -e "${YELLOW}🔐 Authenticating with ECR...${NC}"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI

# Navigate to backend directory
cd "$(dirname "$0")/../.."

# Build Docker image
echo -e "${YELLOW}🏗️  Building Docker image...${NC}"
docker build -t $REPOSITORY_NAME:$TAG .

# Tag for ECR
echo -e "${YELLOW}🏷️  Tagging image for ECR...${NC}"
docker tag $REPOSITORY_NAME:$TAG $ECR_URI:$TAG

# Push to ECR
echo -e "${YELLOW}⬆️  Pushing to ECR...${NC}"
docker push $ECR_URI:$TAG

echo ""
echo -e "${GREEN}🎉 Successfully pushed to ECR!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Copy this image URI: ${YELLOW}$ECR_URI:$TAG${NC}"
echo "2. Follow the manual deployment guide to create App Runner service"
echo "3. Use the image URI above in the App Runner configuration"
echo ""
echo -e "${BLUE}🔗 Quick Links:${NC}"
echo "• ECR Console: https://console.aws.amazon.com/ecr/repositories"
echo "• App Runner Console: https://console.aws.amazon.com/apprunner/home"
echo "• Manual Guide: ./MANUAL-DEPLOYMENT-GUIDE.md"
echo ""
echo -e "${YELLOW}💡 Pro tip:${NC} Save the image URI - you'll need it for App Runner configuration"

# Save image URI to a file for easy access
echo "$ECR_URI:$TAG" > .image-uri
echo -e "${GREEN}✅ Image URI saved to .image-uri file${NC}"