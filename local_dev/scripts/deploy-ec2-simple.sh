#!/bin/bash

# EC2 Docker Deployment Script - Simple Version
# This script builds and pushes to ECR, then shows EC2 commands

set -e  # Exit on any error

# ========================================
# CONFIGURATION
# ========================================
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="337909737340"
export ECR_REPO_NAME="fastapi-606"
export SECRET_NAME="prod/fastapi/606"

# Derived variables
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
FULL_IMAGE_URI="$ECR_REGISTRY/$ECR_REPO_NAME:latest"

echo "=================================="
echo "EC2 Docker Deployment Script"
echo "=================================="
echo ""

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Step 1: Authenticate Docker to ECR
echo "🔐 Step 1: Authenticating to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REGISTRY
echo "✅ Successfully authenticated to ECR"
echo ""

# Step 2: Build Docker image for AMD64
echo "🏗️  Step 2: Building Docker image for AMD64..."
docker buildx build --platform linux/amd64 -t $ECR_REPO_NAME:latest --load .
echo "✅ Docker image built successfully"
echo ""

# Step 3: Tag the image
echo "🏷️  Step 3: Tagging image for ECR..."
docker tag $ECR_REPO_NAME:latest $FULL_IMAGE_URI
echo "✅ Image tagged: $FULL_IMAGE_URI"
echo ""

# Step 4: Push to ECR
echo "📤 Step 4: Pushing image to ECR..."
docker push $FULL_IMAGE_URI
echo "✅ Image pushed to ECR successfully"
echo ""

# Show EC2 deployment commands
echo "=================================="
echo "🎉 Build & Push Complete!"
echo "=================================="
echo ""
echo "📋 Now run these commands on your EC2 instance:"
echo ""
echo "aws ecr get-login-password --region $AWS_REGION | \\"
echo "  docker login --username AWS --password-stdin $ECR_REGISTRY"
echo ""
echo "docker pull $FULL_IMAGE_URI"
echo ""
echo "docker stop fastapi-606 || true"
echo "docker rm fastapi-606 || true"
echo ""
echo "docker run -d \\"
echo "  -p 8080:8080 \\"
echo "  --name fastapi-606 \\"
echo "  --restart unless-stopped \\"
echo "  -e SECRET_NAME=\"$SECRET_NAME\" \\"
echo "  -e AWS_REGION=\"$AWS_REGION\" \\"
echo "  $FULL_IMAGE_URI"
echo ""
echo "docker ps"
echo "docker logs -f fastapi-606"
echo ""
echo "=================================="
echo "Your app will be at: http://3.87.100.24:8080"
echo "=================================="

