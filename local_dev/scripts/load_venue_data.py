#!/usr/bin/env python3
"""
Load FINRA ATS and Venue Mapping data to PostgreSQL

This script:
1. Creates finra_ats table and loads data from finra_ats.csv
2. Creates venue_mapping and venue_aliases tables
3. Loads venue_aliases.json into the mapping tables
4. Cross-references MPID data from finra_ats to venue_mapping

Usage:
    python3 load_venue_data.py --password YOUR_PASSWORD
    
Or set PGPASSWORD environment variable:
    export PGPASSWORD=your_password
    python3 load_venue_data.py
"""

import psycopg2
import json
import csv
import argparse
import os
from pathlib import Path

# Configuration
DB_HOST = "app606-cluster.cluster-cpsacm6ee9zo.us-east-1.rds.amazonaws.com"
DB_USER = "postgres"
DB_NAME = "postgres"
DB_PORT = 5432

BASE_DIR = Path(__file__).parent
FINRA_CSV = BASE_DIR / "finra_ats.csv"
VENUE_ALIASES_JSON = BASE_DIR / "venue_aliases.json"

def get_connection(password=None):
    """Create database connection"""
    conn_params = {
        'host': DB_HOST,
        'database': DB_NAME,
        'user': DB_USER,
        'port': DB_PORT
    }
    
    if password:
        conn_params['password'] = password
    elif os.getenv('PGPASSWORD'):
        conn_params['password'] = os.getenv('PGPASSWORD')
    
    return psycopg2.connect(**conn_params)

def create_finra_ats_table(conn):
    """Create finra_ats table"""
    print("\n📋 Creating finra_ats table...")
    
    with conn.cursor() as cur:
        # Drop and create table
        cur.execute("DROP TABLE IF EXISTS finra_ats CASCADE;")
        
        cur.execute("""
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
        """)
        
        # Create indexes
        cur.execute("CREATE INDEX idx_finra_ats_year_quarter ON finra_ats(year, quarter);")
        cur.execute("CREATE INDEX idx_finra_ats_tier ON finra_ats(tier);")
        cur.execute("CREATE INDEX idx_finra_ats_mpid ON finra_ats(mpid);")
        cur.execute("CREATE INDEX idx_finra_ats_ats_name ON finra_ats(ats_name);")
        
        conn.commit()
    
    print("✅ finra_ats table created")

