#!/usr/bin/env python3
"""
Script to create the monthly_data table and load CSV data from Monthly Data folder.
This follows the same pattern as the 606 data table creation.
"""

import os
import pandas as pd
import psycopg2
from datetime import datetime
from db import get_db_connection
import json

def create_table():
    """Create the monthly_data table based on the schema"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Drop table if it exists
        cur.execute("DROP TABLE IF EXISTS monthly_data;")
        
        # Create table based on schema
        create_table_sql = """
        CREATE TABLE monthly_data (
            id SERIAL PRIMARY KEY,
            day DATE NOT NULL,
            market_participant VARCHAR(255) NOT NULL,
            tape_a_shares NUMERIC,
            tape_b_shares NUMERIC,
            tape_c_shares NUMERIC,
            total_shares NUMERIC,
            tape_a_notional NUMERIC,
            tape_b_notional NUMERIC,
            tape_c_notional NUMERIC,
            total_notional NUMERIC,
            tape_a_trade_count NUMERIC,
            tape_b_trade_count NUMERIC,
            tape_c_trade_count NUMERIC,
            total_trade_count NUMERIC,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cur.execute(create_table_sql)
        conn.commit()
        print("✅ Table 'monthly_data' created successfully")
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def load_csv_data():
    """Load data from all CSV files in the Monthly Data folder"""
    monthly_data_path = "/Users/adamsussman/Documents/606_app/app/OneDrive_1_9-19-2025/Monthly Data"
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get list of CSV files
        csv_files = [f for f in os.listdir(monthly_data_path) if f.endswith('.csv')]
        csv_files.sort()  # Process in order
        
        print(f"📁 Found {len(csv_files)} CSV files to process")
        
        total_rows_loaded = 0
        
        for csv_file in csv_files:
            file_path = os.path.join(monthly_data_path, csv_file)
            print(f"📄 Processing {csv_file}...")
            
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Clean column names to match database schema
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            # Add created_at timestamp
            df['created_at'] = datetime.now()
            
            # Prepare data for insertion
            insert_sql = """
            INSERT INTO monthly_data (
                day, market_participant, tape_a_shares, tape_b_shares, tape_c_shares,
                total_shares, tape_a_notional, tape_b_notional, tape_c_notional,
                total_notional, tape_a_trade_count, tape_b_trade_count, tape_c_trade_count,
                total_trade_count, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            # Convert DataFrame to list of tuples for batch insert
            data_tuples = []
            for _, row in df.iterrows():
                data_tuples.append((
                    pd.to_datetime(row['day']).date() if pd.notna(row['day']) else None,
                    row['market_participant'] if pd.notna(row['market_participant']) else None,
                    row['tape_a_shares'] if pd.notna(row['tape_a_shares']) else None,
                    row['tape_b_shares'] if pd.notna(row['tape_b_shares']) else None,
                    row['tape_c_shares'] if pd.notna(row['tape_c_shares']) else None,
                    row['total_shares'] if pd.notna(row['total_shares']) else None,
                    row['tape_a_notional'] if pd.notna(row['tape_a_notional']) else None,
                    row['tape_b_notional'] if pd.notna(row['tape_b_notional']) else None,
                    row['tape_c_notional'] if pd.notna(row['tape_c_notional']) else None,
                    row['total_notional'] if pd.notna(row['total_notional']) else None,
                    row['tape_a_trade_count'] if pd.notna(row['tape_a_trade_count']) else None,
                    row['tape_b_trade_count'] if pd.notna(row['tape_b_trade_count']) else None,
                    row['tape_c_trade_count'] if pd.notna(row['tape_c_trade_count']) else None,
                    row['total_trade_count'] if pd.notna(row['total_trade_count']) else None,
                    row['created_at']
                ))
            
            # Execute batch insert
            cur.executemany(insert_sql, data_tuples)
            rows_loaded = len(data_tuples)
            total_rows_loaded += rows_loaded
            print(f"   ✅ Loaded {rows_loaded} rows from {csv_file}")
        
        conn.commit()
        print(f"🎉 Successfully loaded {total_rows_loaded} total rows into monthly_data table")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def verify_data():
    """Verify the data was loaded correctly"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get basic statistics
        cur.execute("SELECT COUNT(*) FROM monthly_data;")
        total_rows = cur.fetchone()[0]
        
        cur.execute("SELECT MIN(day), MAX(day) FROM monthly_data;")
        date_range = cur.fetchone()
        
        cur.execute("SELECT COUNT(DISTINCT market_participant) FROM monthly_data;")
        unique_participants = cur.fetchone()[0]
        
        print(f"\n📊 Data Verification:")
        print(f"   Total rows: {total_rows:,}")
        print(f"   Date range: {date_range[0]} to {date_range[1]}")
        print(f"   Unique market participants: {unique_participants}")
        
        # Show sample data
        cur.execute("SELECT * FROM monthly_data ORDER BY day DESC LIMIT 5;")
        sample_data = cur.fetchall()
        
        print(f"\n📋 Sample data (latest 5 rows):")
        for row in sample_data:
            print(f"   {row[1]} | {row[2]} | {row[4]:,} shares")
            
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
    finally:
        cur.close()
        conn.close()

def main():
    """Main function to create table and load data"""
    print("🚀 Starting monthly data table creation and data loading...")
    
    try:
        # Step 1: Create table
        print("\n1️⃣ Creating table...")
        create_table()
        
        # Step 2: Load data
        print("\n2️⃣ Loading CSV data...")
        load_csv_data()
        
        # Step 3: Verify data
        print("\n3️⃣ Verifying data...")
        verify_data()
        
        print("\n✅ Monthly data table creation and loading completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Process failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
