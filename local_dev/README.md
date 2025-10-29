# 606 App - Local Development Environment

This folder contains your complete local development environment for the 606_app project. It mirrors your AWS production setup but runs locally with your PostgreSQL database.

## 🚀 Quick Start

### 1. Initial Setup
```bash
# Navigate to local development folder
cd local_dev

# Create environment configuration
cp env.example .env

# Edit .env with your local database credentials
nano .env  # or use your preferred editor
```

### 2. Start Development Server
```bash
# Start local FastAPI server with hot reload
./start_local.sh
```

### 3. Access Your Application
- **API Server**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Debug Info**: http://localhost:8000/debug

## 📁 Project Structure

```
local_dev/
├── .env                    # Local environment variables (create from env.example)
├── .env.example            # Environment template
├── start_local.sh          # Start local development server
├── deploy_to_aws.sh        # Deploy to AWS (one-click)
├── README.md               # This file
├── main.py                 # FastAPI application entry point
├── db.py                   # Database connection (auto-detects local vs AWS)
├── aws_config.py           # Smart configuration management
├── query.py                # Natural language query processing
├── query_framework.py      # Query routing and execution
├── auth.py                 # Authentication handling
├── ask606.py               # Core question processing
├── requirements.txt        # Python dependencies
├── dockerfile              # Docker configuration (for AWS deployment)
├── 606_schema.json         # Database schema definition
├── prompt.txt              # AI prompt templates
├── venue_aliases.json      # Venue name mappings
├── executing_bd_aliases.json # Broker name mappings
├── venue_categories.json   # Venue categorization
├── broker_categories.json  # Broker categorization
└── ...                     # Additional configuration files
```

## ⚙️ Environment Configuration

### Local Development (.env file)
```bash
# Database Configuration (Local PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_local_db_name
DB_USER=your_local_db_user
DB_PASSWORD=your_local_db_password

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Development Mode
ENVIRONMENT=local
DEBUG=true
```

### Smart Configuration Detection
The `aws_config.py` automatically detects your environment:
- **Local Development**: Uses `.env` file or environment variables
- **AWS Production**: Uses AWS Secrets Manager
- **No code changes needed** when switching between environments!

## 🗄️ Database Requirements

Your local PostgreSQL database should have the same schema as AWS Aurora:

### Required Tables
- `monthly_data` - Market volume data
- `venue_mapping` - Venue name mappings
- `entity_types` - Entity type definitions
- `finra_ats` - FINRA ATS data (if applicable)

### Schema Compatibility
- Same table structures
- Same data types
- Same indexes
- Same constraints

This ensures seamless testing and deployment between local and AWS environments.

## 🔧 Development Workflow

### Daily Development
1. **Start your day**: `./start_local.sh`
2. **Make changes**: Edit code in this folder
3. **Test locally**: FastAPI auto-reloads on changes
4. **Debug**: Use `/debug` endpoint for diagnostics

### Testing API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the top venues by volume?"}'

# Debug information
curl http://localhost:8000/debug
```

### Database Testing
```bash
# Test database connection
python3 -c "from db import get_db_connection; conn = get_db_connection(); print('✅ Database connected successfully')"
```

## 🐛 Troubleshooting

### Common Issues

**Port 8000 already in use:**
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

**Database connection failed:**
- Check your `.env` file has correct database credentials
- Ensure PostgreSQL is running: `brew services start postgresql`
- Test connection: `psql -h localhost -U your_user -d your_db`

**Module import errors:**
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

**Environment variables not loading:**
- Ensure `.env` file exists in `local_dev/` folder
- Check file permissions: `ls -la .env`

### Debug Endpoints
- `/health` - Basic health check
- `/debug` - Detailed system information
- `/` - Root endpoint with environment info

## 📊 Features

### Core Functionality
- **Natural Language Queries**: Ask questions in plain English
- **Venue Analysis**: Analyze trading venues and market data
- **Broker Analysis**: Analyze executing brokers and their relationships
- **Volume Analysis**: Market volume trends and patterns
- **Cross-Table Enrichment**: Complex queries across multiple tables

### AI Integration
- **OpenAI GPT-4**: Natural language processing
- **Smart Query Generation**: Converts questions to SQL
- **Context-Aware Responses**: Understands financial terminology
- **Error Handling**: Graceful fallbacks for complex queries

## 🔄 Hot Reload Development

The development server automatically reloads when you make changes:
- **Python files**: Instant reload on save
- **Configuration files**: Reload on change
- **Database schema**: No restart needed for schema changes

## 📝 Logging

Development server provides detailed logging:
- **Request/Response**: All API calls logged
- **Database queries**: SQL queries and execution times
- **Error details**: Full stack traces for debugging
- **Environment info**: Configuration and connection status

## 🚀 Next Steps

1. **Test the setup**: Run `./start_local.sh` and visit http://localhost:8000/docs
2. **Configure database**: Update `.env` with your PostgreSQL credentials
3. **Test queries**: Try some sample questions via the API
4. **Develop features**: Make your changes in this folder
5. **Deploy to AWS**: Use `./deploy_to_aws.sh` when ready

---

**Need help?** Check the debug endpoint at http://localhost:8000/debug for system status and configuration details.
