#!/bin/bash

# Deploy PII Backend to AWS App Runner using Terraform
# Usage: ./deploy.sh [plan|apply|destroy]

set -e

ACTION=${1:-plan}
TERRAFORM_DIR="$(dirname "$0")/terraform"

echo "🚀 PII Backend App Runner Deployment"
echo "Action: $ACTION"
echo "Terraform directory: $TERRAFORM_DIR"
echo

# Check if terraform.tfvars exists
if [ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
    echo "❌ Error: terraform.tfvars not found!"
    echo
    echo "Please create terraform.tfvars from the example:"
    echo "cp $TERRAFORM_DIR/terraform.tfvars.example $TERRAFORM_DIR/terraform.tfvars"
    echo "Then edit terraform.tfvars with your configuration."
    exit 1
fi

# Change to terraform directory
cd "$TERRAFORM_DIR"

# Initialize Terraform
echo "🔧 Initializing Terraform..."
terraform init

# Validate configuration
echo "✅ Validating Terraform configuration..."
terraform validate

case $ACTION in
    "plan")
        echo "📋 Creating Terraform plan..."
        terraform plan
        ;;
    "apply")
        echo "🚀 Applying Terraform configuration..."
        terraform apply
        echo
        echo "✅ Deployment complete!"
        echo
        echo "App Runner service URL:"
        terraform output -raw app_runner_service_url
        ;;
    "destroy")
        echo "💥 Destroying infrastructure..."
        terraform destroy
        ;;
    *)
        echo "❌ Unknown action: $ACTION"
        echo "Usage: $0 [plan|apply|destroy]"
        exit 1
        ;;
esac

echo
echo "🎉 Operation completed successfully!"