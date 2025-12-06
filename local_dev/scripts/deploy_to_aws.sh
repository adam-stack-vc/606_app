#!/bin/bash

# Streamlined AWS Deployment Script
# This script deploys your local development to AWS with minimal configuration

set -e

# ========================================
# CONFIGURATION - UPDATE THESE VALUES
# ========================================
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="337909737340"
export ECR_REPO_NAME="fastapi-606"
export APP_RUNNER_SERVICE_ARN="arn:aws:apprunner:us-east-1:123456789012:service/fastapi-606-service/abc123"

# Derived variables
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
FULL_IMAGE_URI="$ECR_REGISTRY/$ECR_REPO_NAME:latest"

echo "=================================="
echo "Streamlined AWS Deployment"
echo "=================================="
echo ""

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Error: Docker not running"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Step 1: Copy local development to deployment folder
echo "📋 Step 1: Preparing deployment files..."
if [ -d "../aws_app" ]; then
    echo "Copying local changes to aws_app folder..."
    cp -r . ../aws_app/
    cd ../aws_app
else
    echo "❌ Error: aws_app folder not found"
    exit 1
fi

# Step 2: Authenticate to ECR
echo "🔐 Step 2: Authenticating to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REGISTRY

# Step 3: Build and push Docker image
echo "🏗️  Step 3: Building and pushing Docker image..."
docker build -t $ECR_REPO_NAME:latest .
docker tag $ECR_REPO_NAME:latest $FULL_IMAGE_URI
docker push $FULL_IMAGE_URI

# Step 4: Deploy to AWS
echo "🚀 Step 4: Deploying to AWS..."
aws apprunner start-deployment \
    --service-arn $APP_RUNNER_SERVICE_ARN \
    --region $AWS_REGION

echo ""
echo "=================================="
echo "🎉 Deployment initiated!"
echo "=================================="
echo ""
echo "Monitor deployment in AWS Console:"
echo "https://console.aws.amazon.com/apprunner/home?region=$AWS_REGION"
echo ""

# Return to local development folder
cd ../local_dev
echo "✅ Returned to local development folder"
