"""
Test count and per_entity_average operations with LLM intent extraction
"""
import os
os.environ["USE_LLM_INTENT"] = "true"

from planner import plan_single_sql

# Test queries for new operations
test_queries = [
    # Count operations
    "How many venues did Robinhood use in 2024",
    "How many wholesalers did Charles Schwab use in 2024",
    "How many market makers did Fidelity trade with in June 2024",
    "How many brokers are in the data for 2024",

    # Per-entity average operations
    "Average PFOF per venue for Robinhood in 2024",
    "Average PFOF per wholesaler for TD Ameritrade in 2024",
    "Average PFOF per market maker for E*TRADE in June 2024",
    "Average volume per broker in Q2 2024",

    # Test with synonyms
    "What is the average payment per liquidity provider for Robinhood",
]

print("Testing New Operations: count & per_entity_average")
print("=" * 80)

for query in test_queries:
    print(f"\nQuery: {query}")
    print("-" * 80)
    sql = plan_single_sql(query, {})
    if sql:
        print("✅ Generated SQL:")
        print(sql)
    else:
        print("❌ Failed to generate SQL")
    print()
