#!/usr/bin/env python3
"""
Optimized script to load CSV data into the monthly_data table.
Processes files in smaller batches with progress feedback.
"""

import os
import pandas as pd
from datetime import datetime
from db import get_db_connection

def load_csv_data_batch():
    """Load data from CSV files in optimized batches"""
    monthly_data_path = "/Users/adamsussman/Documents/606_app/app/OneDrive_1_9-19-2025/Monthly Data"
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get list of CSV files
        csv_files = [f for f in os.listdir(monthly_data_path) if f.endswith('.csv')]
        csv_files.sort()
        
        print(f"📁 Found {len(csv_files)} CSV files to process")
        
        total_rows_loaded = 0
        batch_size = 1000  # Process 1000 rows at a time
        
        for i, csv_file in enumerate(csv_files, 1):
            file_path = os.path.join(monthly_data_path, csv_file)
            print(f"📄 Processing {csv_file} ({i}/{len(csv_files)})...")
            
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Clean column names to match database schema
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            # Add created_at timestamp
            df['created_at'] = datetime.now()
            
            # Process in batches
            rows_processed = 0
            for start_idx in range(0, len(df), batch_size):
                end_idx = min(start_idx + batch_size, len(df))
                batch_df = df.iloc[start_idx:end_idx]
                
                # Prepare data for insertion
                data_tuples = []
                for _, row in batch_df.iterrows():
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
                
                cur.executemany(insert_sql, data_tuples)
                rows_processed += len(data_tuples)
                
                # Commit every batch
                conn.commit()
                
                if rows_processed % 5000 == 0:
                    print(f"   📊 Processed {rows_processed:,} rows so far...")
            
            total_rows_loaded += rows_processed
            print(f"   ✅ Loaded {rows_processed:,} rows from {csv_file}")
        
        print(f"🎉 Successfully loaded {total_rows_loaded:,} total rows into monthly_data table")
        
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
        cur.execute("SELECT day, market_participant, total_shares FROM monthly_data ORDER BY day DESC LIMIT 5;")
        sample_data = cur.fetchall()
        
        print(f"\n📋 Sample data (latest 5 rows):")
        for row in sample_data:
            print(f"   {row[0]} | {row[1]} | {row[2]:,} shares")
            
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
    finally:
        cur.close()
        conn.close()

def main():
    """Main function to load data"""
    print("🚀 Starting monthly data loading...")
    
    try:
        # Load data
        print("\n📥 Loading CSV data...")
        load_csv_data_batch()
        
        # Verify data
        print("\n🔍 Verifying data...")
        verify_data()
        
        print("\n✅ Monthly data loading completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Process failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
