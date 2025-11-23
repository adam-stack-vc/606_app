#!/bin/bash

# 606 App Local Database Setup Script
# This script creates tables and loads data into your local PostgreSQL database

set -e

# Load .env if present (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# Prefer DB_PASSWORD from .env if available, else keep existing PGPASSWORD
if [ -n "$DB_PASSWORD" ]; then
    export PGPASSWORD="$DB_PASSWORD"
fi

echo "=================================="
echo "606 App Local Database Setup"
echo "=================================="
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" >/dev/null 2>&1; then
    echo "❌ Error: PostgreSQL is not running"
    echo "Please start PostgreSQL first:"
    echo "  brew services start postgresql"
    echo "  or"
    echo "  sudo systemctl start postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"
echo ""

# Check if we're in the right directory
if [ ! -f "create_tables.sql" ]; then
    echo "❌ Error: create_tables.sql not found"
    echo "Please run this script from the local_dev directory"
    exit 1
fi

echo "✅ Found setup files"
echo ""

# Create tables
echo "📋 Step 1: Creating database tables..."
psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-postgres}" -f create_tables.sql

if [ $? -eq 0 ]; then
    echo "✅ Tables created successfully"
else
    echo "❌ Error creating tables"
    exit 1
fi
echo ""

# Load data
echo "📊 Step 2: Loading data..."
psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-postgres}" -f load_data_robust.sql

if [ $? -eq 0 ]; then
    echo "✅ Data loaded successfully"
else
    echo "❌ Error loading data"
    exit 1
fi
echo ""

# Verify setup
echo "🔍 Step 3: Verifying setup..."
psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-postgres}" -c "
SELECT 
    'executing_bd_606' as table_name, COUNT(*) as records FROM executing_bd_606
UNION ALL
SELECT 
    'monthly_data' as table_name, COUNT(*) as records FROM monthly_data
UNION ALL
SELECT 
    'finra_ats' as table_name, COUNT(*) as records FROM finra_ats
UNION ALL
SELECT 
    'entity_types' as table_name, COUNT(*) as records FROM entity_types
UNION ALL
SELECT 
    'venue_mapping' as table_name, COUNT(*) as records FROM venue_mapping
ORDER BY table_name;
"

echo ""
echo "=================================="
echo "🎉 Database Setup Complete!"
echo "=================================="
echo ""
echo "Your local PostgreSQL database is now ready with:"
echo "  ✅ All required tables created"
echo "  ✅ Real data loaded from AWS export"
echo "  ✅ Indexes and constraints applied"
echo ""
echo "Next steps:"
echo "  1. Test your FastAPI app: ./start_local.sh"
echo "  2. Visit: http://localhost:8000/docs"
echo "  3. Test a query: curl -X POST http://localhost:8000/ask -H 'Content-Type: application/json' -d '{\"question\": \"What are the top venues by volume?\"}'"
echo ""
echo "Database connection test:"
echo "  psql -h localhost -U postgres -d postgres -c \"SELECT COUNT(*) FROM executing_bd_606;\""
echo ""
