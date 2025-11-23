#!/bin/bash

# AWS App Runner Deployment Script
# This script builds, tags, and pushes your Docker image to ECR,
# then triggers a new App Runner deployment

set -e  # Exit on any error

# ========================================
# CONFIGURATION - UPDATE THESE VALUES
# ========================================
export AWS_REGION="us-east-1"                    # Your AWS region
export AWS_ACCOUNT_ID="123456789012"             # Your AWS account ID
export ECR_REPO_NAME="fastapi-606"               # Your ECR repository name
export APP_RUNNER_SERVICE_ARN="arn:aws:apprunner:us-east-1:123456789012:service/fastapi-606-service/abc123"  # Your App Runner service ARN

# ========================================
# DERIVED VARIABLES (Don't change these)
# ========================================
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
IMAGE_NAME="$ECR_REPO_NAME"
FULL_IMAGE_URI="$ECR_REGISTRY/$IMAGE_NAME:latest"

echo "=================================="
echo "AWS App Runner Deployment Script"
echo "=================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Step 1: Authenticate Docker to ECR
echo "🔐 Step 1: Authenticating to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REGISTRY

if [ $? -eq 0 ]; then
    echo "✅ Successfully authenticated to ECR"
else
    echo "❌ Failed to authenticate to ECR"
    exit 1
fi
echo ""

# Step 2: Build Docker image
echo "🏗️  Step 2: Building Docker image..."
docker build -t $IMAGE_NAME:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi
echo ""

# Step 3: Tag the image
echo "🏷️  Step 3: Tagging image for ECR..."
docker tag $IMAGE_NAME:latest $FULL_IMAGE_URI

if [ $? -eq 0 ]; then
    echo "✅ Image tagged: $FULL_IMAGE_URI"
else
    echo "❌ Failed to tag image"
    exit 1
fi
echo ""

# Step 4: Push to ECR
echo "📤 Step 4: Pushing image to ECR..."
docker push $FULL_IMAGE_URI

if [ $? -eq 0 ]; then
    echo "✅ Image pushed to ECR successfully"
else
    echo "❌ Failed to push image to ECR"
    exit 1
fi
echo ""

# Step 5: Trigger App Runner deployment
echo "🚀 Step 5: Triggering App Runner deployment..."
aws apprunner start-deployment \
    --service-arn $APP_RUNNER_SERVICE_ARN \
    --region $AWS_REGION

if [ $? -eq 0 ]; then
    echo "✅ App Runner deployment started"
else
    echo "❌ Failed to start App Runner deployment"
    exit 1
fi
echo ""

# Step 6: Monitor deployment status
echo "⏳ Step 6: Monitoring deployment status..."
echo "Checking every 30 seconds (this may take 3-5 minutes)..."
echo ""

for i in {1..20}; do
    STATUS=$(aws apprunner describe-service \
        --service-arn $APP_RUNNER_SERVICE_ARN \
        --region $AWS_REGION \
        --query 'Service.Status' \
        --output text)
    
    echo "[$i/20] Current status: $STATUS"
    
    if [ "$STATUS" == "RUNNING" ]; then
        echo ""
        echo "=================================="
        echo "🎉 Deployment completed successfully!"
        echo "=================================="
        echo ""
        
        # Get service URL
        SERVICE_URL=$(aws apprunner describe-service \
            --service-arn $APP_RUNNER_SERVICE_ARN \
            --region $AWS_REGION \
            --query 'Service.ServiceUrl' \
            --output text)
        
        echo "Your service is available at:"
        echo "🔗 https://$SERVICE_URL"
        echo ""
        echo "Test with:"
        echo "curl -X POST https://$SERVICE_URL/ask \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{\"question\": \"Give me a list of all unique venue names\"}'"
        echo ""
        exit 0
    fi
    
    if [ "$STATUS" == "OPERATION_IN_PROGRESS" ]; then
        sleep 30
        continue
    fi
    
    if [ "$STATUS" == "CREATE_FAILED" ] || [ "$STATUS" == "UPDATE_FAILED" ]; then
        echo ""
        echo "❌ Deployment failed with status: $STATUS"
        echo "Check CloudWatch logs for 