#!/usr/bin/env python3
"""
Test script for cross-table enrichment functionality

Tests the automatic enrichment of executing_bd queries with monthly_data context
"""

from query import run_query_from_nl
import json

print("="*80)
print("TESTING CROSS-TABLE ENRICHMENT")
print("="*80)

# Test queries
test_queries = [
    "What month in 2024 did Robinhood get paid the most PFOF?",
    "Which broker got paid the most in PFOF in 2024?",
    "Show me Citadel's PFOF payments in March 2024"
]

for i, query in enumerate(test_queries, 1):
    print(f"\n\n{'='*80}")
    print(f"TEST {i}: {query}")
    print('='*80)
    
    result = run_query_from_nl(query)
    
    print(f"\n📊 SQL Generated:")
    print(result.get('sql', 'N/A'))
    
    print(f"\n✅ Primary Results:")
    results = result.get('results', [])
    if results:
        for r in results[:3]:  # Show first 3 results
            print(f"  {r}")
    else:
        print("  No results")
    
    print(f"\n📈 Enrichment Status:")
    enrichment = result.get('enrichment')
    if enrichment:
        if enrichment.get('has_enrichment'):
            print("  ✅ Enrichment succeeded")
            print(f"  Time Period: {enrichment.get('time_period')}")
            
            monthly_context = enrichment.get('monthly_context')
            if monthly_context:
                print(f"  Total Shares: {float(monthly_context.get('total_shares', 0)):,.0f}")
                print(f"  Rank: #{monthly_context.get('month_rank_by_shares', monthly_context.get('year_rank_by_shares', 'N/A'))}")
        
        elif enrichment.get('enrichment_failed'):
            print("  ⚠️  Enrichment failed (primary query still succeeded)")
            print(f"  Debug Info: {enrichment.get('debug_info')}")
            print(f"  Error: {enrichment.get('error')}")
        
        else:
            print("  ℹ️  No enrichment available (no time period detected)")
    else:
        print("  ℹ️  No enrichment")
    
    print(f"\n💡 Insights:")
    insights = result.get('insights', [])
    if insights:
        for insight in insights:
            print(f"  {insight}")
    else:
        print("  No insights generated")
    
    # Check for errors
    if 'error' in result:
        print(f"\n❌ PRIMARY QUERY ERROR: {result['error']}")

print("\n\n" + "="*80)
print("TESTING COMPLETE")
print("="*80)


