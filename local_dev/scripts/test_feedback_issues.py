"""
Re-test problematic queries from query_feedback.csv with LLM intent system
"""
import os
os.environ["USE_LLM_INTENT"] = "true"

from planner import plan_single_sql

# Problematic queries from feedback
test_cases = [
    {
        "id": 1,
        "query": "For each quarter, top market participant by total shares in 2024",
        "issue": "Not partitioning by quarter (OLD: returned all participants aggregated)",
        "expected": "Should use top_per_group with quarter partition"
    },
    {
        "id": 2,
        "query": "List distinct quarters for 2024 (ATS)",
        "issue": "Returned ATS names instead of quarters",
        "expected": "Should return distinct quarters from finra_ats"
    },
    {
        "id": 3,
        "query": "List the first 10 entities across the system in alphabetical order",
        "issue": "Not implemented",
        "expected": "Should use cross_table_entity_list operation"
    },
    {
        "id": 4,
        "query": "what broker has the longest name",
        "issue": "Not implemented - just aggregated PFOF",
        "expected": "Should use string_length operation"
    },
    {
        "id": 5,
        "query": "Top venue per broker by PFOF in 2024",
        "issue": "False positive: detected 'Pershing' from word 'per'",
        "expected": "Should use top_per_group, no venue filter"
    },
    {
        "id": 6,
        "query": "list the month and year values in executed_bd_606",
        "issue": "False positive: detected 'Israel Englander' from 'executed_bd'",
        "expected": "Should list distinct month/year combinations"
    },
    {
        "id": 7,
        "query": "Compare PFOF and estimated volume by broker in 2024",
        "issue": "Only returned PFOF, not both metrics",
        "expected": "Should return both total_pfof_usd and estimated_volume"
    },
    {
        "id": 8,
        "query": "List all unique stock groups present in 2024",
        "issue": "Returned executing_bd instead of stock_group",
        "expected": "Should return distinct stock_group values"
    },
    {
        "id": 9,
        "query": "Latest month with non-zero PFOF in 2024",
        "issue": "Not detecting 'latest' as operation",
        "expected": "Should use latest operation to find most recent month"
    },
    {
        "id": 10,
        "query": "Top 5 months by total trades in 2024",
        "issue": "Used wrong table/metric (used executing_bd_606 PFOF)",
        "expected": "Should use monthly_data.total_trade_count or finra_ats.total_trades"
    },
]

print("=" * 100)
print("RE-TESTING PROBLEMATIC QUERIES WITH LLM INTENT SYSTEM")
print("=" * 100)

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*100}")
    print(f"TEST {test['id']}: {test['query']}")
    print(f"{'='*100}")
    print(f"Previous Issue: {test['issue']}")
    print(f"Expected: {test['expected']}")
    print("-" * 100)

    sql = plan_single_sql(test['query'], {})

    if sql:
        print("✅ GENERATED SQL:")
        # Show key parts
        lines = sql.split("\n")
        for line in lines[:15]:  # First 15 lines
            print(f"  {line}")
        if len(lines) > 15:
            print(f"  ... ({len(lines) - 15} more lines)")

        # Analysis
        print("\n📊 ANALYSIS:")
        sql_lower = sql.lower()

        # Check for key patterns
        if "row_number() over" in sql_lower:
            print("  ✓ Uses window function (top-per-group)")
        if "partition by" in sql_lower:
            print("  ✓ Has PARTITION BY clause")
        if "extract(quarter" in sql_lower:
            print("  ✓ Extracts quarter from date")
        if "extract(month" in sql_lower:
            print("  ✓ Extracts month from date")
        if "length(" in sql_lower:
            print("  ✓ Uses LENGTH function")
        if "union" in sql_lower:
            print("  ✓ Uses UNION (cross-table)")
        if "estimated_volume" in sql_lower:
            print("  ✓ Includes estimated volume calculation")
        if "stock_group" in sql_lower:
            print("  ✓ References stock_group column")
        if "venues = " in sql_lower and "pershing" in sql_lower:
            print("  ⚠️  WARNING: False positive venue detection (Pershing)")
        if "venues = " in sql_lower and "englander" in sql_lower:
            print("  ⚠️  WARNING: False positive venue detection (Englander)")

    else:
        print("❌ FAILED TO GENERATE SQL")

    print()

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print("Review the analysis above to see which issues are now fixed by LLM intent system.")
