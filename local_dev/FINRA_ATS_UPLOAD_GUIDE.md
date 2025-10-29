# FINRA ATS Table Upload Guide

**Date:** October 12, 2025
**Database:** app606-cluster RDS PostgreSQL

---

## Table Schema

**Table Name:** `finra_ats`

**Columns:**
- `quarter` (INTEGER) - Quarter (1-4)
- `year` (INTEGER) - Year (YYYY)
- `tier` (VARCHAR) - Tier classification (nms, otc, tier1)
- `ats_name` (VARCHAR) - Alternative Trading System name
- `total_trades` (NUMERIC) - Total number of trades
- `total_shares` (NUMERIC) - Total number of shares traded
- `mpid` (VARCHAR) - Market Participant ID
- `created_at` (TIMESTAMP) - Record creation timestamp

**Primary Key:** (year, quarter, tier, mpid)

**Indexes:**
- `idx_finra_ats_year_quarter` - For time-based queries
- `idx_finra_ats_tier` - For tier filtering
- `idx_finra_ats_mpid` - For ATS lookups
- `idx_finra_ats_ats_name` - For name searches

---

## Data Source

**File:** `/Users/adamsussman/Documents/606_app/aws_app/finra_ats.csv`
**Rows:** 998 data rows (999 including header)
**Time Range:** Q1 2022 - Q2 2025

---

## Upload Methods

### Method 1: Automated Script (Recommended)

```bash
cd /Users/adamsussman/Documents/606_app/aws_app
./upload_finra_ats.sh
```

This will:
1. Create the table with schema
2. Upload all 998 rows
3. Display summary statistics
4. Show sample data

### Method 2: Manual Steps

```bash
# Step 1: Create table
psql -h app606-cluster.cluster-cpsacm6ee9zo.us-east-1.rds.amazonaws.com \
     -U postgres \
     -f create_finra_ats_table.sql

# Step 2: Upload data
psql -h app606-cluster.cluster-cpsacm6ee9zo.us-east-1.rds.amazonaws.com \
     -U postgres \
     -c "\copy finra_ats(quarter, year, tier, ats_name, total_trades, total_shares, mpid) FROM '/Users/adamsussman/Documents/606_app/aws_app/finra_ats.csv' WITH (FORMAT csv, HEADER true);"
```

---

## Verification Queries

After upload, verify the data:

```sql
-- Total rows
SELECT COUNT(*) FROM finra_ats;
-- Expected: 998

-- Date range
SELECT 
    MIN(year) as earliest_year,
    MAX(year) as latest_year,
    COUNT(DISTINCT mpid) as unique_ats
FROM finra_ats;

-- Tier distribution
SELECT tier, COUNT(*) as count 
FROM finra_ats 
GROUP BY tier 
ORDER BY count DESC;

-- Top ATS by total shares (Q2 2025)
SELECT 
    ats_name,
    total_shares,
    total_trades
FROM finra_ats 
WHERE year = 2025 AND quarter = 2
ORDER BY total_shares DESC
LIMIT 10;
```

---

## Sample Queries

```sql
-- Get UBS ATS quarterly performance
SELECT 
    year,
    quarter,
    total_trades,
    total_shares
FROM finra_ats
WHERE mpid = 'UBSA'
ORDER BY year DESC, quarter DESC;

-- Compare NMS vs OTC tiers
SELECT 
    tier,
    SUM(total_trades) as total_trades,
    SUM(total_shares) as total_shares,
    COUNT(DISTINCT mpid) as num_ats
FROM finra_ats
WHERE year = 2025 AND quarter = 2
GROUP BY tier;

-- Year-over-year growth for specific ATS
SELECT 
    year,
    quarter,
    total_shares,
    LAG(total_shares) OVER (ORDER BY year, quarter) as prev_quarter_shares,
    ROUND(((total_shares - LAG(total_shares) OVER (ORDER BY year, quarter)) / 
           LAG(total_shares) OVER (ORDER BY year, quarter) * 100), 2) as growth_pct
FROM finra_ats
WHERE mpid = 'UBSA'
ORDER BY year, quarter;
```

---

## Files Created

✅ `create_finra_ats_table.sql` - Table schema definition
✅ `upload_finra_ats.sh` - Automated upload script
✅ `FINRA_ATS_UPLOAD_GUIDE.md` - This guide

---

**Ready to upload!** 🚀



