#!/usr/bin/env python3
"""
Test script to verify query tagging and routing logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.query_framework import classify_query, generate_volume_estimation_query

def test_classification():
    """Test the query classification logic"""
    test_cases = [
        # Combined metric queries
        "What is the payment to cph ratio for SP500 stocks?",
        "Calculate the ratio of payment to cph for 2024",
        "Divide payment by cph for all brokers",
        "Show me payment over cph ratio",
        
        # Zero PFOF queries
        "Which brokers received no PFOF?",
        "Show brokers with zero flow",
        "Who got not paid for order flow?",
        "List brokers who received no payment",
        
        # Volume queries
        "What is the volume for each broker?",
        "How many trades did each broker handle?",
        "Show me the number of trades by broker",
        
        # Regular queries (should go to OpenAI)
        "What is the total PFOF for 2024?",
        "Which broker had the highest payment?",
        "Show me all executing brokers",
        
        # Broker-specific queries
        "What is the payment to cph ratio for Charles Schwab?",
        "Show volume for Fidelity",
        "Which brokers received no PFOF except for TD Ameritrade?",
    ]
    
    print("🧪 Testing Query Classification")
    print("=" * 50)
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n{i}. Question: {question}")
        tags = classify_query(question)
        
        # Determine expected routing
        if tags.get("mentions_volume"):
            expected_route = "🔁 Custom: Volume Estimation Query"
        else:
            expected_route = "🧠 OpenAI: Natural Language to SQL"
        
        print(f"   Expected Route: {expected_route}")
        print(f"   Tags: {tags}")
        
        # Show which custom query would be generated
        if tags.get("mentions_volume"):
            year = tags.get("year", 2024)
            stock_group = tags.get("stock_group", "SP500")
            executing_bd = tags.get("executing_bd")
            sql = generate_volume_estimation_query(year=year, stock_group=stock_group, executing_bd=executing_bd)
            print(f"   Generated SQL Preview: {sql[:100]}...")

def test_custom_queries():
    """Test the custom query generation functions"""
    print("\n\n🔧 Testing Custom Query Generation")
    print("=" * 50)
    
    # Test volume estimation query
    print("\n1. Volume Estimation Query (SP500, 2024):")
    sql = generate_volume_estimation_query(year=2024, stock_group='SP500')
    print(sql[:200] + "..." if len(sql) > 200 else sql)
    
    # Test with specific broker
    print("\n2. Volume Estimation Query (SP500, 2024, Charles Schwab):")
    sql = generate_volume_estimation_query(year=2024, stock_group='SP500', executing_bd='Charles Schwab')
    print(sql[:200] + "..." if len(sql) > 200 else sql)

def test_broker_aliases():
    """Test broker alias resolution"""
    print("\n\n🏢 Testing Broker Alias Resolution")
    print("=" * 50)
    
    from app.query_framework import load_broker_aliases, resolve_executing_bd
    
    alias_map = load_broker_aliases()
    print(f"Loaded {len(alias_map)} broker aliases")
    
    test_phrases = [
        "What is the payment to cph ratio for Charles Schwab?",
        "Show me volume for Fidelity",
        "Which brokers received no PFOF except for TD Ameritrade?",
        "Calculate ratio for E*TRADE",
        "Show data for Interactive Brokers",
    ]
    
    for phrase in test_phrases:
        resolved = resolve_executing_bd(phrase, alias_map)
        print(f"'{phrase}' -> Resolved broker: '{resolved}'")

if __name__ == "__main__":
    print("🚀 Starting Query Framework Tests")
    print("=" * 60)
    
    try:
        test_classification()
        test_custom_queries()
        test_broker_aliases()
        
        print("\n\n✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
