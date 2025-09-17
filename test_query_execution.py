#!/usr/bin/env python3
"""
Test script to run actual queries through the full pipeline
"""

import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables from parent directory
parent_dir = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.query import run_query_from_nl

def test_query_execution():
    """Test actual query execution through the full pipeline"""
    
    test_cases = [
        {
            "question": "calcluate volume for Robinhood in SP500 stocks in 2024?",
            "description": "Payment-to-CPH ratio with SP500 and year",
            "expected_route": "Custom SQL"
        },
    
        {
            "question": "Show me the volume for each broker",
            "description": "Volume estimation query",
            "expected_route": "Custom SQL"
        },
        {
            "question": "What is the total PFOF for 2024?",
            "description": "Regular PFOF query (should go to OpenAI)",
            "expected_route": "OpenAI"
        }
    ]
    
    print("🚀 Testing Full Query Execution Pipeline")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Question: {test_case['question']}")
        print(f"   Expected Route: {test_case['expected_route']}")
        print("-" * 50)
        
        try:
            # Run the query through the full pipeline
            result = run_query_from_nl(test_case['question'])
            
            # Check if there was an error
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
                continue
            
            # Display the SQL that was executed
            if 'sql' in result:
                print(f"   📝 SQL Executed:")
                print("   " + "="*40)
                # Show first few lines of SQL
                sql_lines = result['sql'].strip().split('\n')
                for line in sql_lines[:10]:  # Show first 10 lines
                    print("   " + line)
                if len(sql_lines) > 10:
                    print("   ... (truncated)")
                print("   " + "="*40)
            
            # Display results
            if 'results' in result:
                results = result['results']
                print(f"   📊 Results: {len(results)} rows returned")
                
                if results:
                    # Show first few rows
                    print("   Sample Results:")
                    for j, row in enumerate(results[:3]):  # Show first 3 rows
                        print(f"   Row {j+1}: {row}")
                    if len(results) > 3:
                        print(f"   ... and {len(results) - 3} more rows")
                else:
                    print("   No results returned")
            
            print(f"   ✅ Query executed successfully")
            
        except Exception as e:
            print(f"   ❌ Exception during execution: {e}")
            import traceback
            traceback.print_exc()

def test_specific_scenarios():
    """Test specific scenarios that might be problematic"""
    
    print("\n\n🔍 Testing Specific Scenarios")
    print("=" * 60)
    
    scenarios = [
        {
            "question": "Show me all executing brokers",
            "description": "Simple broker list query"
        },
        {
            "question": "What is the payment to cph ratio for TD Ameritrade in 2024?",
            "description": "Broker-specific ratio with year"
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['description']}")
        print(f"   Question: {scenario['question']}")
        print("-" * 50)
        
        try:
            result = run_query_from_nl(scenario['question'])
            
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                print(f"   ✅ Success: {len(result.get('results', []))} rows")
                if result.get('results'):
                    print(f"   Sample: {result['results'][0]}")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def test_database_connection():
    """Test if database connection is working"""
    
    print("\n\n🔌 Testing Database Connection")
    print("=" * 60)
    
    try:
        from app.db import get_db_connection
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Simple test query
        cur.execute("SELECT COUNT(*) FROM executing_bd_606 LIMIT 1")
        count = cur.fetchone()[0]
        
        print(f"   ✅ Database connection successful")
        print(f"   📊 Total rows in executing_bd_606: {count}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")

if __name__ == "__main__":
    print("🧪 Starting Full Query Execution Tests")
    print("=" * 60)
    
    try:
        # Test database connection first
        test_database_connection()
        
        # Run main query tests
        test_query_execution()
        
        # Test specific scenarios
        test_specific_scenarios()
        
        print("\n\n✅ All execution tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
