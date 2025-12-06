#!/usr/bin/env python3
"""Fix corrupted feedback CSV file."""

import pandas as pd
import csv
import shutil
from pathlib import Path

csv_path = Path(__file__).parent.parent / "query_feedback.csv"
backup_path = Path(__file__).parent.parent / "query_feedback.csv.backup"

# Backup
if csv_path.exists():
    shutil.copy(csv_path, backup_path)
    print(f"✅ Backed up to: {backup_path}")

# Schema
columns = ['timestamp', 'question', 'sql_query', 'query_type', 'sql_results_count',
           'genai_response', 'semantic_hints', 'query_notes', 'genai_notes', 'rating']

# Try to salvage or create new
try:
    df = pd.read_csv(csv_path, on_bad_lines='skip', engine='python')
    print(f"Salvaged {len(df)} rows")
    if 'semantic_hints' not in df.columns:
        df['semantic_hints'] = False
    df = df[columns]
except:
    print("Creating new CSV...")
    df = pd.DataFrame(columns=columns)

# Write with proper quoting
df.to_csv(csv_path, index=False, quoting=csv.QUOTE_ALL)
print(f"✅ Fixed: {len(df)} rows")

# Verify
df_check = pd.read_csv(csv_path)
print(f"✅ Verified: {len(df_check)} rows, {len(df_check.columns)} columns")
