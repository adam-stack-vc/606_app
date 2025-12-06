#!/usr/bin/env python3
"""
Debug script to check database connection and data
"""
import os
from dotenv import load_dotenv
from db import get_db_connection

load_dotenv()

def test_db_connection():
    """Test basic database connectivity"""
    print("=" * 80)
    print("Database Connectivity Test")
    print("=" * 80)
    print()
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Test 1: Basic connection
        print("✅ Database connection successful!")
        print()
        
        # Test 2: Check if table exists
        print("📊 Checking if table exists...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'executing_bd_606'
            );
        """)
        exists = cur.fetchone()[0]
        if exists:
            print("✅ Table 'executing_bd_606' exists")
        else:
            print("❌ Table 'executing_bd_606' does NOT exist!")
            return
        print()
        
        # Test 3: Count total rows
        print("📊 Counting total rows...")
        cur.execute("SELECT COUNT(*) FROM executing_bd_606;")
        total = cur.fetchone()[0]
        print(f"✅ Total rows: {total:,}")
        print()
        
        # Test 4: Check data_type distribution
        print("📊 Checking data_type distribution...")
        cur.execute("""
            SELECT data_type, COUNT(*) as count
            FROM executing_bd_606
            GROUP BY data_type;
        """)
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]:,} rows")
        print()
        
        # Test 5: Check for Robinhood data
        print("📊 Checking for 'Robinhood' data...")
        cur.execute("""
            SELECT COUNT(*) 
            FROM executing_bd_606 
            WHERE executing_bd = 'Robinhood';
        """)
        robinhood_count = cur.fetchone()[0]
        print(f"  Exact match 'Robinhood': {robinhood_count:,} rows")
        
        # Check case-insensitive
        cur.execute("""
            SELECT COUNT(*) 
            FROM executing_bd_606 
            WHERE LOWER(executing_bd) = 'robinhood';
        """)
        robinhood_lower = cur.fetchone()[0]
        print(f"  Case-insensitive 'robinhood': {robinhood_lower:,} rows")
        print()
        
        # Test 6: Show actual executing_bd values
        print("📊 Top 10 executing_bd values...")
        cur.execute("""
            SELECT executing_bd, COUNT(*) as count
            FROM executing_bd_606
            WHERE executing_bd IS NOT NULL AND executing_bd != ''
            GROUP BY executing_bd
            ORDER BY count DESC
            LIMIT 10;
        """)
        for row in cur.fetchall():
            print(f"  '{row[0]}': {row[1]:,} rows")
        print()
        
        # Test 7: Check year distribution
        print("📊 Checking year distribution...")
        cur.execute("""
            SELECT year, COUNT(*) as count
            FROM executing_bd_606
            GROUP BY year
            ORDER BY year DESC;
        """)
        for row in cur.fetchall():
            print(f"  Year {row[0]}: {row[1]:,} rows")
        print()
        
        # Test 8: Check month distribution for 2024
        print("📊 Checking month distribution for 2024...")
        cur.execute("""
            SELECT month, COUNT(*) as count
            FROM executing_bd_606
            WHERE year = 2024
            GROUP BY month
            ORDER BY month;
        """)
        months = cur.fetchall()
        if months:
            for row in months:
                print(f"  Month '{row[0]}': {row[1]:,} rows")
        else:
            print("  ❌ No data for 2024!")
        print()
        
        # Test 9: Try the exact query that's failing
        print("📊 Testing the exact query...")
        cur.execute("""
            SELECT month, 
              SUM(netpmtpaidrecvmarketordersusd) +
              SUM(netpmtpaidrecvmarketablelimitordersusd) +
              SUM(netpmtpaidrecvnonmarketablelimitordersusd) +
              SUM(netpmtpaidrecvotherordersusd) AS total_pf
            FROM executing_bd_606
            WHERE executing_bd = 'Robinhood' 
              AND data_type = 'venue' 
              AND year = 2024 
              AND month IS NOT NULL AND month != ''
              AND netpmtpaidrecvmarketordersusd IS NOT NULL 
              AND netpmtpaidrecvmarketablelimitordersusd IS NOT NULL 
              AND netpmtpaidrecvnonmarketablelimitordersusd IS NOT NULL 
              AND netpmtpaidrecvotherordersusd IS NOT NULL 
            GROUP BY month
            ORDER BY total_pf DESC
            LIMIT 1;
        """)
        result = cur.fetchall()
        if result:
            print(f"✅ Query returned: {result}")
        else:
            print("❌ Query returned empty results")
            
            # Try without some filters
            print("\n📊 Trying simplified query...")
            cur.execute("""
                SELECT COUNT(*) 
                FROM executing_bd_606
                WHERE executing_bd = 'Robinhood' 
                  AND data_type = 'venue' 
                  AND year = 2024;
            """)
            simplified = cur.fetchone()[0]
            print(f"  Robinhood + venue + 2024: {simplified} rows")
        print()
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_connection()

