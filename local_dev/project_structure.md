# Project Structure & File Guide

## 📁 Complete Project Structure

```
your-fastapi-606-project/
│
├── 📄 Dockerfile                          ← NEW - Created for AWS deployment
├── 📄 requirements.txt                    ← NEW - Python dependencies
├── 📄 deploy.sh                          ← NEW - Automated deployment script
│
├── 📄 aws_config.py                       ← NEW - AWS Secrets Manager integration
├── 📄 db.py                              ← UPDATED - Now uses AWS config
├── 📄 query.py                           ← UPDATED - Now uses AWS config
├── 📄 main.py                            ← KEEP AS IS - Your FastAPI app
├── 📄 auth.py                            ← KEEP AS IS - Your auth logic
│
├── 📄 query_framework.py                  ← KEEP AS IS - Your query utilities
├── 📄 prompt.txt                         ← KEEP AS IS - Your SQL prompt
├── 📄 606_schema.json                    ← KEEP AS IS - Your schema definition
├── 📄 executing_bd_aliases.json          ← KEEP AS IS - Your broker aliases
├── 📄 venue_aliases.json                 ← KEEP AS IS - Your venue aliases
│
├── 📄 .env                               ← KEEP - For local development only
├── 📄 .gitignore                         ← RECOMMENDED - See below
│
└── 📄 ask606.py                          ← LEGACY - Not needed for AWS deployment
```

---

## 📝 File Descriptions

### NEW FILES (Create These)

#### **Dockerfile**
- **Purpose:** Containerizes your FastAPI application
- **What it does:** 
  - Sets up Python 3.11 environment
  - Installs system dependencies (PostgreSQL client, gcc)
  - Installs Python packages from requirements.txt
  - Copies your code into the container
  - Exposes port 8080
  - Runs your FastAPI app with uvicorn
- **Action:** ✅ Copy the provided Dockerfile to your project root

#### **requirements.txt**
- **Purpose:** Lists all Python dependencies
- **What it includes:**
  - fastapi, uvicorn (web framework)
  - psycopg2-binary (PostgreSQL driver)
  - openai (GPT-4 API)
  - pandas (data processing)
  - boto3 (AWS SDK for Python)
  - python-dotenv (local .env support)
- **Action:** ✅ Copy the provided requirements.txt to your project root

#### **aws_config.py**
- **Purpose:** Smart configuration loader
- **What it does:**
  - Detects if running in AWS or locally
  - If in AWS: Reads secrets from AWS Secrets Manager
  - If local: Reads from .env file
  - Caches secrets to avoid repeated API calls
- **Action:** ✅ Create this new file in your project root

#### **deploy.sh**
- **Purpose:** Automated deployment script
- **What it does:**
  - Builds Docker image
  - Authenticates to AWS ECR
  - Pushes image to ECR
  - Triggers App Runner deployment
  - Monitors deployment status
- **Configuration needed:**
  - Update `AWS_REGION`
  - Update `AWS_ACCOUNT_ID`
  - Update `APP_RUNNER_SERVICE_ARN`
- **Action:** ✅ Create this file and make it executable: `chmod +x deploy.sh`

---

### UPDATED FILES (Replace These)

#### **db.py**
- **What changed:** 
  - ❌ Removed: `from dotenv import load_dotenv`
  - ❌ Removed: Direct `os.getenv()` calls
  - ✅ Added: `from aws_config import config`
  - ✅ Changed: Now uses `config.get()` for all credentials
- **Why:** Works both locally (with .env) and in AWS (with Secrets Manager)
- **Action:** ⚠️ Replace your existing db.py with the updated version

#### **query.py** (or queryv1.py)
- **What changed:**
  - ❌ Removed: `from dotenv import load_dotenv`
  - ❌ Removed: `load_dotenv()` call
  - ✅ Added: `from aws_config import config`
  - ✅ Changed: OpenAI client now uses `config.get('OPENAI_API_KEY')`
  - ✅ Fixed: Added `columns` extraction (was missing in your original)
- **Why:** Works both locally and in AWS
- **Action:** ⚠️ Replace your existing query.py with the updated version

---

### KEEP AS IS (No Changes Needed)

