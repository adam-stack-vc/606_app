-- Create FINRA ATS table and load data
-- Based on finra_ats.csv structure

-- Drop table if exists (optional - comment out if you want to keep existing data)
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
    
    -- Add composite primary key
    PRIMARY KEY (year, quarter, tier, mpid)
);

-- Create indexes for common queries
CREATE INDEX idx_finra_ats_year_quarter ON finra_ats(year, quarter);
CREATE INDEX idx_finra_ats_tier ON finra_ats(tier);
CREATE INDEX idx_finra_ats_mpid ON finra_ats(mpid);
CREATE INDEX idx_finra_ats_ats_name ON finra_ats(ats_name);

-- Add comment to table
COMMENT ON TABLE finra_ats IS 'FINRA ATS (Alternative Trading System) quarterly trading data';
COMMENT ON COLUMN finra_ats.quarter IS 'Quarter (1-4)';
COMMENT ON COLUMN finra_ats.year IS 'Year (YYYY)';
COMMENT ON COLUMN finra_ats.tier IS 'Tier classification (nms, otc, tier1, etc.)';
COMMENT ON COLUMN finra_ats.ats_name IS 'Alternative Trading System name';
COMMENT ON COLUMN finra_ats.total_trades IS 'Total number of trades';
COMMENT ON COLUMN finra_ats.total_shares IS 'Total number of shares traded';
COMMENT ON COLUMN finra_ats.mpid IS 'Market Participant ID';

-- Grant permissions (adjust as needed)
-- GRANT SELECT ON finra_ats TO readonly_user;
-- GRANT ALL ON finra_ats TO readwrite_user;

COMMIT;



