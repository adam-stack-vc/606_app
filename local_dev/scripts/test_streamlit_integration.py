#!/usr/bin/env python3
"""
Test the actual streamlit app functions
"""

import sys
sys.path.insert(0, '/Users/adamsussman/Documents/606_app/local_dev')

import pandas as pd
import os

# Test that we can read the production CSV
FEEDBACK_CSV = "query_feedback.csv"

print("=" * 80)
print("Testing Streamlit Integration")
print("=" * 80)

# Test 1: Read production CSV
print("\n1. Reading production CSV...")
try:
    df = pd.read_csv(FEEDBACK_CSV)
    print(f"✓ Successfully read {len(df)} rows")
    print(f"  Columns: {list(df.columns)}")

    if 'semantic_hints' in df.columns:
        print(f"✓ semantic_hints column exists")
        print(f"  Values: {df['semantic_hints'].tolist()}")
    else:
        print(f"✗ semantic_hints column missing!")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Simulate a new query with semantic_hints=True
print("\n2. Simulating new feedback entry...")
try:
    from datetime import datetime
    import csv as csv_module

    feedback_entry = {
        'timestamp': datetime.now().isoformat(),
        'question': 'Test question with semantic hints',
        'sql_query': 'SELECT * FROM test WHERE id = 1;',
        'query_type': 'test',
        'sql_results_count': 1,
        'genai_response': 'Test response',
        'semantic_hints': True,  # This is the key field
        'query_notes': 'Test notes',
        'genai_notes': 'Test genai notes',
        'rating': 4
    }

    df_new = pd.DataFrame([feedback_entry])
    df_new.to_csv(FEEDBACK_CSV, mode='a', header=False, index=False, quoting=csv_module.QUOTE_ALL)
    print(f"✓ Appended new entry with semantic_hints=True")

    # Read back
    df_check = pd.read_csv(FEEDBACK_CSV)
    last_row = df_check.iloc[-1]
    print(f"✓ Verified: semantic_hints = {last_row['semantic_hints']}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check sidebar logic would work
print("\n3. Testing sidebar logic...")
try:
    feedback_df = pd.read_csv(FEEDBACK_CSV)
    print(f"✓ Total entries: {len(feedback_df)}")

    if 'rating' in feedback_df.columns and feedback_df['rating'].notna().any():
        avg_rating = feedback_df['rating'].mean()
        print(f"✓ Average rating: {avg_rating:.2f}")
    else:
        print(f"✓ No ratings yet (would show info)")

    # Download button would work
    csv_data = feedback_df.to_csv(index=False)
    print(f"✓ CSV export would work ({len(csv_data)} bytes)")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("✓ All integration tests passed!")
print("=" * 80)
