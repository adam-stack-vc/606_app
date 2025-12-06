#!/usr/bin/env python3
"""
Test semantic hints functionality
"""

import requests
import json

API_URL = "http://localhost:8000/ask"

def test_query(question, use_semantic_hints):
    """Test a query with or without semantic hints"""
    print(f"\n{'='*80}")
    print(f"Question: {question}")
    print(f"Semantic Hints: {use_semantic_hints}")
    print(f"{'='*80}")

    response = requests.post(
        API_URL,
        json={"question": question, "use_semantic_hints": use_semantic_hints},
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\nSQL Query:")
        print(data.get('sql', 'No SQL generated'))
        print(f"\nSemantic Hints Used: {data.get('semantic_hints_used', 'N/A')}")
        print(f"Query Type: {data.get('query_type', 'N/A')}")
        print(f"Results Count: {len(data.get('results', []))}")

        if data.get('results'):
            print(f"\nFirst Result:")
            print(json.dumps(data['results'][0], indent=2))

        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    # Test 1: Simple query without semantic hints
    test_query("PFOF for Robinhood in April 2024", use_semantic_hints=False)

    # Test 2: Same query with semantic hints
    test_query("PFOF for Robinhood in April 2024", use_semantic_hints=True)

    # Test 3: Complex query with superlatives (should benefit from semantic hints)
    test_query("What venue received the highest volume in 2024?", use_semantic_hints=False)
    test_query("What venue received the highest volume in 2024?", use_semantic_hints=True)

    print(f"\n{'='*80}")
    print("Tests complete!")
    print(f"{'='*80}\n")
