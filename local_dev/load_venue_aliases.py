#!/usr/bin/env python3
"""
Script to load venue aliases from JSON file into the venue_mapping database table.
"""

import json
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_venue_aliases_to_db():
    """Load venue aliases from JSON file into database table."""
    
    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 5432),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cursor = conn.cursor()
    
    try:
        # Load JSON file
        with open("venue_aliases.json", "r") as f:
            venue_data = json.load(f)
        
        # Get venue_map from JSON
        venue_map = venue_data.get("venue_map", {})
        
        # Clear existing data
        cursor.execute("DELETE FROM venue_mapping")
        
        # Insert venue aliases
        insert_count = 0
        for canonical_name, aliases in venue_map.items():
            for alias in aliases:
                try:
                    cursor.execute(
                        "INSERT INTO venue_mapping (canonical_name, alias) VALUES (%s, %s)",
                        (canonical_name, alias)
                    )
                    insert_count += 1
                except psycopg2.IntegrityError:
                    # Skip duplicates
                    pass
        
        # Commit changes
        conn.commit()
        
        print(f"✅ Successfully loaded {insert_count} venue aliases into database")
        
        # Show some examples
        cursor.execute("SELECT canonical_name, alias FROM venue_mapping WHERE alias ILIKE '%citadel%' LIMIT 5")
        examples = cursor.fetchall()
        print("\nExample Citadel aliases:")
        for canonical, alias in examples:
            print(f"  {alias} → {canonical}")
            
    except Exception as e:
        print(f"❌ Error loading venue aliases: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    load_venue_aliases_to_db()
