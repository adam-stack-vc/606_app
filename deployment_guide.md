# AWS App Runner Deployment Guide

## 📋 Prerequisites Checklist

Before starting, gather this information from your AWS account:

- [ ] AWS Account ID
- [ ] AWS Region (e.g., `us-east-1`)
- [ ] RDS PostgreSQL Endpoint
- [ ] RDS Database Name
- [ ] RDS Username
- [ ] RDS Password
- [ ] VPC ID (where RDS is located)
- [ ] Security Group ID (for RDS)
- [ ] OpenAI API Key

---

## 🔐 Step 1: Create AWS Secrets Manager Secret

### Option A: Using AWS Console

1. Go to **AWS Secrets Manager** in AWS Console
2. Click **Store a new secret**
3. Select **Other type of secret**
4. Add the following key-value pairs:

```
DB_HOST: [YOUR_RDS_ENDPOINT]
DB_PORT: 5432
DB_NAME: [YOUR_DATABASE_NAME]
DB_USER: [YOUR_DB_USERNAME]
DB_PASSWORD: [YOUR_DB_PASSWORD]
OPENAI_API_KEY: [YOUR_OPENAI_KEY]
```

5. Name your secret: `prod/fastapi/606`
6. Click through and create the secret
7. **Copy the Secret ARN** - you'll need this later

### Option B: Using AWS CLI

```bash
aws secretsmanager create-secret \
    --name prod/fastapi/606 \
    --description "FastAPI 606 application secrets" \
    --secret-string '{
        "DB_HOST":"YOUR_RDS_ENDPOINT",
        "DB_PORT":"5432",
        "DB_NAME":"YOUR_DATABASE_NAME",
        "DB_USER":"YOUR_DB_USERNAME",
        "DB_PASSWORD":"YOUR_DB_PASSWORD",
        "OPENAI_API_KEY":"YOUR_OPENAI_KEY"
    }' \
    --region us-east-1
```

---

## 🏗️ Step 2: Prepare Your Project Structure

Your project should have this structure:

```
your-project/
├── Dockerfile                    # ✅ Created above
├── requirements.txt              # ✅ Created above
├── aws_config.py                 # ✅ Created above
├── main.py                       # ✅ Your existing file
├── db.py                         # ⚠️ Replace with updated version
├── query.py                      # ⚠️ Replace with updated version
├── auth.py                       # ✅ Your existing file
├── prompt.txt                    # ✅ Your existing file
├── 606_schema.json              # ✅ Your existing file
├── query_framework.py           # ✅ Your existing file
├── executing_bd_aliases.json    # ✅ Your mapping file
├── venue_aliases.json           # ✅ Your mapping file
└── .env                         # ⚠️ Keep for local testing only
```

**Important:** Replace `db.py` and `query.py` with the AWS-enabled versions provided above.

---

## 🐳 Step 3: Build and Test Docker Image Locally

```bash
# Build the image
docker build -t fastapi-606 .

# Test locally (using .env file)
docker run -p 8080:8080 --env-file .env fastapi-606

# Test the endpoint
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Give me a list of all unique venue names"}'
```

If this works locally, you're ready to deploy! 🎉

---

## ☁️ Step 4: Push Image to Amazon ECR

### Create ECR Repository

```bash
# Set your AWS region and account ID
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=337909737340  # ⚠️ REPLACE WITH YOUR ACCOUNT ID

# Create ECR repository
aws ecr create-repository \
    --repository-name fastapi-606 \
    --region $AWS_REGION
```

### Authenticate Docker to ECR

```bash
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

### Tag and Push Image

```bash
# Tag the image
docker tag fastapi-606:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fastapi-606:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fastapi-606:latest
```

**Copy the full image URI** - you'll need it next:
```
123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-606:latest
```

---

## 🚀 Step 5: Create IAM Role for App Runner

### Option A: Using AWS Console

1. Go to **IAM** → **Roles** → **Create role**
2. Select **AWS Service** → **App Runner**
3. Attach these policies:
   - `AWSAppRunnerServicePolicyForECRAccess` (for pulling images)
   - Create a custom inline policy for Secrets Manager:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": ""
        }
    ]
}
```

4. Name the role: `AppRunnerECRAccessRole`
5. **Copy the Role ARN**

### Option B: Using AWS CLI

Create `trust-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Create `secrets-policy.json`:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/fastapi/606-*"
        }
    ]
}
```

Run commands:
```bash
# Create the role
aws iam create-role \
    --role-name AppRunnerECRAccessRole \
    --assume-role-policy-document file://trust-policy.json

# Attach ECR access policy
aws iam attach-role-policy \
    --role-name AppRunnerECRAccessRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess

# Create and attach secrets policy
aws iam put-role-policy \
    --role-name AppRunnerECRAccessRole \
    --policy-name SecretsManagerAccess \
    --policy-document file://secrets-policy.json
```

---

## 🎯 Step 6: Create App Runner Service

### Option A: Using AWS Console

