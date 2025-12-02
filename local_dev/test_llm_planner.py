"""
Test script for LLM-based intent extraction and SQL generation
"""
import os
os.environ["USE_LLM_INTENT"] = "true"  # Enable LLM mode

from planner import plan_single_sql

# Test queries
test_queries = [
    "Who paid Robinhood PFOF in June 2024",
    "Top 5 brokers by PFOF in 2024",
    "For each quarter, top market participant by total shares in 2024",
    "What brokers traded in Q2 2024",
    "Compare PFOF and estimated volume by broker in 2024",
    "List distinct quarters for 2024 ATS data",
    "Which month had the lowest PFOF for Citadel in 2024",
]

print("Testing LLM Intent → SQL Generation")
print("=" * 80)

for query in test_queries:
    print(f"\nQuery: {query}")
    print("-" * 80)
    sql = plan_single_sql(query, {})
    if sql:
        print("Generated SQL:")
        print(sql)
    else:
        print("❌ Failed to generate SQL")
    print()
