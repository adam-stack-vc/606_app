#!/usr/bin/env python3
"""
Script to populate the entity_types table with data from entity_types.json
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db import get_db_connection

def load_entity_types_data():
    """Load entity types data from JSON file"""
    json_path = os.path.join(os.path.dirname(__file__), 'app', 'entity_types.json')
    with open(json_path, 'r') as f:
        return json.load(f)

def get_parent_organization(venue_name, venue_aliases):
    """Determine parent organization from venue aliases"""
    venue_map = venue_aliases.get('venue_map', {})
    aliases = venue_map.get(venue_name, [])
    
    # Common parent organizations
    parent_mapping = {
        'cboe': 'CBOE',
        'nasdaq': 'Nasdaq', 
        'nyse': 'NYSE',
        'iex': 'IEX',
        'miax': 'MIAX',
        'memx': 'MEMX',
        'citadel': 'Citadel',
        'jane street': 'Jane Street',
        'goldman sachs': 'Goldman Sachs',
        'morgan stanley': 'Morgan Stanley',
        'virtu': 'Virtu',
        'wolverine': 'Wolverine',
        'dash': 'DASH',
        'matrix': 'Matrix',
        'wall street access': 'Wall Street Access',
        'apex': 'Apex',
        'bny': 'BNY Mellon',
        'ubs': 'UBS',
        'citi': 'Citigroup',
        'rbc': 'RBC',
        'credit suisse': 'Credit Suisse'
    }
    
    for alias in aliases:
        for key, parent in parent_mapping.items():
            if key in alias.lower():
                return parent
    
    return None

def populate_entity_types_table():
    """Populate the entity_types table"""
    print("🔄 Loading entity types data...")
    
    # Load data
    entity_data = load_entity_types_data()
    venue_entity_map = entity_data.get('venue_entity_map', {})
    entity_types_info = entity_data.get('entity_types', {})
    
    # Load venue aliases to get parent organizations
    venue_aliases_path = os.path.join(os.path.dirname(__file__), 'app', 'venue_aliases.json')
    with open(venue_aliases_path, 'r') as f:
        venue_aliases = json.load(f)
    
    print(f"📊 Found {len(venue_entity_map)} venues to insert")
    
    # Connect to database
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Clear existing data (optional - remove if you want to keep existing data)
        print("🗑️  Clearing existing entity_types data...")
        cur.execute("DELETE FROM entity_types")
        
        # Insert venue data
        inserted_count = 0
        for venue_name, entity_type in venue_entity_map.items():
            # Get description for entity type
            description = entity_types_info.get(entity_type, {}).get('description', '')
            
            # Get parent organization
            parent_org = get_parent_organization(venue_name, venue_aliases)
            
            # Insert record
            cur.execute("""
                INSERT INTO entity_types (venue_name, entity_type, description, parent_organization)
                VALUES (%s, %s, %s, %s)
            """, (venue_name, entity_type, description, parent_org))
            
            inserted_count += 1
            
            if inserted_count % 20 == 0:
                print(f"📝 Inserted {inserted_count} venues...")
        
        # Commit changes
        conn.commit()
        print(f"✅ Successfully inserted {inserted_count} venues into entity_types table")
        
        # Show summary
        cur.execute("SELECT entity_type, COUNT(*) FROM entity_types GROUP BY entity_type ORDER BY entity_type")
        results = cur.fetchall()
        
        print("\n📈 Entity type distribution:")
        for entity_type, count in results:
            print(f"   {entity_type}: {count} venues")
        
        # Show parent organization distribution
        cur.execute("SELECT parent_organization, COUNT(*) FROM entity_types WHERE parent_organization IS NOT NULL GROUP BY parent_organization ORDER BY COUNT(*) DESC LIMIT 10")
        parent_results = cur.fetchall()
        
        print("\n🏢 Top parent organizations:")
        for parent, count in parent_results:
            print(f"   {parent}: {count} venues")
            
    except Exception as e:
        print(f"❌ Error populating table: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    populate_entity_types_table()
    print("\n🎉 Entity types table population completed!")
