-- 606 App Data Loading Script - Robust Version
-- This script handles CSV files with variable column counts

-- ========================================
-- 1. LOAD FINRA ATS DATA
-- ========================================

\echo 'Loading FINRA ATS data...'

-- Create temporary table with exact number of columns (8)
CREATE TEMP TABLE temp_finra_ats (
    col1 TEXT, col2 TEXT, col3 TEXT, col4 TEXT, col5 TEXT, col6 TEXT, col7 TEXT, col8 TEXT
);

-- Load data as text (handles any number of columns)
\copy temp_finra_ats FROM '/Users/adamsussman/Documents/606_app/local_dev/finra_ats.csv' WITH CSV HEADER;

-- Insert into real table (map columns by position)
INSERT INTO finra_ats (quarter, year, tier, ats_name, total_trades, total_shares, mpid)
SELECT 
    col1::INTEGER as quarter,
    col2::INTEGER as year,
    col3 as tier,
    col4 as ats_name,
    col5::NUMERIC as total_trades,
    col6::NUMERIC as total_shares,
    col7 as mpid
FROM temp_finra_ats
WHERE col1 IS NOT NULL AND col1 != 'quarter'; -- Skip header row

DROP TABLE temp_finra_ats;

\echo 'FINRA ATS data loaded: ' || (SELECT COUNT(*) FROM finra_ats) || ' records'

-- ========================================
-- 2. LOAD MONTHLY DATA
-- ========================================

\echo 'Loading monthly market data...'

-- Create temporary table with exact number of columns (16)
CREATE TEMP TABLE temp_monthly_data (
    col1 TEXT, col2 TEXT, col3 TEXT, col4 TEXT, col5 TEXT, col6 TEXT, col7 TEXT, col8 TEXT, col9 TEXT, col10 TEXT,
    col11 TEXT, col12 TEXT, col13 TEXT, col14 TEXT, col15 TEXT, col16 TEXT
);

-- Load data as text
\copy temp_monthly_data FROM '/Users/adamsussman/Documents/606_app/local_dev/monthly_data.csv' WITH CSV HEADER;

-- Insert into real table (map columns by position, handle decimal values)
INSERT INTO monthly_data (day, market_participant, tape_a_shares, tape_b_shares, tape_c_shares, total_shares, tape_a_notional, tape_b_notional, tape_c_notional, total_notional, tape_a_trade_count, tape_b_trade_count, tape_c_trade_count, total_trade_count)
SELECT 
    col2::DATE as day,
    col3 as market_participant,
    col4::NUMERIC::BIGINT as tape_a_shares,
    col5::NUMERIC::BIGINT as tape_b_shares,
    col6::NUMERIC::BIGINT as tape_c_shares,
    col7::NUMERIC::BIGINT as total_shares,
    col8::NUMERIC as tape_a_notional,
    col9::NUMERIC as tape_b_notional,
    col10::NUMERIC as tape_c_notional,
    col11::NUMERIC as total_notional,
    col12::INTEGER as tape_a_trade_count,
    col13::INTEGER as tape_b_trade_count,
    col14::INTEGER as tape_c_trade_count,
    col15::INTEGER as total_trade_count
FROM temp_monthly_data
WHERE col1 IS NOT NULL AND col1 != 'id'; -- Skip header row

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

-- Create temporary table with exact number of columns (14)
CREATE TEMP TABLE temp_venue_mapping (
    col1 TEXT, col2 TEXT, col3 TEXT, col4 TEXT, col5 TEXT, col6 TEXT, col7 TEXT, col8 TEXT, col9 TEXT, col10 TEXT,
    col11 TEXT, col12 TEXT, col13 TEXT, col14 TEXT
);

-- Load data as text
\copy temp_venue_mapping FROM '/Users/adamsussman/Documents/606_app/local_dev/venue_mapping.csv' WITH CSV HEADER;

-- Insert into real table (map columns by position)
INSERT INTO venue_mapping (canonical_name, mpid, ats_name, executing_bd, venues, market_participant, entity_type, parent_company, is_active, notes)
SELECT 
    col2 as canonical_name,
    col3 as mpid,
    col4 as ats_name,
    col5 as executing_bd,
    col6 as venues,
    col7 as market_participant,
    col8 as entity_type,
    col9 as parent_company,
    CASE WHEN col10 = 't' THEN true ELSE false END as is_active,
    col14 as notes
FROM temp_venue_mapping
WHERE col1 IS NOT NULL AND col1 != 'venue_id'; -- Skip header row

DROP TABLE temp_venue_mapping;

\echo 'Venue mapping data loaded: ' || (SELECT COUNT(*) FROM venue_mapping) || ' records'

-- ========================================
-- 5. LOAD REAL 606 DATA
-- ========================================

\echo 'Loading real 606 data from AWS export...'

