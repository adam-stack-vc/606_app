# Temporal Dimension Bug - Root Cause Analysis

**Date:** December 3, 2025
**Discovered by:** User testing of Query ID 82
**Severity:** HIGH - Affects existing queries in test suite

---

## Summary

**Bug:** Queries that group by temporal dimensions (month/quarter/year) on `executing_bd_606` table generate SQL without GROUP BY clauses.

**Root Cause:** `build_aggregate()` in `sql_templates.py` only handles temporal dimensions for tables with `day_col`, but `executing_bd_606` has explicit `month` and `year` columns.

**Affected Queries:** 3 existing queries (IDs 26, 27, 82)

---

## Affected Queries

| ID | Question | Expected | Actual |
|----|----------|----------|--------|
| 26 | "For each month, top 3 brokers by PFOF in 2024" | GROUP BY month, executing_bd | ❌ No GROUP BY |
| 27 | "PFOF by month in 2024" | GROUP BY month | ❌ No GROUP BY |
| 82 | "For Robinhood, how many venues in each month of 2024?" | GROUP BY month | ❌ No GROUP BY |

---

## Root Cause Trace

### Step 1: Query Classification
```
Query: "For Robinhood, how many venues in each month of 2024?"
classify_query_enhanced() returns:
  - year: 2024
  - month: None
  - executing_bd: None (not detected - secondary issue)
```

### Step 2: Operation Detection
```
_detect_operation_and_dims() returns:
  - operation: "aggregate_with_count" ✅
  - auto_dims: ['month'] ✅
```

### Step 3: Intent Building
```
QueryIntent.from_tags(tags):
  - intent.dimensions: [] (empty initially)

plan_single_sql sets:
  - intent.dimensions = auto_dims = ['month'] ✅
```

### Step 4: SQL Generation
```
aggregate_with_count handler:
  - count_target = 'venues' ✅
  - intent.metric = 'venues' ✅
  - intent.aggregation = 'COUNT' ✅
  - Calls: build_aggregate(intent, table)
```

### Step 5: build_aggregate() - THE BUG
```python
# sql_templates.py line 303-322
def build_aggregate(intent: QueryIntent, table: str) -> str:
    caps = get_capabilities(table)

    dims = []
    temporal_dims = []
    requested_dims = intent.dimensions or []  # ['month']

    for dim in requested_dims:
        if dim in caps.allowed_dimensions:
            # ❌ 'month' not in {'venues', 'stock_group', 'executing_bd'}
            dims.append(dim)
        elif dim in ["month", "quarter", "year"] and caps.time.day_col:
            # ❌ caps.time.day_col is None for executing_bd_606
            temporal_dims.append(dim)

    # Result: dims = [] and temporal_dims = []
    # Therefore: NO GROUP BY generated!
```

### Capabilities for executing_bd_606:
```python
caps.allowed_dimensions = {'venues', 'stock_group', 'executing_bd'}
caps.time.day_col = None        # ❌ No day column
caps.time.year_col = 'year'     # ✅ Has year column
caps.time.month_col = 'month'   # ✅ Has month column
caps.time.quarter_col = None    # ❌ No quarter column (derived)
```

**The Problem:**
`build_aggregate` assumes temporal dimensions only work with `EXTRACT(MONTH FROM day_col)` style queries (like `monthly_data` table), but `executing_bd_606` has explicit `month` and `year` string columns!

---

## Why This Happens

### Table Schemas Comparison:

**monthly_data (works):**
```sql
CREATE TABLE monthly_data (
    day DATE,  -- ✅ day column for EXTRACT
    ...
)

-- Query: "total shares by quarter in 2024"
-- Generated SQL:
SELECT EXTRACT(QUARTER FROM day) AS quarter, SUM(total_shares)
FROM monthly_data
WHERE EXTRACT(YEAR FROM day) = 2024
GROUP BY EXTRACT(QUARTER FROM day);
```

**executing_bd_606 (broken):**
```sql
CREATE TABLE executing_bd_606 (
    year VARCHAR,   -- ✅ Explicit columns
    month VARCHAR,  -- ✅ Explicit columns
    ...
)

-- Query: "PFOF by month in 2024"
-- Generated SQL (WRONG):
SELECT SUM(...) AS total_pfof_usd
FROM executing_bd_606
WHERE year = 2024;
-- ❌ Missing: SELECT month, ... GROUP BY month
```

