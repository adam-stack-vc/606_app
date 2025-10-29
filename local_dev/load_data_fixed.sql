-- 606 App Data Loading Script - Fixed Version
-- This script loads real data into your local PostgreSQL database

-- ========================================
-- 1. LOAD FINRA ATS DATA
-- ========================================

\echo 'Loading FINRA ATS data...'

-- Create temporary table to handle extra columns
CREATE TEMP TABLE temp_finra_ats (
    quarter INTEGER,
    year INTEGER,
    tier VARCHAR(10),
    ats_name VARCHAR(255),
    total_trades NUMERIC,
    total_shares NUMERIC,
    mpid VARCHAR(10),
    created_at TIMESTAMP
);

-- Load data into temp table
\copy temp_finra_ats FROM '/Users/adamsussman/Documents/606_app/local_dev/finra_ats.csv' WITH CSV HEADER;

-- Insert into real table (skip created_at)
INSERT INTO finra_ats (quarter, year, tier, ats_name, total_trades, total_shares, mpid)
SELECT quarter, year, tier, ats_name, total_trades, total_shares, mpid
FROM temp_finra_ats;

DROP TABLE temp_finra_ats;

\echo 'FINRA ATS data loaded: ' || (SELECT COUNT(*) FROM finra_ats) || ' records'

-- ========================================
-- 2. LOAD MONTHLY DATA
-- ========================================

\echo 'Loading monthly market data...'

-- Create temporary table to handle extra columns
CREATE TEMP TABLE temp_monthly_data (
    id INTEGER,
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
    created_at TIMESTAMP
);

-- Load data into temp table
\copy temp_monthly_data FROM '/Users/adamsussman/Documents/606_app/local_dev/monthly_data.csv' WITH CSV HEADER;

-- Insert into real table (skip id and created_at)
INSERT INTO monthly_data (day, market_participant, tape_a_shares, tape_b_shares, tape_c_shares, total_shares, tape_a_notional, tape_b_notional, tape_c_notional, total_notional, tape_a_trade_count, tape_b_trade_count, tape_c_trade_count, total_trade_count)
SELECT day, market_participant, tape_a_shares, tape_b_shares, tape_c_shares, total_shares, tape_a_notional, tape_b_notional, tape_c_notional, total_notional, tape_a_trade_count, tape_b_trade_count, tape_c_trade_count, total_trade_count
FROM temp_monthly_data;

DROP TABLE temp_monthly_data;

\echo 'Monthly data loaded: ' || (SELECT COUNT(*) FROM monthly_data) || ' records'

-- ========================================
-- 3. LOAD ENTITY TYPES (Sample Data)
-- ========================================

\echo 'Loading entity types...'

INSERT INTO entity_types (venue_name, entity_type, description, parent_organization) VALUES
-- Major Exchanges
('NYSE', 'EXCH', 'New York Stock Exchange', 'Intercontinental Exchange'),
('NASDAQ', 'EXCH', 'NASDAQ Stock Market', 'Nasdaq Inc.'),
('NYSE American', 'EXCH', 'NYSE American Exchange', 'Intercontinental Exchange'),
('NYSE National', 'EXCH', 'NYSE National Exchange', 'Intercontinental Exchange'),
('NASDAQ BX', 'EXCH', 'NASDAQ BX Exchange', 'Nasdaq Inc.'),

-- Major ATS
('UBS ATS', 'ATS', 'UBS Alternative Trading System', 'UBS'),
('SIGMA X2', 'ATS', 'Credit Suisse SIGMA X2 ATS', 'Credit Suisse'),
('CROSSFINDER', 'ATS', 'Goldman Sachs CROSSFINDER ATS', 'Goldman Sachs'),
('JPM-X', 'ATS', 'JPMorgan JPM-X ATS', 'JPMorgan Chase'),
('MS Pool', 'ATS', 'Morgan Stanley MS Pool ATS', 'Morgan Stanley'),

-- Major Brokers
('Robinhood Securities, LLC', 'Broker', 'Robinhood retail broker', 'Robinhood Markets'),
('Charles Schwab & Co., Inc.', 'Broker', 'Charles Schwab retail broker', 'Charles Schwab Corporation'),
('Fidelity Brokerage Services LLC', 'Broker', 'Fidelity retail broker', 'Fidelity Investments'),
('TD Ameritrade', 'Broker', 'TD Ameritrade retail broker', 'Charles Schwab Corporation'),
('E*TRADE Securities LLC', 'Broker', 'E*TRADE retail broker', 'Morgan Stanley'),

-- Market Makers
('Citadel Securities LLC', 'Market Maker', 'Citadel market making', 'Citadel LLC'),
('Virtu Financial', 'Market Maker', 'Virtu market making', 'Virtu Financial'),
('Two Sigma Securities', 'Market Maker', 'Two Sigma market making', 'Two Sigma'),
('DRW Trading', 'Market Maker', 'DRW market making', 'DRW Holdings'),

-- Wholesalers
('Citadel Securities LLC', 'Wholesaler', 'Citadel wholesale trading', 'Citadel LLC'),
('Virtu Financial', 'Wholesaler', 'Virtu wholesale trading', 'Virtu Financial'),
('Two Sigma Securities', 'Wholesaler', 'Two Sigma wholesale trading', 'Two Sigma')

