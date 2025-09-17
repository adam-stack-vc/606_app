#!/usr/bin/env python3
"""
Test script to show actual SQL output for key query types
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.query_framework import classify_query, generate_volume_estimation_query

def test_sql_output():
    """Test and display actual SQL output for key scenarios"""
    
    test_cases = [
        {
            "question": "What is the payment to cph ratio for SP500 stocks in 2024?",
            "description": "Payment-to-CPH ratio with SP500 and year"
        },
        {
            "question": "Show me the volume for each broker",
            "description": "Volume estimation query"
        }
    ]
    
    print("🔍 Testing SQL Output Generation")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Question: {test_case['question']}")
        print("-" * 50)
        
        # Classify the query
        tags = classify_query(test_case['question'])
        print(f"   Tags: {tags}")
        
        # Generate appropriate SQL
        year = tags.get("year", 2024)
        stock_group = tags.get("stock_group", "SP500")
        executing_bd = tags.get("executing_bd")
        
        if tags.get("mentions_volume"):
            sql = generate_volume_estimation_query(year=year, stock_group=stock_group, executing_bd=executing_bd)
            print("   🔁 Generated: Volume Estimation Query")
        else:
            print("   🧠 Would route to: OpenAI")
            continue
        
        print("\n   SQL Output:")
        print("   " + "="*40)
        # Indent each line of SQL for better readability
        for line in sql.strip().split('\n'):
            print("   " + line)
        print("   " + "="*40)

if __name__ == "__main__":
    test_sql_output()