1. Go to **App Runner** in AWS Console
2. Click **Create service**
3. **Source:**
   - Repository type: **Container registry**
   - Provider: **Amazon ECR**
   - Browse and select your image: `fastapi-606:latest`
   - Deployment trigger: **Manual** (or Automatic)
4. **Service settings:**
   - Service name: `fastapi-606-service`
   - Virtual CPU: **1 vCPU**
   - Memory: **2 GB**
   - Port: **8080**
5. **Environment variables:**
   - `SECRET_NAME`: `prod/fastapi/606`
   - `AWS_REGION`: `us-east-1`
6. **Security:**
   - Instance role: Select the role you created
   - VPC connector: Select your VPC (where RDS is located)
   - Security groups: Add the RDS security group
vpc-0b2322d2ed6c5a117

7. **Review and create**

### Option B: Using AWS CLI

Create `apprunner-config.json`:

```json
{
  "ServiceName": "fastapi-606-service",
  "SourceConfiguration": {
    "ImageRepository": {
      "ImageIdentifier": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-606:latest",
      "ImageConfiguration": {
        "Port": "8080",
        "RuntimeEnvironmentVariables": {
          "SECRET_NAME": "prod/fastapi/606",
          "AWS_REGION": "us-east-1"
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AuthenticationConfiguration": {
      "AccessRoleArn": "arn:aws:iam::123456789012:role/AppRunnerECRAccessRole"
    }
  },
  "InstanceConfiguration": {
    "Cpu": "1 vCPU",
    "Memory": "2 GB",
    "InstanceRoleArn": "arn:aws:iam::123456789012:role/AppRunnerECRAccessRole"
  },
  "NetworkConfiguration": {
    "EgressConfiguration": {
      "EgressType": "VPC",
      "VpcConnectorArn": "arn:aws:apprunner:us-east-1:123456789012:vpcconnector/YOUR_VPC_CONNECTOR"
    }
  }
}
```

**⚠️ Replace these values:**
- Image URI
- Account ID
- Role ARN
- VPC Connector ARN

Then run:
```bash
aws apprunner create-service --cli-input-json file://apprunner-config.json
```

---

## ✅ Step 7: Verify Deployment

### Check Service Status

```bash
aws apprunner list-services --region us-east-1
```

Wait for status to be **RUNNING** (takes 3-5 minutes)

### Get Service URL

```bash
aws apprunner describe-service \
    --service-arn YOUR_SERVICE_ARN \
    --query 'Service.ServiceUrl' \
    --output text
```

### Test the Endpoint

```bash
# Your App Runner URL will look like:
# https://abc123xyz.us-east-1.awsapprunner.com

curl -X POST https://YOUR_APP_RUNNER_URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Give me a list of all unique venue names"}'
```

---

## 🔄 Step 8: Update Your Application

When you make code changes:

```bash
# 1. Rebuild Docker image
docker build -t fastapi-606 .

# 2. Tag and push to ECR
docker tag fastapi-606:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fastapi-606:latest
    
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/fastapi-606:latest

# 3. Trigger new deployment (if manual deployment)
aws apprunner start-deployment --service-arn YOUR_SERVICE_ARN
```

---

## 🛡️ Security Best Practices

✅ **Your database is now secure:**
- RDS is in a **private subnet** (no internet access)
- App Runner connects through **VPC connector**
- Credentials stored in **Secrets Manager** (encrypted)
- No `.env` files in production

✅ **Additional recommendations:**
- Enable App Runner **health checks**: `/health` endpoint
- Add **CloudWatch logs** monitoring
- Set up **CloudWatch alarms** for errors
- Use **AWS WAF** if exposing to public internet

---

## 🐛 Troubleshooting

### Container won't start
- Check CloudWatch logs: App Runner → Your service → Logs
- Common issues:
  - Wrong port (must be 8080)
  - Missing environment variables
  - Database connection failure

### Can't connect to RDS
- Verify VPC connector is configured
- Check security group allows App Runner
- Verify RDS endpoint in Secrets Manager

### Secrets not loading
- Check IAM role has Secrets Manager permissions
- Verify secret name matches: `prod/fastapi/606`
- Check `SECRET_NAME` environment variable

---

## 💰 Cost Estimate

**App Runner:**
- ~$25-40/month for 1 vCPU, 2GB memory (24/7 runtime)
- Pay per request for actual usage

**Secrets Manager:**
- $0.40/month per secret
- $0.05 per 10,000 API calls

**ECR:**
- $0.10/GB storage per month
- Free data transfer to App Runner

**Total estimated cost:** ~$30-50/month depending on traffic

---

## 🎉 You're Done!

Your FastAPI app is now running securely in AWS with:
- ✅ Private database access (no internet exposure)
- ✅ Secure credential management
- ✅ Auto-scaling and high availability
- ✅ HTTPS by default
- ✅ Easy updates via Docker

**Your API URL:** `https://[service-id].us-east-1.awsapprunner.com`