-- Create temporary table with exact number of columns (26)
CREATE TEMP TABLE temp_executing_bd_606 (
    col1 TEXT, col2 TEXT, col3 TEXT, col4 TEXT, col5 TEXT, col6 TEXT, col7 TEXT, col8 TEXT, col9 TEXT, col10 TEXT,
    col11 TEXT, col12 TEXT, col13 TEXT, col14 TEXT, col15 TEXT, col16 TEXT, col17 TEXT, col18 TEXT, col19 TEXT, col20 TEXT,
    col21 TEXT, col22 TEXT, col23 TEXT, col24 TEXT, col25 TEXT, col26 TEXT
);

-- Load data as text (handles empty strings and variable columns)
\copy temp_executing_bd_606 FROM '/Users/adamsussman/Documents/606_app/local_dev/executing_bd_606.csv' WITH CSV HEADER;

-- Insert into real table (map columns by position, handle empty strings and data_type constraint)
INSERT INTO executing_bd_606 (executing_bd, venues, stock_group, marketablelimitpct, nonmarketablelimitpct, otherpct, netpmtpaidrecvmarketordersusd, netpmtpaidrecvmarketorderscph, netpmtpaidrecvmarketablelimitordersusd, netpmtpaidrecvmarketablelimitorderscph, netpmtpaidrecvnonmarketablelimitordersusd, netpmtpaidrecvnonmarketablelimitorderscph, netpmtpaidrecvotherordersusd, netpmtpaidrecvotherorderscph, materialaspects, month, year, data_type, ndopct, ndomarketpct, ndomarketablelimitpct, ndononmarketablelimitpct, ndootherpct, orderpct, marketpct)
SELECT 
    col1 as executing_bd,
    col2 as venues,
    col3 as stock_group,
    CASE WHEN col4 = '' OR col4 IS NULL THEN NULL ELSE col4::NUMERIC END as marketablelimitpct,
    CASE WHEN col5 = '' OR col5 IS NULL THEN NULL ELSE col5::NUMERIC END as nonmarketablelimitpct,
    CASE WHEN col6 = '' OR col6 IS NULL THEN NULL ELSE col6::NUMERIC END as otherpct,
    CASE WHEN col7 = '' OR col7 IS NULL THEN NULL ELSE col7::NUMERIC END as netpmtpaidrecvmarketordersusd,
    CASE WHEN col8 = '' OR col8 IS NULL THEN NULL ELSE col8::NUMERIC END as netpmtpaidrecvmarketorderscph,
    CASE WHEN col9 = '' OR col9 IS NULL THEN NULL ELSE col9::NUMERIC END as netpmtpaidrecvmarketablelimitordersusd,
    CASE WHEN col10 = '' OR col10 IS NULL THEN NULL ELSE col10::NUMERIC END as netpmtpaidrecvmarketablelimitorderscph,
    CASE WHEN col11 = '' OR col11 IS NULL THEN NULL ELSE col11::NUMERIC END as netpmtpaidrecvnonmarketablelimitordersusd,
    CASE WHEN col12 = '' OR col12 IS NULL THEN NULL ELSE col12::NUMERIC END as netpmtpaidrecvnonmarketablelimitorderscph,
    CASE WHEN col13 = '' OR col13 IS NULL THEN NULL ELSE col13::NUMERIC END as netpmtpaidrecvotherordersusd,
    CASE WHEN col14 = '' OR col14 IS NULL THEN NULL ELSE col14::NUMERIC END as netpmtpaidrecvotherorderscph,
    col15 as materialaspects,
    col16 as month,
    col17::INTEGER as year,
    CASE WHEN col19 = 'ndo' THEN 'venue' ELSE col19 END as data_type, -- Map 'ndo' to 'venue' to satisfy constraint
    CASE WHEN col20 = '' OR col20 IS NULL THEN NULL ELSE col20::NUMERIC END as ndopct,
    CASE WHEN col21 = '' OR col21 IS NULL THEN NULL ELSE col21::NUMERIC END as ndomarketpct,
    CASE WHEN col22 = '' OR col22 IS NULL THEN NULL ELSE col22::NUMERIC END as ndomarketablelimitpct,
    CASE WHEN col23 = '' OR col23 IS NULL THEN NULL ELSE col23::NUMERIC END as ndononmarketablelimitpct,
    CASE WHEN col24 = '' OR col24 IS NULL THEN NULL ELSE col24::NUMERIC END as ndootherpct,
    CASE WHEN col25 = '' OR col25 IS NULL THEN NULL ELSE col25::NUMERIC END as orderpct,
    CASE WHEN col26 = '' OR col26 IS NULL THEN NULL ELSE col26::NUMERIC END as marketpct
FROM temp_executing_bd_606
WHERE col1 IS NOT NULL AND col1 != 'executing_bd'; -- Skip header row

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
