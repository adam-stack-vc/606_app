#!/usr/bin/env python3
"""
Test script to test individual components of the query system
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from parent directory
parent_dir = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_classification_component():
    """Test just the classification component"""
    print("🏷️  Testing Classification Component")
    print("=" * 50)
    
    from app.query_framework import classify_query
    
    test_questions = [
        "What is the payment to cph ratio?",
        "Which brokers received no PFOF?",
        "Show me the volume for each broker",
        "What is the total PFOF for 2024?",
        "Calculate ratio for Charles Schwab"
    ]
    
    for question in test_questions:
        tags = classify_query(question)
        print(f"Q: {question}")
        print(f"  Tags: {tags}")
        print()

def test_sql_generation_component():
    """Test just the SQL generation component"""
    print("🔧 Testing SQL Generation Component")
    print("=" * 50)
    
    from app.query_framework import (
        generate_volume_estimation_query
    )
    
    # Test different parameter combinations
    test_cases = [
        {
            "name": "Volume Estimation (default)",
            "func": generate_volume_estimation_query,
            "args": {}
        },
        {
            "name": "Volume Estimation (with broker)",
            "func": generate_volume_estimation_query,
            "args": {"executing_bd": "Charles Schwab"}
        }
    ]
    
    for test_case in test_cases:
        print(f"{test_case['name']}:")
        sql = test_case['func'](**test_case['args'])
        print(f"  SQL Length: {len(sql)} characters")
        print(f"  First 100 chars: {sql[:100]}...")
        print()

def test_broker_resolution_component():
    """Test just the broker resolution component"""
    print("🏢 Testing Broker Resolution Component")
    print("=" * 50)
    
    from app.query_framework import load_broker_aliases, resolve_executing_bd
    
    alias_map = load_broker_aliases()
    print(f"Loaded {len(alias_map)} broker alias groups")
    
    test_phrases = [
        "Charles Schwab",
        "schwab",
        "TD Ameritrade",
        "td ameritrade",
        "Fidelity",
        "fidelity",
        "Robinhood",
        "robinhood"
    ]
    
    for phrase in test_phrases:
        resolved = resolve_executing_bd(phrase, alias_map)
        print(f"'{phrase}' -> '{resolved}'")

def test_database_component():
    """Test just the database component"""
    print("🗄️  Testing Database Component")
    print("=" * 50)
    
    try:
        from app.db import get_db_connection
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Test basic connection
        cur.execute("SELECT 1")
        result = cur.fetchone()
        print(f"✅ Basic query: {result}")
        
        # Test table existence
        cur.execute("SELECT COUNT(*) FROM executing_bd_606")
        count = cur.fetchone()[0]
        print(f"✅ Table access: {count} rows in executing_bd_606")
        
        # Test sample data
        cur.execute("SELECT DISTINCT executing_bd FROM executing_bd_606 LIMIT 5")
        brokers = cur.fetchall()
        print(f"✅ Sample brokers: {[b[0] for b in brokers]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def test_openai_component():
    """Test if OpenAI component is accessible"""
    print("🧠 Testing OpenAI Component")
    print("=" * 50)
    
    try:
        from app.query import client
        
        # Check if client is initialized
        if client:
            print("✅ OpenAI client initialized")
            
            # Check API key
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                print("✅ OpenAI API key found")
            else:
                print("❌ OpenAI API key not found")
        else:
            print("❌ OpenAI client not initialized")
            
    except Exception as e:
        print(f"❌ OpenAI component error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Individual Components")
    print("=" * 60)
    
    try:
        test_classification_component()
        test_sql_generation_component()
        test_broker_resolution_component()
        test_database_component()
        test_openai_component()
        
        print("\n✅ All component tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Component tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