#### **main.py**
- Your FastAPI application entry point
- Defines the `/ask` endpoint
- **Action:** ✅ No changes needed

#### **auth.py**
- Your Azure AD authentication logic
- **Action:** ✅ No changes needed
- **Note:** Currently simplified - you may want to enhance this later

#### **query_framework.py**
- Your query classification and SQL generation utilities
- Contains broker and venue alias resolution
- **Action:** ✅ No changes needed

#### **prompt.txt**
- Your system prompt for GPT-4
- Contains SQL generation instructions
- **Action:** ✅ No changes needed

#### **606_schema.json**
- Your database schema definition
- Used by query framework
- **Action:** ✅ No changes needed

#### **executing_bd_aliases.json**
- Your broker name aliases
- **Action:** ✅ No changes needed
- **Make sure:** This file has the structure: `{"executing_bd_map": {...}}`

#### **venue_aliases.json**
- Your venue name aliases
- **Action:** ✅ No changes needed
- **Make sure:** This file has the structure: `{"venue_map": {...}}`

#### **.env**
- Your local development environment variables
- **Action:** ✅ Keep this for local testing
- **Important:** ⚠️ Never commit this file to git!

---

### OPTIONAL/LEGACY FILES

#### **ask606.py**
- Your original standalone script
- **Status:** Not used in AWS deployment
- **Action:** Can delete or keep for reference

---

## 🔒 .gitignore File (Recommended)

Create a `.gitignore` file to avoid committing sensitive data:

```
# Environment variables
.env
.env.local
.env.production

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# AWS
.aws-sam/

# Local test data
*.db
*.sqlite
```

---

## 🚀 How Files Work Together

### Local Development Flow:
```
1. You run: uvicorn main:app --reload
2. main.py starts FastAPI
3. User sends request to /ask endpoint
4. query.py calls aws_config.py
5. aws_config.py detects local environment
6. aws_config.py reads .env file
7. db.py uses config to connect to database
8. OpenAI client uses config for API key
9. Results returned to user
```

### AWS Production Flow:
```
1. App Runner starts your Docker container
2. Dockerfile runs: uvicorn main:app
3. main.py starts FastAPI
4. User sends request to /ask endpoint
5. query.py calls aws_config.py
6. aws_config.py detects AWS environment
7. aws_config.py fetches from Secrets Manager
8. db.py uses config to connect to RDS
9. OpenAI client uses config for API key
10. Results returned to user
```

---

## ✅ Quick Setup Checklist

- [ ] Create all NEW files (Dockerfile, requirements.txt, aws_config.py, deploy.sh)
- [ ] Replace db.py with updated version
- [ ] Replace query.py with updated version
- [ ] Verify all mapping JSON files exist (aliases)
- [ ] Create .gitignore file
- [ ] Update deploy.sh with your AWS account details
- [ ] Test locally: `docker build -t fastapi-606 .`
- [ ] Test locally: `docker run -p 8080:8080 --env-file .env fastapi-606`
- [ ] Follow AWS deployment guide

---

## 🧪 Testing Your Setup

### Test 1: Local Docker Build
```bash
docker build -t fastapi-606 .
```
✅ Should complete without errors

### Test 2: Local Docker Run
```bash
docker run -p 8080:8080 --env-file .env fastapi-606
```
✅ Should start without errors

### Test 3: API Call
```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Give me a list of all unique venue names"}'
```
✅ Should return SQL query and results

### Test 4: Verify AWS Config
```python
# Run in Python shell
from aws_config import config
print(config.get('DB_HOST'))
```
✅ Should print your database host (from .env locally)

---

## 📞 Support & Next Steps

**If you encounter issues:**

1. **Docker build fails**
   - Check that all files are in the correct location
   - Verify requirements.txt has no syntax errors
   - Check Docker is running

2. **Local testing fails**
   - Verify .env file has all required variables
   - Check database connection from your machine
   - Test OpenAI API key separately

3. **AWS deployment fails**
   - Check CloudWatch logs in App Runner console
   - Verify Secrets Manager has correct values
   - Confirm IAM role has proper permissions
   - Check VPC connector and security groups

**Ready to deploy?**
→ Follow the **AWS Deployment Guide** step-by-step