-- 606 App Local Database Setup Script
-- This script creates all necessary tables and loads data for local development

-- ========================================
-- 1. CREATE MAIN TABLES
-- ========================================

-- Create executing_bd_606 table (main 606 data)
DROP TABLE IF EXISTS executing_bd_606 CASCADE;

CREATE TABLE executing_bd_606 (
    id SERIAL PRIMARY KEY,
    executing_bd VARCHAR(255),
    venues VARCHAR(255),
    stock_group VARCHAR(50) CHECK (stock_group IN ('SP500', 'OtherStocks', 'Options')),
    marketablelimitpct NUMERIC,
    nonmarketablelimitpct NUMERIC,
    otherpct NUMERIC,
    
    netpmtpaidrecvmarketordersusd NUMERIC,
    netpmtpaidrecvmarketorderscph NUMERIC,
    netpmtpaidrecvmarketablelimitordersusd NUMERIC,
    netpmtpaidrecvmarketablelimitorderscph NUMERIC,
    netpmtpaidrecvnonmarketablelimitordersusd NUMERIC,
    netpmtpaidrecvnonmarketablelimitorderscph NUMERIC,
    netpmtpaidrecvotherordersusd NUMERIC,
    netpmtpaidrecvotherorderscph NUMERIC,
    
    ndopct NUMERIC,
    ndomarketpct NUMERIC,
    ndomarketablelimitpct NUMERIC,
    ndononmarketablelimitpct NUMERIC,
    ndootherpct NUMERIC,
    
    orderpct NUMERIC,
    marketpct NUMERIC,
    
    materialaspects TEXT,
    month VARCHAR(10),
    year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_type VARCHAR(50) CHECK (data_type IN ('executing_bd', 'venue'))
);

-- Create monthly_data table (market volume data)
DROP TABLE IF EXISTS monthly_data CASCADE;

CREATE TABLE monthly_data (
    id SERIAL PRIMARY KEY,
    day DATE,
    market_participant VARCHAR(255),
    tape_a_shares BIGINT,
    tape_b_shares BIGINT,
    tape_c_shares BIGINT,
    total_shares BIGINT,
    tape_a_notional NUMERIC,
    tape_b_notional NUMERIC,
    tape_c_notional NUMERIC,
    total_notional NUMERIC,
    tape_a_trade_count INTEGER,
    tape_b_trade_count INTEGER,
    tape_c_trade_count INTEGER,
    total_trade_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create finra_ats table
DROP TABLE IF EXISTS finra_ats CASCADE;

CREATE TABLE finra_ats (
    id SERIAL PRIMARY KEY,
    quarter INTEGER,
    year INTEGER,
    tier VARCHAR(10),
    ats_name VARCHAR(255),
    total_trades NUMERIC,
    total_shares NUMERIC,
    mpid VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create entity_types table
DROP TABLE IF EXISTS entity_types CASCADE;

CREATE TABLE entity_types (
    id SERIAL PRIMARY KEY,
    venue_name VARCHAR(255) NOT NULL UNIQUE,
    entity_type VARCHAR(50) NOT NULL,
    description TEXT,
    parent_organization VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create venue_mapping table
DROP TABLE IF EXISTS venue_mapping CASCADE;

CREATE TABLE venue_mapping (
    venue_id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(255) NOT NULL UNIQUE,
    ats_name VARCHAR(255),
    mpid VARCHAR(10),
    executing_bd VARCHAR(255),
    venues VARCHAR(255),
    market_participant VARCHAR(255),
    crd_number VARCHAR(50),
    sec_id VARCHAR(50),
    entity_type VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    parent_company VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT CURRENT_USER
);

-- ========================================
-- 2. CREATE INDEXES
-- ========================================

-- Indexes for executing_bd_606
CREATE INDEX idx_executing_bd_606_executing_bd ON executing_bd_606(executing_bd);
CREATE INDEX idx_executing_bd_606_venues ON executing_bd_606(venues);
CREATE INDEX idx_executing_bd_606_month_year ON executing_bd_606(month, year);
CREATE INDEX idx_executing_bd_606_data_type ON executing_bd_606(data_type);

-- Indexes for monthly_data
CREATE INDEX idx_monthly_data_day ON monthly_data(day);
CREATE INDEX idx_monthly_data_market_participant ON monthly_data(market_participant);
CREATE INDEX idx_monthly_data_total_shares ON monthly_data(total_shares);

-- Indexes for finra_ats
CREATE INDEX idx_finra_ats_ats_name ON finra_ats(ats_name);
CREATE INDEX idx_finra_ats_mpid ON finra_ats(mpid);
CREATE INDEX idx_finra_ats_year_quarter ON finra_ats(year, quarter);

-- Indexes for entity_types
CREATE INDEX idx_entity_types_venue_name ON entity_types(venue_name);
CREATE INDEX idx_entity_types_entity_type ON entity_types(entity_type);

-- Indexes for venue_mapping
CREATE INDEX idx_venue_mapping_canonical_name ON venue_mapping(canonical_name);
CREATE INDEX idx_venue_mapping_mpid ON venue_mapping(mpid) WHERE mpid IS NOT NULL;
CREATE INDEX idx_venue_mapping_ats_name ON venue_mapping(ats_name) WHERE ats_name IS NOT NULL;
CREATE INDEX idx_venue_mapping_executing_bd ON venue_mapping(executing_bd) WHERE executing_bd IS NOT NULL;
CREATE INDEX idx_venue_mapping_venues ON venue_mapping(venues) WHERE venues IS NOT NULL;
CREATE INDEX idx_venue_mapping_market_participant ON venue_mapping(market_participant) WHERE market_participant IS NOT NULL;

-- ========================================
-- 3. CREATE TRIGGERS
-- ========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER entity_types_update_timestamp
    BEFORE UPDATE ON entity_types
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER venue_mapping_update_timestamp
    BEFORE UPDATE ON venue_mapping
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- ========================================
-- 4. ADD COMMENTS
-- ========================================

COMMENT ON TABLE executing_bd_606 IS 'Main 606 report data for executing broker-dealers and venues';
COMMENT ON TABLE monthly_data IS 'Daily market volume data by market participant';
COMMENT ON TABLE finra_ats IS 'FINRA ATS trading data';
COMMENT ON TABLE entity_types IS 'Maps venues to their entity types (Broker, ATS, EXCH)';
COMMENT ON TABLE venue_mapping IS 'Reference table mapping different identifiers for trading venues/broker-dealers across multiple data sources';

-- ========================================
-- 5. SUCCESS MESSAGE
-- ========================================

\echo ''
\echo '=========================================='
\echo '606 App Database Tables Created Successfully!'
\echo '=========================================='
\echo 'Tables created:'
\echo '  - executing_bd_606 (main 606 data)'
\echo '  - monthly_data (market volume data)'
\echo '  - finra_ats (FINRA ATS data)'
\echo '  - entity_types (venue type mappings)'
\echo '  - venue_mapping (cross-reference table)'
\echo ''
\echo 'Next steps:'
\echo '  1. Load data using load_data.sql'
\echo '  2. Test with: SELECT COUNT(*) FROM executing_bd_606;'
\echo ''

COMMIT;
