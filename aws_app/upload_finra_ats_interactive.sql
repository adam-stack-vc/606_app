-- FINRA ATS Table Creation and Data Upload
-- Database: postgres
-- Run this with: psql -h app606-cluster.cluster-cpsacm6ee9zo.us-east-1.rds.amazonaws.com -U postgres -d postgres -f upload_finra_ats_interactive.sql

-- Drop table if exists
DROP TABLE IF EXISTS finra_ats;

-- Create table
CREATE TABLE finra_ats (
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL,
    tier VARCHAR(50) NOT NULL,
    ats_name VARCHAR(255) NOT NULL,
    total_trades NUMERIC(15, 2),
    total_shares NUMERIC(18, 2),
    mpid VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (year, quarter, tier, mpid)
);

-- Create indexes
CREATE INDEX idx_finra_ats_year_quarter ON finra_ats(year, quarter);
CREATE INDEX idx_finra_ats_tier ON finra_ats(tier);
CREATE INDEX idx_finra_ats_mpid ON finra_ats(mpid);
CREATE INDEX idx_finra_ats_ats_name ON finra_ats(ats_name);

-- Add comments
COMMENT ON TABLE finra_ats IS 'FINRA ATS quarterly trading data (Q1 2022 - Q2 2025)';

-- Load data using client-side copy
\copy finra_ats(quarter, year, tier, ats_name, total_trades, total_shares, mpid) FROM '/Users/adamsussman/Documents/606_app/aws_app/finra_ats.csv' WITH (FORMAT csv, HEADER true);

-- Show results
\echo ''
\echo '=========================================='
\echo 'Upload Complete! Summary:'
\echo '=========================================='

SELECT 
    COUNT(*) as total_rows,
    MIN(year) as earliest_year,
    MAX(year) as latest_year,
    COUNT(DISTINCT mpid) as unique_ats,
    COUNT(DISTINCT tier) as tiers
FROM finra_ats;

\echo ''
\echo 'Tier Distribution:'
SELECT tier, COUNT(*) as count 
FROM finra_ats 
GROUP BY tier 
ORDER BY count DESC;

\echo ''
\echo 'Latest Quarter (Q2 2025) - Top 10 ATS:'
SELECT 
    ats_name,
    tier,
    total_shares as shares,
    total_trades as trades
FROM finra_ats 
WHERE year = 2025 AND quarter = 2
ORDER BY total_shares DESC
LIMIT 10;

