-- Venue Mapping System with Aliases
-- Database: postgres
-- Integrates venue_aliases.json with cross-table mappings
-- Run this with: psql -h app606-cluster.cluster-cpsacm6ee9zo.us-east-1.rds.amazonaws.com -U postgres -d postgres -f create_venue_mapping_with_aliases.sql

-- ============================================================================
-- TABLE 1: venue_mapping (Main reference table)
-- ============================================================================
DROP TABLE IF EXISTS venue_aliases CASCADE;
DROP TABLE IF EXISTS venue_mapping CASCADE;

CREATE TABLE venue_mapping (
    venue_id SERIAL PRIMARY KEY,
    
    -- Canonical name (from venue_aliases.json keys)
    canonical_name VARCHAR(255) NOT NULL UNIQUE,
    
    -- Cross-table identifiers
    mpid VARCHAR(10),                    -- FINRA MPID
    ats_name VARCHAR(255),               -- FINRA ATS full name
    executing_bd VARCHAR(255),           -- 606 executing BD name
    venues VARCHAR(255),                 -- 606 venue name
    market_participant VARCHAR(255),     -- monthly_data participant name
    
    -- Additional metadata
    entity_type VARCHAR(50),             -- 'ATS', 'Exchange', 'Broker-Dealer', 'Market Maker'
    parent_company VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    
    -- Store aliases as JSONB for flexible queries
    aliases JSONB,                       -- Array of aliases from venue_aliases.json
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- ============================================================================
-- TABLE 2: venue_aliases (Normalized alias lookup - many aliases to one venue)
-- ============================================================================
CREATE TABLE venue_aliases (
    alias_id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venue_mapping(venue_id) ON DELETE CASCADE,
    alias VARCHAR(255) NOT NULL,
    alias_type VARCHAR(50),              -- 'common_name', 'mpid', 'legal_entity', 'abbreviation'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Each alias should be unique
    UNIQUE(alias)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- venue_mapping indexes
CREATE INDEX idx_venue_mapping_mpid ON venue_mapping(mpid) WHERE mpid IS NOT NULL;
CREATE INDEX idx_venue_mapping_canonical ON venue_mapping USING gin(to_tsvector('english', canonical_name));
CREATE INDEX idx_venue_mapping_aliases ON venue_mapping USING gin(aliases);
CREATE INDEX idx_venue_mapping_entity_type ON venue_mapping(entity_type);

-- venue_aliases indexes
CREATE INDEX idx_venue_aliases_venue_id ON venue_aliases(venue_id);
CREATE INDEX idx_venue_aliases_alias ON venue_aliases(alias);
CREATE INDEX idx_venue_aliases_alias_lower ON venue_aliases(LOWER(alias));

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to find venue by any alias
CREATE OR REPLACE FUNCTION find_venue_by_alias(search_term TEXT)
RETURNS TABLE (
    venue_id INTEGER,
    canonical_name VARCHAR(255),
    matched_alias VARCHAR(255),
    mpid VARCHAR(10)
) AS $$
BEGIN
    -- First try exact match on canonical name
    RETURN QUERY
    SELECT 
        vm.venue_id,
        vm.canonical_name,
        search_term as matched_alias,
        vm.mpid
    FROM venue_mapping vm
    WHERE LOWER(vm.canonical_name) = LOWER(search_term)
    LIMIT 1;
    
    -- If no exact match, try aliases
    IF NOT FOUND THEN
        RETURN QUERY
        SELECT 
            vm.venue_id,
            vm.canonical_name,
            va.alias as matched_alias,
            vm.mpid
        FROM venue_aliases va
        JOIN venue_mapping vm ON va.venue_id = vm.venue_id
        WHERE LOWER(va.alias) = LOWER(search_term)
        LIMIT 1;
    END IF;
    
    -- If still not found, try fuzzy match on canonical name
    IF NOT FOUND THEN
        RETURN QUERY
        SELECT 
            vm.venue_id,
            vm.canonical_name,
            'fuzzy match' as matched_alias,
            vm.mpid
        FROM venue_mapping vm
        WHERE LOWER(vm.canonical_name) LIKE '%' || LOWER(search_term) || '%'
        LIMIT 1;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to get all identifiers for a venue
CREATE OR REPLACE FUNCTION get_venue_identifiers(search_term TEXT)
RETURNS TABLE (
    canonical_name VARCHAR(255),
    mpid VARCHAR(10),
    ats_name VARCHAR(255),
    executing_bd VARCHAR(255),
    venues VARCHAR(255),
    market_participant VARCHAR(255),
    all_aliases TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vm.canonical_name,
        vm.mpid,
        vm.ats_name,
        vm.executing_bd,
        vm.venues,
        vm.market_participant,
        ARRAY_AGG(DISTINCT va.alias) as all_aliases
    FROM venue_mapping vm
    LEFT JOIN venue_aliases va ON vm.venue_id = va.venue_id
    WHERE vm.venue_id = (SELECT venue_id FROM find_venue_by_alias(search_term) LIMIT 1)
    GROUP BY vm.venue_id, vm.canonical_name, vm.mpid, vm.ats_name, 
             vm.executing_bd, vm.venues, vm.market_participant;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS FOR EASY QUERYING
-- ============================================================================

-- View that shows all aliases flattened
CREATE OR REPLACE VIEW venue_all_names AS
SELECT 
    vm.venue_id,
    vm.canonical_name,
    vm.mpid,
    vm.entity_type,
    COALESCE(va.alias, vm.canonical_name) as name_variant,
    CASE 
        WHEN va.alias IS NULL THEN 'canonical'
        ELSE va.alias_type
    END as name_type
FROM venue_mapping vm
LEFT JOIN venue_aliases va ON vm.venue_id = va.venue_id;

COMMENT ON VIEW venue_all_names IS 'Flattened view showing all name variants for each venue';

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE venue_mapping IS 'Master reference table for trading venues with cross-table identifiers';
COMMENT ON TABLE venue_aliases IS 'Alias lookup table - maps various names to canonical venue names';
COMMENT ON FUNCTION find_venue_by_alias(TEXT) IS 'Find venue by any alias or identifier (exact, fuzzy)';
COMMENT ON FUNCTION get_venue_identifiers(TEXT) IS 'Get all identifiers for a venue across all tables';

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
\echo ''
\echo '=========================================='
\echo 'Venue Mapping Tables Created!'
\echo '=========================================='
\echo ''
\echo 'Next steps:'
\echo '1. Load venue_aliases.json data'
\echo '2. Add MPID mappings from finra_ats'
\echo '3. Add mappings from executing_bd_606'
\echo '4. Add mappings from monthly_data'
\echo ''

