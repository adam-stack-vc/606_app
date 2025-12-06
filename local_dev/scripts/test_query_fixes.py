#!/usr/bin/env python3
"""
Test script for query feedback fixes
Tests all 5 problematic queries from query_feedback.csv
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from planner import plan_single_sql
from multi_table_query_framework import classify_query_enhanced

# Define test queries from feedback CSV
TEST_QUERIES = [
    {
        "id": 1,
        "query": "On average, how many venues did a broker get PFOF from in April 2025",
        "expected_patterns": [
            "GROUP BY executing_bd",  # Should group by broker
            "COUNT(DISTINCT venues)",  # Should count venues
            # Note: "on average" would require nested query (P2 feature),
            # but at minimum should group by broker
        ],
        "notes": "Two-level aggregation (AVG of COUNT) - P2 feature, but should at least GROUP BY broker"
    },
    {
        "id": 2,
        "query": "In April 2024, For each executing_bd count the number of distinct venue names where PFOF is greater than 0 or NOT NULL across all stock_groups.",
        "expected_patterns": [
            "GROUP BY executing_bd",
            "COUNT(DISTINCT venues)",
            "data_type = 'venue'",
        ],
        "notes": "Should use planner path, not complex handler"
    },
    {
        "id": 3,
        "query": "In April 2024, each broker received PFOF from how many venues?",
        "expected_patterns": [
            "GROUP BY executing_bd",
            "COUNT(DISTINCT venues)",
            "data_type = 'venue'",
        ],
        "notes": "Core 'for each X, count Y' pattern"
    },
    {
        "id": 4,
        "query": "In April 2024, list every broker that received PFOF and the number of venues for each broker",
        "expected_patterns": [
            "GROUP BY executing_bd",
            "COUNT(DISTINCT venues)",
            "data_type = 'venue'",
        ],
        "notes": "'list X and count Y' pattern"
    },
    {
        "id": 5,
        "query": "In April 2024, list every executing_bd that received PFOF from a venue and the number of venues",
        "expected_patterns": [
            "GROUP BY executing_bd",
            "COUNT(DISTINCT venues)",
            "data_type = 'venue'",
        ],
        "notes": "Similar to #4, should include count"
    }
]

def test_query(test_case):
    """Test a single query and verify expected patterns"""
    query = test_case["query"]
    test_id = test_case["id"]
    expected = test_case["expected_patterns"]
    notes = test_case["notes"]

    print(f"\n{'='*80}")
    print(f"TEST {test_id}: {notes}")
    print(f"{'='*80}")
    print(f"Query: {query}")
    print(f"\n--- Classification ---")

    # Step 1: Classify the query
    tags = classify_query_enhanced(query)
    print(f"Tags: {tags}")

    # Step 2: Generate SQL
    print(f"\n--- SQL Generation ---")
    try:
        sql = plan_single_sql(query, tags)

        if sql:
            print(f"✅ SQL Generated:")
            print(sql)

            # Step 3: Verify expected patterns
            print(f"\n--- Pattern Verification ---")
            all_found = True
            for pattern in expected:
                if pattern.upper() in sql.upper():
                    print(f"✅ Found: {pattern}")
                else:
                    print(f"❌ MISSING: {pattern}")
                    all_found = False

            # Check for bad patterns
            bad_patterns = []
            if "SELECT COUNT(DISTINCT venues)" in sql and "GROUP BY" not in sql:
                bad_patterns.append("COUNT without GROUP BY (global count)")

            if bad_patterns:
                print(f"\n⚠️  BAD PATTERNS DETECTED:")
                for bp in bad_patterns:
                    print(f"   - {bp}")
                all_found = False

            return {
                "test_id": test_id,
                "query": query,
                "status": "PASS" if all_found else "FAIL",
                "sql": sql,
                "missing_patterns": [p for p in expected if p.upper() not in sql.upper()],
                "bad_patterns": bad_patterns
            }
        else:
            print(f"❌ No SQL generated (returned None)")
            return {
                "test_id": test_id,
                "query": query,
                "status": "FAIL",
                "sql": None,
                "missing_patterns": expected,
                "bad_patterns": ["No SQL generated"]
            }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "test_id": test_id,
            "query": query,
            "status": "ERROR",
            "sql": None,
            "error": str(e)
        }

def main():
    """Run all tests and generate summary"""
    print("="*80)
    print("QUERY FEEDBACK FIX TESTING")
    print("Testing P0 and P1 fixes for 'for each X, count Y' patterns")
    print("="*80)

    results = []
    for test_case in TEST_QUERIES:
        result = test_query(test_case)
        results.append(result)

    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Errors: {errors}")

    if failed > 0 or errors > 0:
        print(f"\n--- Failed/Error Tests ---")
        for r in results:
            if r["status"] in ["FAIL", "ERROR"]:
                print(f"\nTest {r['test_id']}: {r['status']}")
                print(f"  Query: {r['query']}")
                if r.get("missing_patterns"):
                    print(f"  Missing patterns: {r['missing_patterns']}")
                if r.get("bad_patterns"):
                    print(f"  Bad patterns: {r['bad_patterns']}")
                if r.get("error"):
                    print(f"  Error: {r['error']}")

    print(f"\n{'='*80}")
    if passed == len(results):
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Review results above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
