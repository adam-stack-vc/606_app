#!/usr/bin/env python3
"""
Comprehensive test of query generation with alias resolution
"""
import os
from dotenv import load_dotenv
from query import run_query_from_nl
from db import get_db_connection

load_dotenv()

# Comprehensive test questions
TEST_QUESTIONS = [
    # Basic broker queries
    "Give me a list of all brokers",
    "List all venues",
    
    # Robinhood queries (should resolve to 'Robinhood Securities, LLC')
    "How much PFOF did Robinhood receive in 2024?",
    "What month did Robinhood receive the most PFOF in 2024?",
    "What venues did Robinhood use in January 2024?",
    "How much PFOF did Robinhood receive for S&P 500 stocks in 2024?",
    
    # Schwab queries (should resolve to 'Charles Schwab')
    "How much PFOF did Schwab receive in 2024?",
    "What venues did Charles Schwab use in 2024?",
    
    # Webull queries
    "How much PFOF did Webull receive in 2024?",
    "What was Webull's total PFOF in January 2024?",
    
    # TD Ameritrade
    "How much PFOF did TD Ameritrade receive in 2024?",
    
    # Public
    "How much PFOF did Public receive in 2024?",
    
    # Venue-specific queries
    "Which broker received the most PFOF from Citadel in 2024?",
    "How much PFOF came from Virtu in 2024?",
    
    # Complex queries
    "Which broker had the highest payment rate in 2024?",
    "What percentage of Robinhood's orders were marketable limit orders?",
    "Compare PFOF for Robinhood vs Schwab in 2024",
    
    # Month comparisons
    "Which month had the highest PFOF for Robinhood in 2024?",
    "How did Robinhood's PFOF change from January to December 2024?",
]

def get_actual_db_values():
    """Get actual broker and venue names from DB for reference"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get top brokers
    cur.execute("""
        SELECT DISTINCT executing_bd, COUNT(*) as cnt
        FROM executing_bd_606
        WHERE executing_bd IS NOT NULL AND executing_bd != ''
        GROUP BY executing_bd
        ORDER BY cnt DESC
        LIMIT 20;
    """)
    brokers = [row[0] for row in cur.fetchall()]
    
    # Get top venues
    cur.execute("""
        SELECT DISTINCT venues, COUNT(*) as cnt
        FROM executing_bd_606
        WHERE venues IS NOT NULL AND venues != ''
        GROUP BY venues
        ORDER BY cnt DESC
        LIMIT 20;
    """)
    venues = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return brokers, venues

def main():
    print("=" * 80)
    print("COMPREHENSIVE QUERY TESTING")
    print("=" * 80)
    print()
    
    # Show actual DB values for reference
    print("📊 Getting actual database values for reference...")
    brokers, venues = get_actual_db_values()
    
    print(f"\nTop 20 Brokers in DB:")
    for i, broker in enumerate(brokers, 1):
        print(f"  {i}. {broker}")
    
    print(f"\nTop 20 Venues in DB:")
    for i, venue in enumerate(venues, 1):
        print(f"  {i}. {venue}")
    
    print("\n" + "=" * 80)
    print("RUNNING TEST QUERIES")
    print("=" * 80)
    
    results = []
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{i}. {question}")
        print("-" * 80)
        
        try:
            result = run_query_from_nl(question)
            
            sql = result.get('sql', '')
            data = result.get('results', [])
            error = result.get('error')
            
            # Show SQL
            print(f"SQL: {sql[:200]}{'...' if len(sql) > 200 else ''}")
            
            if error:
                print(f"❌ ERROR: {error}")
                results.append({"question": question, "status": "error", "error": error})
            elif not data:
                print(f"⚠️  WARNING: Query returned no results")
                results.append({"question": question, "status": "empty", "sql": sql})
            else:
                print(f"✅ SUCCESS: {len(data)} result(s)")
                if len(data) <= 3:
                    for row in data:
                        print(f"   {row}")
                results.append({"question": question, "status": "success", "count": len(data)})
            
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.append({"question": question, "status": "exception", "error": str(e)})
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    success = sum(1 for r in results if r['status'] == 'success')
    empty = sum(1 for r in results if r['status'] == 'empty')
    errors = sum(1 for r in results if r['status'] in ['error', 'exception'])
    
    print(f"\n✅ Successful queries: {success}/{len(results)}")
    print(f"⚠️  Empty results: {empty}/{len(results)}")
    print(f"❌ Errors: {errors}/{len(results)}")
    
    if empty > 0:
        print("\n⚠️  Queries with empty results (possible alias issues):")
        for r in results:
            if r['status'] == 'empty':
                print(f"  • {r['question']}")
    
    if errors > 0:
        print("\n❌ Queries with errors:")
        for r in results:
            if r['status'] in ['error', 'exception']:
                print(f"  • {r['question']}")
                print(f"    {r.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()

