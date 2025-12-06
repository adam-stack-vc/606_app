#!/usr/bin/env python3
"""
Test full workflow: query -> response -> save feedback
"""

import requests
import pandas as pd
import csv
import os
from datetime import datetime

API_URL = "http://localhost:8000/ask"
FEEDBACK_CSV = "query_feedback_test.csv"

def test_workflow(use_semantic_hints):
    print(f"\n{'='*80}")
    print(f"Testing workflow with semantic_hints={use_semantic_hints}")
    print(f"{'='*80}")

    # Step 1: Call API
    print("\n1. Calling API...")
    response = requests.post(
        API_URL,
        json={"question": "PFOF for Robinhood in April 2024", "use_semantic_hints": use_semantic_hints},
        timeout=30
    )

    if response.status_code != 200:
        print(f"✗ API call failed: {response.status_code}")
        return False

    data = response.json()
    print(f"✓ API call succeeded")
    print(f"  semantic_hints_used: {data.get('semantic_hints_used')}")
    print(f"  query_type: {data.get('query_type')}")

    # Step 2: Simulate saving feedback
    print("\n2. Saving feedback to CSV...")

    feedback_entry = {
        'timestamp': datetime.now().isoformat(),
        'question': data.get('question', 'PFOF for Robinhood in April 2024'),
        'sql_query': data.get('sql', ''),
        'query_type': data.get('query_type', ''),
        'sql_results_count': len(data.get('results', [])),
        'genai_response': data.get('response', ''),
        'semantic_hints': data.get('semantic_hints_used', False),
        'query_notes': 'Test notes',
        'genai_notes': 'Test genai notes',
        'rating': 5
    }

    df = pd.DataFrame([feedback_entry])

    file_exists = os.path.exists(FEEDBACK_CSV)
    if file_exists:
        df.to_csv(FEEDBACK_CSV, mode='a', header=False, index=False, quoting=csv.QUOTE_ALL)
    else:
        df.to_csv(FEEDBACK_CSV, mode='w', header=True, index=False, quoting=csv.QUOTE_ALL)

    print(f"✓ Saved feedback to {FEEDBACK_CSV}")

    # Step 3: Read back and verify
    print("\n3. Reading back CSV...")
    try:
        feedback_df = pd.read_csv(FEEDBACK_CSV)
        print(f"✓ Successfully read {len(feedback_df)} rows")
        print(f"  Columns: {list(feedback_df.columns)}")

        # Check last row
        last_row = feedback_df.iloc[-1]
        print(f"\n  Last row:")
        print(f"    semantic_hints: {last_row['semantic_hints']}")
        print(f"    question: {last_row['question']}")
        print(f"    rating: {last_row['rating']}")

        return True
    except Exception as e:
        print(f"✗ Error reading CSV: {e}")
        return False

# Test with semantic hints off
success1 = test_workflow(False)

# Test with semantic hints on
success2 = test_workflow(True)

print(f"\n{'='*80}")
if success1 and success2:
    print("✓ All tests passed!")
    print(f"\nTest CSV: {FEEDBACK_CSV}")
    print("You can examine this file to verify the format is correct")
else:
    print("✗ Some tests failed")
print(f"{'='*80}\n")
