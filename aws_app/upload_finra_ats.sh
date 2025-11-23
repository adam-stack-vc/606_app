#!/bin/bash
# Upload FINRA ATS data to PostgreSQL

DB_HOST="app606-cluster.cluster-cpsacm6ee9zo.us-east-1.rds.amazonaws.com"
DB_USER="postgres"
CSV_FILE="/Users/adamsussman/Documents/606_app/aws_app/finra_ats.csv"
SQL_FILE="/Users/adamsussman/Documents/606_app/aws_app/create_finra_ats_table.sql"

echo "=========================================="
echo "FINRA ATS Table Upload"
echo "=========================================="
echo ""
echo "Step 1: Creating table schema..."
echo ""

# Create the table
psql -h "$DB_HOST" -U "$DB_USER" -f "$SQL_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Table created successfully"
    echo ""
    echo "Step 2: Uploading CSV data..."
    echo ""
    
    # Upload CSV data using \copy (client-side copy)
    psql -h "$DB_HOST" -U "$DB_USER" << EOF
\copy finra_ats(quarter, year, tier, ats_name, total_trades, total_shares, mpid) FROM '$CSV_FILE' WITH (FORMAT csv, HEADER true);

-- Show upload results
SELECT 
    COUNT(*) as total_rows,
    MIN(year) as earliest_year,
    MAX(year) as latest_year,
    COUNT(DISTINCT mpid) as unique_ats
FROM finra_ats;

-- Show sample data
SELECT * FROM finra_ats ORDER BY year DESC, quarter DESC LIMIT 10;
EOF
    
    echo ""
    echo "=========================================="
    echo "✅ Upload Complete!"
    echo "=========================================="
else
    echo ""
    echo "❌ Table creation failed"
    exit 1
fi



