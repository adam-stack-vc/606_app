# Venue Mapping System - Complete Guide

**Database:** `postgres` on app606-cluster  
**Purpose:** Unified lookup table for trading venues across multiple data sources

---

## 📊 Tables Created

### 1. `finra_ats` (Data Table)
Contains quarterly ATS trading data from FINRA

**Columns:**
- quarter, year, tier, ats_name, total_trades, total_shares, **mpid**

### 2. `venue_mapping` (Main Reference Table)
Maps one venue to all its identifiers across different systems

**Columns:**
- `venue_id` (primary key)
- `canonical_name` - Preferred/official name
- **`mpid`** - Links to finra_ats
- **`ats_name`** - Links to finra_ats  
- **`executing_bd`** - Links to executing_bd_606
- **`venues`** - Links to executing_bd_606
- **`market_participant`** - Links to monthly_data
- `aliases` - JSONB array of all aliases
- `entity_type`, `parent_company`, metadata fields

### 3. `venue_aliases` (Normalized Alias Table)
Maps multiple aliases to one venue (many-to-one relationship)

**Columns:**
- `alias_id` (primary key)
- `venue_id` (foreign key to venue_mapping)
- `alias` - The alternate name
- `alias_type` - Type of alias

---

## 🔄 How the Tables Work Together

```
venue_aliases.json (180 venues, 500+ aliases)
    ↓
venue_mapping (canonical names + identifiers)
    ↓
venue_aliases (individual aliases) → links back to venue_mapping
    ↓
finra_ats (trading data) - joined via MPID
executing_bd_606 - joined via executing_bd or venues  
monthly_data - joined via market_participant
```

### Example: "Goldman Sachs"

**venue_mapping row:**
```
venue_id: 42
canonical_name: "Goldman Sachs & Co."
mpid: "GSCO"
ats_name: "SIGMA X2"
aliases: ["goldman", "goldman sachs", "gs"]
```

**venue_aliases rows:**
```
alias_id: 101, venue_id: 42, alias: "goldman"
alias_id: 102, venue_id: 42, alias: "goldman sachs"  
alias_id: 103, venue_id: 42, alias: "gs"
```

**Usage:**
```sql
-- Search by any alias
SELECT * FROM venue_aliases WHERE alias = 'goldman';
-- Returns venue_id: 42

-- Get all identifiers
SELECT * FROM venue_mapping WHERE venue_id = 42;
-- Returns MPID, ATS name, etc.

-- Get trading data
SELECT * FROM finra_ats WHERE mpid = 'GSCO';
-- Returns all quarterly data for Goldman
```

---

## 🚀 Installation Methods

### Method 1: Python Script (Recommended - All-in-One)

```bash
cd /Users/adamsussman/Documents/606_app/aws_app

# Install psycopg2 if needed
pip3 install psycopg2-binary

# Run the loader
python3 load_venue_data.py --password YOUR_PASSWORD

# Or set password as environment variable
export PGPASSWORD=your_password
python3 load_venue_data.py
```

This will:
1. Create finra_ats table ✅
2. Load 998 rows from finra_ats.csv ✅
3. Create venue_mapping table ✅
4. Create venue_aliases table ✅
5. Load 180 venues from venue_aliases.json ✅
6. Cross-reference MPIDs ✅
7. Show summary statistics ✅

### Method 2: Manual SQL (Step-by-step)

```bash
# Step 1: Load FINRA ATS data
psql -h app606-cluster.cluster-cpsacm6ee9zo.us-east-1.rds.amazonaws.com \
     -U postgres -d postgres \
     -f upload_finra_ats_interactive.sql

# Step 2: Create venue mapping tables
psql -h app606-cluster.cluster-cpsacm6ee9zo.us-east-1.rds.amazonaws.com \
     -U postgres -d postgres \
     -f create_venue_mapping_with_aliases.sql

# Step 3: Load aliases (requires Python script)
python3 load_venue_data.py --password YOUR_PASSWORD
```

---

## 🔍 Helper Functions Created

### `find_venue_by_alias(search_term)`
Find a venue by any alias, canonical name, or MPID

