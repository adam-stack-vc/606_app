#!/usr/bin/env python3
"""
Test CSV reading and migration with the streamlit app
"""

import pandas as pd
import os
import csv as csv_module

FEEDBACK_CSV = "query_feedback.csv"

# Test 1: Try to read the current CSV
print("=" * 80)
print("Test 1: Read current CSV")
print("=" * 80)

try:
    df = pd.read_csv(FEEDBACK_CSV)
    print(f"✓ Successfully read CSV with {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst row:")
    print(df.iloc[0] if len(df) > 0 else "No data")
except Exception as e:
    print(f"✗ Error reading CSV: {e}")

# Test 2: Check header
print("\n" + "=" * 80)
print("Test 2: Check header structure")
print("=" * 80)

try:
    with open(FEEDBACK_CSV, 'r') as f:
        header = f.readline().strip()
        print(f"Header: {header}")
        cols = header.count(',') + 1
        print(f"Number of columns in header: {cols}")
except Exception as e:
    print(f"✗ Error reading header: {e}")

# Test 3: Check first data row
print("\n" + "=" * 80)
print("Test 3: Check first data row")
print("=" * 80)

try:
    with open(FEEDBACK_CSV, 'r') as f:
        f.readline()  # skip header
        first_row = f.readline().strip()
        # Count fields properly with CSV reader
        import csv
        reader = csv.reader([first_row])
        fields = next(reader)
        print(f"Number of fields in first row: {len(fields)}")
        for i, field in enumerate(fields):
            print(f"  Field {i}: {field[:50]}..." if len(field) > 50 else f"  Field {i}: {field}")
except Exception as e:
    print(f"✗ Error reading first row: {e}")

# Test 4: Migration logic
print("\n" + "=" * 80)
print("Test 4: Test migration logic")
print("=" * 80)

try:
    existing_df = pd.read_csv(FEEDBACK_CSV, nrows=0)
    print(f"Columns in existing file: {list(existing_df.columns)}")

    if 'semantic_hints' not in existing_df.columns:
        print("⚠ Migration needed: 'semantic_hints' column missing")

        # Read full file
        old_df = pd.read_csv(FEEDBACK_CSV)
        print(f"Read {len(old_df)} rows from old format")

        # Add semantic_hints column
        old_df['semantic_hints'] = False
        print("Added 'semantic_hints' column with default False")

        # Reorder columns
        column_order = ['timestamp', 'question', 'sql_query', 'query_type', 'sql_results_count',
                      'genai_response', 'semantic_hints', 'query_notes', 'genai_notes', 'rating']
        old_df = old_df[column_order]
        print(f"Reordered columns: {list(old_df.columns)}")

        # Write to backup first
        backup_file = FEEDBACK_CSV.replace('.csv', '_backup_test.csv')
        old_df.to_csv(backup_file, mode='w', header=True, index=False, quoting=csv_module.QUOTE_ALL)
        print(f"✓ Migration would work - wrote test to {backup_file}")
    else:
        print("✓ No migration needed - 'semantic_hints' column already exists")
except Exception as e:
    print(f"✗ Migration test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Tests complete")
print("=" * 80)
