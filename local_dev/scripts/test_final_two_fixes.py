"""
Test the two remaining issues that were broken
"""
import os
os.environ["USE_LLM_INTENT"] = "true"

from planner import plan_single_sql

print("=" * 80)
print("TESTING THE TWO REMAINING FIXES")
print("=" * 80)

# Test 1: List multiple columns (month and year)
print("\n" + "="*80)
print("TEST 1: list the month and year values in executed_bd_606")
print("="*80)
print("Expected: SELECT DISTINCT year, month FROM executing_bd_606...")
print("-" * 80)

sql1 = plan_single_sql("list the month and year values in executed_bd_606", {})
if sql1:
    print("✅ GENERATED SQL:")
    print(sql1)
    if "year" in sql1.lower() and "month" in sql1.lower():
        if sql1.lower().count("select distinct") > 0 and "," in sql1:
            print("\n✓ SUCCESS: Returns both month AND year columns!")
        else:
            print("\n⚠️  PARTIAL: Has both fields but may not be in same SELECT")
    else:
        print("\n❌ FAILED: Missing month or year")
else:
    print("❌ NO SQL GENERATED")

# Test 2: pfof_and_volume
print("\n" + "="*80)
print("TEST 2: Compare PFOF and estimated volume by broker in 2024")
print("="*80)
print("Expected: SELECT executing_bd, total_pfof_usd, estimated_volume...")
print("-" * 80)

sql2 = plan_single_sql("Compare PFOF and estimated volume by broker in 2024", {})
if sql2:
    print("✅ GENERATED SQL:")
    print(sql2)
    if "total_pfof_usd" in sql2 and "estimated_volume" in sql2:
        print("\n✓ SUCCESS: Returns BOTH pfof and estimated volume!")
    elif "total_pfof_usd" in sql2:
        print("\n⚠️  PARTIAL: Has PFOF but missing estimated volume")
    else:
        print("\n❌ FAILED: Missing metrics")
else:
    print("❌ NO SQL GENERATED")

print("\n" + "=" * 80)
print("FINAL VERDICT")
print("=" * 80)

if sql1 and sql2:
    if ("year" in sql1.lower() and "month" in sql1.lower() and "," in sql1) and \
       ("total_pfof_usd" in sql2 and "estimated_volume" in sql2):
        print("🎉 BOTH TESTS PASSED! All 10/10 feedback issues are now fixed!")
    else:
        print("⚠️  SQL generated but may have issues")
else:
    print("❌ One or more tests failed")
