-- Venue/ATS Mapping Table
-- Maps different identifiers for the same trading venue/broker-dealer across tables

DROP TABLE IF EXISTS venue_mapping CASCADE;

CREATE TABLE venue_mapping (
    -- Primary identifier
    venue_id SERIAL PRIMARY KEY,
    
    -- Canonical/preferred name
    canonical_name VARCHAR(255) NOT NULL UNIQUE,
    
    -- Identifiers from different tables
    -- From finra_ats table
    ats_name VARCHAR(255),              -- Full ATS name from FINRA
    mpid VARCHAR(10),                    -- Market Participant ID (FINRA)
    
    -- From executing_bd_606 table
    executing_bd VARCHAR(255),           -- Executing broker-dealer name
    venues VARCHAR(255),                 -- Venue name from 606 reports
    
    -- From monthly_data table
    market_participant VARCHAR(255),     -- Market participant name
    
    -- Additional identifiers
    crd_number VARCHAR(50),              -- CRD number (if applicable)
    sec_id VARCHAR(50),                  -- SEC ID (if applicable)
    
    -- Metadata
    entity_type VARCHAR(50),             -- 'ATS', 'Broker-Dealer', 'Exchange', 'Market Maker', etc.
    is_active BOOLEAN DEFAULT true,
    parent_company VARCHAR(255),         -- Parent company if applicable
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT CURRENT_USER
);

-- Create indexes for lookups from different tables
CREATE INDEX idx_venue_mapping_mpid ON venue_mapping(mpid) WHERE mpid IS NOT NULL;
CREATE INDEX idx_venue_mapping_ats_name ON venue_mapping(ats_name) WHERE ats_name IS NOT NULL;
CREATE INDEX idx_venue_mapping_executing_bd ON venue_mapping(executing_bd) WHERE executing_bd IS NOT NULL;
CREATE INDEX idx_venue_mapping_venues ON venue_mapping(venues) WHERE venues IS NOT NULL;
CREATE INDEX idx_venue_mapping_market_participant ON venue_mapping(market_participant) WHERE market_participant IS NOT NULL;
CREATE INDEX idx_venue_mapping_entity_type ON venue_mapping(entity_type);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_venue_mapping_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
CREATE TRIGGER venue_mapping_update_timestamp
    BEFORE UPDATE ON venue_mapping
    FOR EACH ROW
    EXECUTE FUNCTION update_venue_mapping_timestamp();

-- Add comments
COMMENT ON TABLE venue_mapping IS 'Reference table mapping different identifiers for trading venues/broker-dealers across multiple data sources';
COMMENT ON COLUMN venue_mapping.canonical_name IS 'Preferred/standardized name for the venue';
COMMENT ON COLUMN venue_mapping.ats_name IS 'ATS name from FINRA ATS data';
COMMENT ON COLUMN venue_mapping.mpid IS 'Market Participant ID from FINRA';
COMMENT ON COLUMN venue_mapping.executing_bd IS 'Executing broker-dealer name from 606 reports';
COMMENT ON COLUMN venue_mapping.venues IS 'Venue name from 606 executing_bd table';
COMMENT ON COLUMN venue_mapping.market_participant IS 'Market participant from monthly_data table';

-- Insert initial mappings from finra_ats (to bootstrap the table)
INSERT INTO venue_mapping (canonical_name, ats_name, mpid, entity_type)
SELECT DISTINCT 
    ats_name as canonical_name,
    ats_name,
    mpid,
    'ATS' as entity_type
FROM finra_ats
ON CONFLICT (canonical_name) DO NOTHING;

-- Show summary
SELECT 
    COUNT(*) as total_venues,
    COUNT(DISTINCT mpid) as with_mpid,
    COUNT(DISTINCT ats_name) as with_ats_name,
    COUNT(DISTINCT entity_type) as entity_types
FROM venue_mapping;

\echo ''
\echo '=========================================='
\echo 'Venue Mapping Table Created!'
\echo '=========================================='
\echo 'Initial data loaded from finra_ats table'
\echo 'Next: Add mappings from executing_bd_606 and monthly_data'
\echo ''

COMMIT;