def load_finra_ats_data(conn):
    """Load data from finra_ats.csv"""
    print(f"\n📥 Loading data from {FINRA_CSV}...")
    
    # Use utf-8-sig to handle BOM (Byte Order Mark)
    with open(FINRA_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    with conn.cursor() as cur:
        insert_query = """
            INSERT INTO finra_ats (quarter, year, tier, ats_name, total_trades, total_shares, mpid)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (year, quarter, tier, mpid) DO NOTHING;
        """
        
        for row in rows:
            cur.execute(insert_query, (
                int(row['quarter']),
                int(row['year']),
                row['tier'],
                row['ats_name'],
                float(row['total_trades']),
                float(row['total_shares']),
                row['mpid']
            ))
        
        conn.commit()
    
    print(f"✅ Loaded {len(rows)} rows into finra_ats")

def create_venue_mapping_tables(conn):
    """Create venue_mapping and venue_aliases tables"""
    print("\n📋 Creating venue mapping tables...")
    
    with conn.cursor() as cur:
        # Drop existing tables
        cur.execute("DROP TABLE IF EXISTS venue_aliases CASCADE;")
        cur.execute("DROP TABLE IF EXISTS venue_mapping CASCADE;")
        
        # Create venue_mapping table
        cur.execute("""
            CREATE TABLE venue_mapping (
                venue_id SERIAL PRIMARY KEY,
                canonical_name VARCHAR(255) NOT NULL UNIQUE,
                mpid VARCHAR(10),
                ats_name VARCHAR(255),
                executing_bd VARCHAR(255),
                venues VARCHAR(255),
                market_participant VARCHAR(255),
                entity_type VARCHAR(50),
                parent_company VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                aliases JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            );
        """)
        
        # Create venue_aliases table
        cur.execute("""
            CREATE TABLE venue_aliases (
                alias_id SERIAL PRIMARY KEY,
                venue_id INTEGER NOT NULL REFERENCES venue_mapping(venue_id) ON DELETE CASCADE,
                alias VARCHAR(255) NOT NULL UNIQUE,
                alias_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        cur.execute("CREATE INDEX idx_venue_mapping_mpid ON venue_mapping(mpid) WHERE mpid IS NOT NULL;")
        cur.execute("CREATE INDEX idx_venue_mapping_aliases ON venue_mapping USING gin(aliases);")
        cur.execute("CREATE INDEX idx_venue_aliases_venue_id ON venue_aliases(venue_id);")
        cur.execute("CREATE INDEX idx_venue_aliases_alias_lower ON venue_aliases(LOWER(alias));")
        
        conn.commit()
    
    print("✅ Venue mapping tables created")

def load_venue_aliases_json(conn):
    """Load venue_aliases.json into venue_mapping and venue_aliases tables"""
    print(f"\n📥 Loading venue aliases from {VENUE_ALIASES_JSON}...")
    
    with open(VENUE_ALIASES_JSON, 'r') as f:
        data = json.load(f)
    
    venue_map = data.get('venue_map', {})
    
    with conn.cursor() as cur:
        for canonical_name, aliases_list in venue_map.items():
            # Insert into venue_mapping
            cur.execute("""
                INSERT INTO venue_mapping (canonical_name, aliases)
                VALUES (%s, %s)
                RETURNING venue_id;
            """, (canonical_name, json.dumps(aliases_list)))
            
            venue_id = cur.fetchone()[0]
            
            # Insert each alias into venue_aliases
            for alias in aliases_list:
                cur.execute("""
                    INSERT INTO venue_aliases (venue_id, alias, alias_type)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (alias) DO NOTHING;
                """, (venue_id, alias, 'common_name'))
        
        conn.commit()
    
    print(f"✅ Loaded {len(venue_map)} venues with their aliases")

def cross_reference_mpid(conn):
    """Cross-reference MPID data from finra_ats to venue_mapping"""
    print("\n🔗 Cross-referencing MPID data from finra_ats...")
    
    with conn.cursor() as cur:
        # Get distinct MPID and ATS names from finra_ats
        cur.execute("""
            SELECT DISTINCT mpid, ats_name 
            FROM finra_ats 
            WHERE mpid IS NOT NULL
            ORDER BY mpid;
        """)
        
        finra_data = cur.fetchall()
        
        matched_count = 0
        unmatched_count = 0
        
        for mpid, ats_name in finra_data:
            # Try to find matching venue by name similarity
            cur.execute("""
                SELECT venue_id, canonical_name 
                FROM venue_mapping 
                WHERE LOWER(canonical_name) LIKE %s
                   OR EXISTS (
                       SELECT 1 FROM venue_aliases va 
                       WHERE va.venue_id = venue_mapping.venue_id 
                       AND LOWER(va.alias) LIKE %s
                   )
                LIMIT 1;
            """, (f'%{ats_name.lower()}%', f'%{ats_name.lower()}%'))
            
            result = cur.fetchone()
            
            if result:
                venue_id, canonical = result
                # Update venue_mapping with MPID and ATS name
                cur.execute("""
                    UPDATE venue_mapping 
                    SET mpid = %s, ats_name = %s
                    WHERE venue_id = %s AND mpid IS NULL;
                """, (mpid, ats_name, venue_id))
                matched_count += 1
            else:
                # Create new venue for unmatched ATS
                cur.execute("""
                    INSERT INTO venue_mapping (canonical_name, mpid, ats_name, entity_type)
                    VALUES (%s, %s, %s, 'ATS')
                    ON CONFLICT (canonical_name) DO UPDATE
                    SET mpid = EXCLUDED.mpid, ats_name = EXCLUDED.ats_name;
                """, (ats_name, mpid, ats_name))
                unmatched_count += 1
        
        conn.commit()
    
    print(f"✅ Cross-referenced {matched_count} venues")
    print(f"ℹ️  Created {unmatched_count} new venues (not in aliases)")

def show_statistics(conn):
    """Display summary statistics"""
    print("\n" + "="*70)
    print("UPLOAD SUMMARY")
    print("="*70)
    
    with conn.cursor() as cur:
        # finra_ats stats
        cur.execute("""
            SELECT 
                COUNT(*) as total_rows,
                MIN(year) as earliest_year,
                MAX(year) as latest_year,
                COUNT(DISTINCT mpid) as unique_ats
            FROM finra_ats;
        """)
        stats = cur.fetchone()
        print(f"\n📊 finra_ats table:")
        print(f"   Total rows: {stats[0]}")
        print(f"   Year range: {stats[1]} - {stats[2]}")
        print(f"   Unique ATS: {stats[3]}")
        
        # venue_mapping stats
        cur.execute("""
            SELECT 
                COUNT(*) as total_venues,
                COUNT(mpid) FILTER (WHERE mpid IS NOT NULL) as with_mpid,
                COUNT(DISTINCT entity_type) as entity_types
            FROM venue_mapping;
        """)
        stats = cur.fetchone()
        print(f"\n🏢 venue_mapping table:")
        print(f"   Total venues: {stats[0]}")
        print(f"   With MPID: {stats[1]}")
        print(f"   Entity types: {stats[2]}")
        
        # venue_aliases stats
        cur.execute("SELECT COUNT(*) FROM venue_aliases;")
        alias_count = cur.fetchone()[0]
        print(f"\n🔖 venue_aliases table:")
        print(f"   Total aliases: {alias_count}")
        
        # Sample queries
        print(f"\n📋 Sample venue mappings:")
        cur.execute("""
            SELECT 
                canonical_name,
                mpid,
                entity_type,
                (SELECT COUNT(*) FROM venue_aliases va WHERE va.venue_id = vm.venue_id) as alias_count
            FROM venue_mapping vm
            WHERE mpid IS NOT NULL
            ORDER BY canonical_name
            LIMIT 10;
        """)
        
        for row in cur.fetchall():
            print(f"   • {row[0][:40]:40} | MPID: {row[1]:6} | Aliases: {row[3]}")

def main():
    parser = argparse.ArgumentParser(description='Load FINRA ATS and Venue Mapping data')
    parser.add_argument('--password', help='PostgreSQL password')
    args = parser.parse_args()
    
    print("="*70)
    print("FINRA ATS & Venue Mapping Data Loader")
    print("="*70)
    print(f"Host: {DB_HOST}")
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")
    
    try:
        # Connect to database
        print("\n🔌 Connecting to database...")
        conn = get_connection(args.password)
        print("✅ Connected successfully")
        
        # Step 1: Create and load finra_ats
        create_finra_ats_table(conn)
        load_finra_ats_data(conn)
        
        # Step 2: Create venue mapping tables
        create_venue_mapping_tables(conn)
        
        # Step 3: Load venue aliases from JSON
        load_venue_aliases_json(conn)
        
        # Step 4: Cross-reference MPID data
        cross_reference_mpid(conn)
        
        # Step 5: Show statistics
        show_statistics(conn)
        
        print("\n" + "="*70)
        print("✅ ALL DATA LOADED SUCCESSFULLY!")
        print("="*70)
        print("\n📚 Useful queries:")
        print("   -- Find venue by any alias:")
        print("   SELECT * FROM find_venue_by_alias('goldman');")
        print()
        print("   -- Get all identifiers for UBS:")
        print("   SELECT * FROM get_venue_identifiers('ubs');")
        print()
        print("   -- See all name variants:")
        print("   SELECT * FROM venue_all_names WHERE canonical_name LIKE '%Goldman%';")
        
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