```sql
-- Examples:
SELECT * FROM find_venue_by_alias('goldman');
SELECT * FROM find_venue_by_alias('GSCO');
SELECT * FROM find_venue_by_alias('ubs');

-- Returns: venue_id, canonical_name, matched_alias, mpid
```

### `get_venue_identifiers(search_term)`
Get ALL identifiers for a venue across all tables

```sql
-- Example:
SELECT * FROM get_venue_identifiers('citadel');

-- Returns all identifiers:
-- canonical_name, mpid, ats_name, executing_bd, venues, 
-- market_participant, all_aliases[]
```

---

## 📈 Example Queries

### Basic Lookups

```sql
-- Find UBS by any alias
SELECT * FROM find_venue_by_alias('ubs');

-- Get all UBS identifiers
SELECT * FROM get_venue_identifiers('ubs');

-- See all aliases for Goldman Sachs
SELECT va.alias 
FROM venue_mapping vm
JOIN venue_aliases va ON vm.venue_id = va.venue_id
WHERE vm.canonical_name LIKE '%Goldman%';
```

### Cross-Table Joins

```sql
-- Get FINRA trading data using an alias
SELECT fa.*
FROM venue_aliases va
JOIN venue_mapping vm ON va.venue_id = vm.venue_id
JOIN finra_ats fa ON vm.mpid = fa.mpid
WHERE va.alias = 'citadel'
  AND fa.year = 2025
ORDER BY fa.quarter DESC;

-- Compare venues across time
SELECT 
    vm.canonical_name,
    fa.year,
    fa.quarter,
    SUM(fa.total_shares) as total_shares
FROM venue_mapping vm
JOIN finra_ats fa ON vm.mpid = fa.mpid
WHERE vm.canonical_name IN ('UBS Securities, LLC ATS', 'Goldman Sachs & Co. LLC SIGMA X2')
GROUP BY vm.canonical_name, fa.year, fa.quarter
ORDER BY fa.year DESC, fa.quarter DESC;
```

### Fuzzy Matching

```sql
-- Find all venues related to "nasdaq"
SELECT DISTINCT vm.canonical_name, vm.mpid
FROM venue_mapping vm
WHERE EXISTS (
    SELECT 1 FROM venue_aliases va 
    WHERE va.venue_id = vm.venue_id 
    AND va.alias LIKE '%nasdaq%'
)
ORDER BY vm.canonical_name;
```

---

## 🔧 Maintenance

### Add New Aliases

```sql
-- Add alias to existing venue
INSERT INTO venue_aliases (venue_id, alias, alias_type)
SELECT venue_id, 'new alias', 'abbreviation'
FROM venue_mapping
WHERE canonical_name = 'UBS Securities, LLC ATS';
```

### Update Cross-References

```sql
-- Add executing_bd mapping
UPDATE venue_mapping
SET executing_bd = 'UBS Financial Services, Inc.'
WHERE canonical_name = 'UBS Securities, LLC ATS';

-- Add market_participant mapping
UPDATE venue_mapping  
SET market_participant = 'UBS Securities LLC'
WHERE canonical_name = 'UBS Securities, LLC ATS';
```

---

## 📁 Files

✅ **`finra_ats.csv`** - Source data (998 rows, Q1 2022 - Q2 2025)
✅ **`venue_aliases.json`** - Alias mappings (180 venues, 500+ aliases)
✅ **`create_venue_mapping_with_aliases.sql`** - Table schemas
✅ **`upload_finra_ats_interactive.sql`** - FINRA data loader
✅ **`load_venue_data.py`** - Python all-in-one loader
✅ **`VENUE_MAPPING_GUIDE.md`** - This guide

---

## ✨ Benefits

✅ **Unified Reference**
   - One canonical name per venue
   - All identifiers in one place
   - Works across all your tables

✅ **Flexible Matching**
   - Find by any alias ("ubs", "goldman", "citadel")
   - Fuzzy matching for variations
   - Case-insensitive searches

✅ **Easy Joins**
   - Use MPID to join finra_ats
   - Use executing_bd for 606 data
   - Use market_participant for monthly data

✅ **Maintainable**
   - Add new aliases easily
   - Update cross-references as needed
   - Full audit trail

---

**Ready to load!** Run `load_venue_data.py` to set everything up. 🚀



