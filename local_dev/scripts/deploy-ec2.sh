#!/bin/bash

# EC2 Docker Deployment Script
# This script builds, pushes to ECR, and deploys to EC2

set -e  # Exit on any error

# ========================================
# CONFIGURATION
# ========================================
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="337909737340"
export ECR_REPO_NAME="fastapi-606"
export EC2_INSTANCE_ID="i-0b8ff2ba8620dfafc"
export SECRET_NAME="prod/fastapi/606"

# Derived variables
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
FULL_IMAGE_URI="$ECR_REGISTRY/$ECR_REPO_NAME:latest"

echo "=================================="
echo "EC2 Docker Deployment Script"
echo "=================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed"
    exit 1
fi

# Check if Docker is running
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

if [ $? -eq 0 ]; then
    echo "✅ Successfully authenticated to ECR"
else
    echo "❌ Failed to authenticate to ECR"
    exit 1
fi
echo ""

# Step 2: Build Docker image for AMD64
echo "🏗️  Step 2: Building Docker image for AMD64..."
docker buildx build --platform linux/amd64 -t $ECR_REPO_NAME:latest --load .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi
echo ""

# Step 3: Tag the image
echo "🏷️  Step 3: Tagging image for ECR..."
docker tag $ECR_REPO_NAME:latest $FULL_IMAGE_URI

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

# Step 5: Deploy to EC2
echo "🚀 Step 5: Deploying to EC2..."
echo "Connecting to EC2 instance..."

aws ssm send-command \
    --instance-ids $EC2_INSTANCE_ID \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=[
        "aws ecr get-login-password --region '"$AWS_REGION"' | docker login --username AWS --password-stdin '"$ECR_REGISTRY"'",
        "docker pull '"$FULL_IMAGE_URI"'",
        "docker stop fastapi-606 || true",
        "docker rm fastapi-606 || true",
        "docker run -d -p 8080:8080 --name fastapi-606 --restart unless-stopped -e SECRET_NAME='"$SECRET_NAME"' -e AWS_REGION='"$AWS_REGION"' '"$FULL_IMAGE_URI"'",
        "docker ps"
    ]' \
    --region $AWS_REGION \
    --output text \
    --query 'Command.CommandId' > /tmp/ssm-command-id.txt

COMMAND_ID=$(cat /tmp/ssm-command-id.txt)

if [ -z "$COMMAND_ID" ]; then
    echo "❌ Failed to send deployment command to EC2"
    exit 1
fi

echo "✅ Deployment command sent (Command ID: $COMMAND_ID)"
echo ""

# Step 6: Wait for deployment to complete
echo "⏳ Step 6: Waiting for deployment to complete..."
sleep 5

aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id $EC2_INSTANCE_ID \
    --region $AWS_REGION \
    --query 'StandardOutputContent' \
    --output text

echo ""
echo "=================================="
echo "🎉 Deployment completed!"
echo "=================================="
echo ""
echo "Your application is available at:"
echo "🔗 http://3.87.100.24:8080"
echo ""
echo "Test endpoints:"
echo "  Health:  curl http://3.87.100.24:8080/health"
echo "  API Docs: http://3.87.100.24:8080/docs"
echo ""
echo "View logs on EC2:"
echo "  docker logs -f fastapi-606"
echo ""

