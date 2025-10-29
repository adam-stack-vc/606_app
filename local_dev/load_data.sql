-- 606 App Data Loading Script
-- This script loads sample data into your local PostgreSQL database

-- ========================================
-- 1. LOAD FINRA ATS DATA
-- ========================================

\echo 'Loading FINRA ATS data...'

-- Copy data from CSV file (skip id and created_at columns)
\copy finra_ats (quarter, year, tier, ats_name, total_trades, total_shares, mpid) FROM '/Users/adamsussman/Documents/606_app/local_dev/finra_ats.csv' WITH CSV HEADER;

\echo 'FINRA ATS data loaded: ' || (SELECT COUNT(*) FROM finra_ats) || ' records'

-- ========================================
-- 2. LOAD MONTHLY DATA (Sample)
-- ========================================

\echo 'Loading monthly market data...'

-- Load monthly data from your exported CSV (skip id and created_at columns)
\copy monthly_data (day, market_participant, tape_a_shares, tape_b_shares, tape_c_shares, total_shares, tape_a_notional, tape_b_notional, tape_c_notional, total_notional, tape_a_trade_count, tape_b_trade_count, tape_c_trade_count, total_trade_count) FROM '/Users/adamsussman/Documents/606_app/local_dev/monthly_data.csv' WITH CSV HEADER;

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
-- 4. CREATE VENUE MAPPINGS
-- ========================================

\echo 'Creating venue mappings...'

-- Insert mappings from finra_ats
INSERT INTO venue_mapping (canonical_name, ats_name, mpid, entity_type)
SELECT DISTINCT 
    ats_name as canonical_name,
    ats_name,
    mpid,
    'ATS' as entity_type
FROM finra_ats
ON CONFLICT (canonical_name) DO NOTHING;

-- Insert mappings from monthly_data
INSERT INTO venue_mapping (canonical_name, market_participant, entity_type)
SELECT DISTINCT 
    market_participant as canonical_name,
    market_participant,
    CASE 
        WHEN market_participant LIKE '%NYSE%' OR market_participant LIKE '%NASDAQ%' THEN 'EXCH'
        WHEN market_participant LIKE '%ATS%' THEN 'ATS'
        ELSE 'Broker'
    END as entity_type
FROM monthly_data
WHERE market_participant NOT IN (SELECT canonical_name FROM venue_mapping)
ON CONFLICT (canonical_name) DO NOTHING;

\echo 'Venue mappings created: ' || (SELECT COUNT(*) FROM venue_mapping) || ' records'

-- Load real venue mapping data from AWS export (match CSV columns)
\echo 'Loading real venue mapping data...'
\copy venue_mapping (canonical_name, mpid, ats_name, executing_bd, venues, market_participant, entity_type, parent_company, is_active, notes) FROM '/Users/adamsussman/Documents/606_app/local_dev/venue_mapping.csv' WITH CSV HEADER;

\echo 'Real venue mapping data loaded: ' || (SELECT COUNT(*) FROM venue_mapping) || ' records'

-- ========================================
-- 5. LOAD REAL 606 DATA
-- ========================================

\echo 'Loading real 606 data from AWS export...'

-- Copy real 606 data from exported CSV file (match CSV column order)
-- Handle empty strings by converting them to NULL for numeric fields
\copy executing_bd_606 (executing_bd, venues, stock_group, marketablelimitpct, nonmarketablelimitpct, otherpct, netpmtpaidrecvmarketordersusd, netpmtpaidrecvmarketorderscph, netpmtpaidrecvmarketablelimitordersusd, netpmtpaidrecvmarketablelimitorderscph, netpmtpaidrecvnonmarketablelimitordersusd, netpmtpaidrecvnonmarketablelimitorderscph, netpmtpaidrecvotherordersusd, netpmtpaidrecvotherorderscph, materialaspects, month, year, data_type, ndopct, ndomarketpct, ndomarketablelimitpct, ndononmarketablelimitpct, ndootherpct, orderpct, marketpct) FROM '/Users/adamsussman/Documents/606_app/local_dev/executing_bd_606.csv' WITH CSV HEADER NULL '';

-- Clean up any remaining empty strings in numeric columns
UPDATE executing_bd_606 SET marketablelimitpct = NULL WHERE marketablelimitpct = 0;
UPDATE executing_bd_606 SET nonmarketablelimitpct = NULL WHERE nonmarketablelimitpct = 0;
UPDATE executing_bd_606 SET otherpct = NULL WHERE otherpct = 0;
UPDATE executing_bd_606 SET netpmtpaidrecvmarketordersusd = NULL WHERE netpmtpaidrecvmarketordersusd = 0;
UPDATE executing_bd_606 SET netpmtpaidrecvmarketorderscph = NULL WHERE netpmtpaidrecvmarketorderscph = 0;
UPDATE executing_bd_606 SET netpmtpaidrecvmarketablelimitordersusd = NULL WHERE netpmtpaidrecvmarketablelimitordersusd = 0;
UPDATE executing_bd_606 SET netpmtpaidrecvmarketablelimitorderscph = NULL WHERE netpmtpaidrecvmarketablelimitorderscph = 0;
UPDATE executing_bd_606 SET netpmtpaidrecvnonmarketablelimitordersusd = NULL WHERE netpmtpaidrecvnonmarketablelimitordersusd = 0;
UPDATE executing_bd_606 SET netpmtpaidrecvnonmarketablelimitorderscph = NULL WHERE netpmtpaidrecvnonmarketablelimitorderscph = 0;
UPDATE executing_bd_606 SET netpmtpaidrecvotherordersusd = NULL WHERE netpmtpaidrecvotherordersusd = 0;
UPDATE executing_bd_606 SET netpmtpaidrecvotherorderscph = NULL WHERE netpmtpaidrecvotherorderscph = 0;
UPDATE executing_bd_606 SET ndopct = NULL WHERE ndopct = 0;
UPDATE executing_bd_606 SET ndomarketpct = NULL WHERE ndomarketpct = 0;
UPDATE executing_bd_606 SET ndomarketablelimitpct = NULL WHERE ndomarketablelimitpct = 0;
UPDATE executing_bd_606 SET ndononmarketablelimitpct = NULL WHERE ndononmarketablelimitpct = 0;
UPDATE executing_bd_606 SET ndootherpct = NULL WHERE ndootherpct = 0;
UPDATE executing_bd_606 SET orderpct = NULL WHERE orderpct = 0;
UPDATE executing_bd_606 SET marketpct = NULL WHERE marketpct = 0;

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