ON CONFLICT (venue_name) DO NOTHING;

\echo 'Entity types loaded: ' || (SELECT COUNT(*) FROM entity_types) || ' records'

-- ========================================
-- 4. LOAD VENUE MAPPINGS
-- ========================================

\echo 'Loading venue mapping data...'

-- Create temporary table to handle extra columns
CREATE TEMP TABLE temp_venue_mapping (
    venue_id INTEGER,
    canonical_name VARCHAR(255),
    mpid VARCHAR(10),
    ats_name VARCHAR(255),
    executing_bd VARCHAR(255),
    venues VARCHAR(255),
    market_participant VARCHAR(255),
    entity_type VARCHAR(50),
    parent_company VARCHAR(255),
    is_active BOOLEAN,
    aliases TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    notes TEXT
);

-- Load data into temp table
\copy temp_venue_mapping FROM '/Users/adamsussman/Documents/606_app/local_dev/venue_mapping.csv' WITH CSV HEADER;

-- Insert into real table (skip venue_id, aliases, created_at, updated_at)
INSERT INTO venue_mapping (canonical_name, mpid, ats_name, executing_bd, venues, market_participant, entity_type, parent_company, is_active, notes)
SELECT canonical_name, mpid, ats_name, executing_bd, venues, market_participant, entity_type, parent_company, is_active, notes
FROM temp_venue_mapping;

DROP TABLE temp_venue_mapping;

\echo 'Venue mapping data loaded: ' || (SELECT COUNT(*) FROM venue_mapping) || ' records'

-- ========================================
-- 5. LOAD REAL 606 DATA
-- ========================================

\echo 'Loading real 606 data from AWS export...'

-- Create temporary table to handle extra columns
CREATE TEMP TABLE temp_executing_bd_606 (
    executing_bd VARCHAR(255),
    venues VARCHAR(255),
    stock_group VARCHAR(50),
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
    materialaspects TEXT,
    month VARCHAR(10),
    year INTEGER,
    created_at TIMESTAMP,
    data_type VARCHAR(50),
    ndopct NUMERIC,
    ndomarketpct NUMERIC,
    ndomarketablelimitpct NUMERIC,
    ndononmarketablelimitpct NUMERIC,
    ndootherpct NUMERIC,
    orderpct NUMERIC,
    marketpct NUMERIC
);

-- Load data into temp table
\copy temp_executing_bd_606 FROM '/Users/adamsussman/Documents/606_app/local_dev/executing_bd_606.csv' WITH CSV HEADER NULL '';

-- Insert into real table (skip created_at)
INSERT INTO executing_bd_606 (executing_bd, venues, stock_group, marketablelimitpct, nonmarketablelimitpct, otherpct, netpmtpaidrecvmarketordersusd, netpmtpaidrecvmarketorderscph, netpmtpaidrecvmarketablelimitordersusd, netpmtpaidrecvmarketablelimitorderscph, netpmtpaidrecvnonmarketablelimitordersusd, netpmtpaidrecvnonmarketablelimitorderscph, netpmtpaidrecvotherordersusd, netpmtpaidrecvotherorderscph, materialaspects, month, year, data_type, ndopct, ndomarketpct, ndomarketablelimitpct, ndononmarketablelimitpct, ndootherpct, orderpct, marketpct)
SELECT executing_bd, venues, stock_group, marketablelimitpct, nonmarketablelimitpct, otherpct, netpmtpaidrecvmarketordersusd, netpmtpaidrecvmarketorderscph, netpmtpaidrecvmarketablelimitordersusd, netpmtpaidrecvmarketablelimitorderscph, netpmtpaidrecvnonmarketablelimitordersusd, netpmtpaidrecvnonmarketablelimitorderscph, netpmtpaidrecvotherordersusd, netpmtpaidrecvotherorderscph, materialaspects, month, year, data_type, ndopct, ndomarketpct, ndomarketablelimitpct, ndononmarketablelimitpct, ndootherpct, orderpct, marketpct
FROM temp_executing_bd_606;

DROP TABLE temp_executing_bd_606;

\echo 'Real 606 data loaded: ' || (SELECT COUNT(*) FROM executing_bd_606) || ' records'

-- ========================================
-- 6. VERIFICATION QUERIES
-- ========================================

\echo ''
\echo '=========================================='
\echo 'Data Loading Complete!'
\echo '=========================================='
\echo 'Summary:'
\echo '  - FINRA ATS: ' || (SELECT COUNT(*) FROM finra_ats) || ' records'
\echo '  - Monthly Data: ' || (SELECT COUNT(*) FROM monthly_data) || ' records'
\echo '  - Entity Types: ' || (SELECT COUNT(*) FROM entity_types) || ' records'
\echo '  - Venue Mappings: ' || (SELECT COUNT(*) FROM venue_mapping) || ' records'
\echo '  - 606 Data: ' || (SELECT COUNT(*) FROM executing_bd_606) || ' records'
\echo ''
\echo 'Sample queries to test:'
\echo '  SELECT COUNT(*) FROM executing_bd_606;'
\echo '  SELECT * FROM venue_mapping LIMIT 5;'
\echo '  SELECT DISTINCT market_participant FROM monthly_data LIMIT 10;'
\echo ''

COMMIT;