---

## The Logic Gap

`build_aggregate()` has this logic:

```python
if dim in caps.allowed_dimensions:
    # Add to dims (works for 'venues', 'stock_group', 'executing_bd')
    dims.append(dim)
elif dim in ["month", "quarter", "year"] and caps.time.day_col:
    # Add to temporal_dims (works for monthly_data with day column)
    temporal_dims.append(dim)
else:
    # ❌ Dimension is IGNORED!
    pass
```

For `executing_bd_606`:
- `month` is NOT in `allowed_dimensions`
- `caps.time.day_col` is None
- **Result: month dimension is silently ignored!**

---

## Fix Required

Modify `build_aggregate()` in `sql_templates.py` to handle explicit temporal columns:

```python
for dim in requested_dims:
    if dim in caps.allowed_dimensions:
        dims.append(dim)
    elif dim in ["month", "quarter", "year"] and caps.time.day_col:
        # Table uses day column, need EXTRACT
        temporal_dims.append(dim)
    elif dim == "month" and caps.time.month_col:
        # NEW: Table has explicit month column
        dims.append(caps.time.month_col)
    elif dim == "year" and caps.time.year_col:
        # NEW: Table has explicit year column
        dims.append(caps.time.year_col)
    elif dim == "quarter":
        # NEW: Quarter requires special handling
        # For executing_bd_606, derive from month
        # For monthly_data, use EXTRACT from day
        if caps.time.day_col:
            temporal_dims.append("quarter")
        elif caps.time.month_col:
            # Derive quarter from month in SELECT/GROUP BY
            # This is complex, may need separate handler
            pass
```

---

## Secondary Issue: Entity Detection

The query "For Robinhood, how many venues..." also has a secondary bug:
- "Robinhood" is not detected by `classify_query_enhanced()`
- Result: No `WHERE executing_bd = 'Robinhood Securities, LLC'` filter

This is a separate issue in entity name resolution.

---

## Impact Assessment

### Existing Queries Affected:
- **ID 26** - Top 3 brokers per month (top_per_group operation)
- **ID 27** - PFOF by month (aggregate operation)
- **ID 82** - Venue count per month for Robinhood (aggregate_with_count)

### Potential Other Affected Patterns:
- Any query with "by month" on executing_bd_606
- Any query with "for each month" on executing_bd_606
- Any query with "per month" on executing_bd_606
- Quarter-based queries (when implemented)

### Tables NOT Affected:
- ✅ `monthly_data` - Uses day column with EXTRACT (works correctly)
- ✅ `finra_ats` - Similar structure to executing_bd_606 (likely also broken)

---

## Testing After Fix

Test these queries to verify fix:

```python
test_queries = [
    "PFOF by month in 2024",  # ID 27
    "For each month, top 3 brokers by PFOF in 2024",  # ID 26
    "How many venues in each month of 2024?",  # ID 82 (simplified)
]

for query in test_queries:
    sql = plan_single_sql(query, classify_query_enhanced(query))
    assert "GROUP BY" in sql and "month" in sql.lower()
```

Expected SQL for ID 27:
```sql
SELECT month, SUM(...) AS total_pfof_usd
FROM executing_bd_606
WHERE year = 2024 AND data_type = 'venue'
GROUP BY month
ORDER BY month;
```

---

## Recommendation

1. **Fix `build_aggregate()` immediately** - This breaks 3 existing test queries
2. **Check `finra_ats` table** - Likely has same issue with quarter column
3. **Add explicit temporal dimensions to `allowed_dimensions`** - Alternative simpler fix
4. **Fix entity detection for "Robinhood"** - Secondary issue for ID 82
5. **Add comprehensive tests** - Cover all temporal dimension + table combinations

---

## Priority

**P0 - Critical:** This breaks existing queries that were thought to be working. The test suite has queries that expect GROUP BY month but aren't getting it.

**Estimated Fix Time:** 1-2 hours
**Estimated Test Time:** 30 minutes
**Risk:** Low (isolated to temporal dimension handling)
