# Query Feedback Diagnostic Report

**Date:** December 3, 2025
**Source:** query_feedback.csv (5 problematic queries)
**Analyst:** System Diagnostic

---

## Executive Summary

All 5 queries in the feedback CSV suffer from the same **root cause**: The system fails to properly handle "**for each [entity]**" or "**each [entity]**" patterns when combined with aggregation requests like "**how many**" or "**count**".

### Common Pattern:
- User asks: "For each broker, how many venues..."
- Expected: `GROUP BY executing_bd` with `COUNT(DISTINCT venues)` per broker
- Actual: Global `COUNT(DISTINCT venues)` with NO GROUP BY

---

## Detailed Issue Analysis

### **Issue #1: Query 1 - Two-Level Aggregation**

**Query:** "On average, how many venues did a broker get PFOF from in April 2025"

**Expected Behavior:**
```sql
-- Step 1: Count venues per broker
WITH broker_venue_counts AS (
  SELECT executing_bd, COUNT(DISTINCT venues) AS venue_count
  FROM executing_bd_606
  WHERE year = 2025 AND month = '4' AND data_type = 'venue'
  GROUP BY executing_bd
)
-- Step 2: Average across brokers
SELECT AVG(venue_count) AS avg_venues_per_broker
FROM broker_venue_counts;
```

**Actual SQL Generated:**
```sql
SELECT
  SUM(...) AS total_pfof_usd,
  COUNT(DISTINCT venues) AS venue_count,
  (...) / NULLIF(COUNT(DISTINCT venues), 0) AS pfof_per_venue
FROM executing_bd_606
WHERE year = 2025 AND month = '4' AND data_type = 'venue';
-- NO GROUP BY!
```

**Result:** Returns 1 row with:
- `venue_count = 261` (global count of all venues)
- Instead of: Average of (venues per broker)

**Root Causes:**
1. ✅ **"each broker" detected** → Triggers "aggregate" operation (planner.py:82-85)
2. ✅ **Dimension inferred** → "broker" → `executing_bd` (planner.py:164-165)
3. ❌ **"on average" + "how many venues"** → System interprets as "per-entity average" (PFOF per venue)
4. ❌ **Two-level aggregation not supported** → No pattern for "average of (count per entity)"
5. ❌ **Wrong operation selected** → Uses `build_per_entity_average` instead of nested subquery

**Pattern Not Detected:**
- "on average" + "for each X" + "how many Y" should trigger two-level aggregation

---

### **Issue #2: Query 2 - Complex Handler Hallucination**

**Query:** "In April 2024, For each executing_bd count the number of distinct venue names where PFOF is greater than 0 or NOT NULL across all stock_groups."

**Query Type:** `complex_multi_table`
**Results Count:** `0`
**User Notes:** "this went totally haywire"

**Expected Behavior:**
```sql
SELECT executing_bd, COUNT(DISTINCT venues) AS venue_count
FROM executing_bd_606
WHERE year = 2024 AND month = '4'
  AND data_type = 'venue'
  AND (
    netpmtpaidrecvmarketordersusd > 0 OR
    netpmtpaidrecvmarketablelimitordersusd > 0 OR
    netpmtpaidrecvnonmarketablelimitordersusd > 0 OR
    netpmtpaidrecvotherordersusd > 0
  )
GROUP BY executing_bd
ORDER BY venue_count DESC;
```

**Actual Result:**
- SQL generated: Not shown in CSV (complex handler)
- Results: 0 rows returned
- GenAI response: Hallucinated data about 3 brokers with Citadel

**GenAI Hallucinated Response:**
```
"Based on the provided query results, there are three executing brokers (executing_bd)
that have PFOF greater than 0. Each broker is associated with one distinct venue,
namely "CITADEL SECURITIES LLC". Therefore, the total number of distinct venues is 1,
and the sum of brokers is 3."
```

Then lists a table with Robinhood, TD Ameritrade, Charles Schwab with PFOF values.

**Root Causes:**
1. ❌ **Complex query routed to multi-table handler** → Query is actually single-table
2. ❌ **Complex handler returned empty results** (`sql_results_count = 0`)
3. ❌ **GenAI synthesized fake data** → Generated plausible-looking but false results
4. ❌ **No safety check** → System doesn't validate that narrative matches actual results

**Critical Bug:**
The GenAI synthesis layer creates confident narratives even when `results_count = 0`. This is a **data integrity violation** - the system should NEVER invent data.

---

### **Issue #3: Query 3 - Missing GROUP BY**

**Query:** "In April 2024, each broker received PFOF from how many venues?"

**Expected SQL:**
```sql
SELECT executing_bd, COUNT(DISTINCT venues) AS venue_count
FROM executing_bd_606
WHERE year = 2024 AND month = '4'
  AND data_type = 'venue'
  AND venues IS NOT NULL
  AND venues != ''
GROUP BY executing_bd
ORDER BY venue_count DESC;
```

**Actual SQL:**
```sql
SELECT COUNT(DISTINCT venues) AS venue_count
FROM executing_bd_606
WHERE year = 2024 AND month = '4'
  AND venues IS NOT NULL
  AND venues != ''
  AND data_type = 'venue';
-- NO GROUP BY!
```

**Result:** Returns 1 row: `venue_count = 41` (total unique venues globally)
**Expected:** 10-15 rows showing each broker and their venue count

**Root Causes:**
1. ✅ **"each broker" detected** → Triggers "aggregate" operation (planner.py:82-85)
2. ✅ **Dimension inferred** → Returns "executing_bd" (planner.py:164-165)
3. ❌ **But "how many venues" overrides dimensions** → Switches to "count" operation
4. ❌ **"count" operation uses `build_count`** → No GROUP BY support (sql_templates.py:621-670)
5. ❌ **Dimensions lost when operation changes**

**Code Flow:**
```python
# planner.py line 82-85
if any(w in text for w in ["each", "per"]) or ...:
    return "aggregate", dims  # ✅ Correct operation

# But later (somewhere in plan_single_sql):
# "how many venues" triggers → operation = "count"  # ❌ Wrong!
# build_count() doesn't accept dimensions → generates global COUNT
```

**Pattern Not Detected:**
- "each [entity]" + "how many [other_entity]" should use `build_aggregate` with:
  - `dimensions = [entity]`
  - `metric = COUNT(DISTINCT other_entity)`
  - Not the standalone `build_count` function

---

### **Issue #4: Query 4 - Same as Issue #3**

**Query:** "In April 2024, list every broker that received PFOF and the number of venues for each broker"

**User Notes:** "this is retrieving a venue that received PFOF, not an executing_bd"

**Actual SQL:** (Same as Query 3)
```sql
SELECT COUNT(DISTINCT venues) AS venue_count
FROM executing_bd_606
WHERE year = 2024 AND month = '4'
  AND venues IS NOT NULL
  AND venues != '';
```

**Expected:** Same as Query 3 - should GROUP BY executing_bd

**Root Causes:** Identical to Issue #3
- "list every broker" + "number of venues for each broker"
- Should use `build_aggregate` with dimensions=["executing_bd"]
- Instead uses `build_count` with no dimensions

---

### **Issue #5: Query 5 - Missing Aggregation**

**Query:** "In April 2024, list every executing_bd that received PFOF from a venue and the number of venues"

**User Notes:** "I reworded the previous query and got the list of executing_bd but not the number of venues [per]"

**Actual SQL:**
```sql
SELECT DISTINCT executing_bd
FROM executing_bd_606
WHERE year = 2024 AND month = '4'
  AND executing_bd IS NOT NULL
  AND executing_bd != ''
ORDER BY executing_bd;
```

**Result:** 13 rows (list of broker names)
**Missing:** `COUNT(DISTINCT venues)` column

**Expected SQL:**
```sql
SELECT executing_bd, COUNT(DISTINCT venues) AS venue_count
FROM executing_bd_606
WHERE year = 2024 AND month = '4'
  AND data_type = 'venue'
  AND executing_bd IS NOT NULL
  AND executing_bd != ''
GROUP BY executing_bd
ORDER BY venue_count DESC;
```

**Root Causes:**
1. ✅ **"list every executing_bd" correctly parsed** → Uses `build_distinct`
2. ❌ **"and the number of venues" ignored** → Second part of query lost
3. ❌ **Should detect compound request** → List + count = aggregate with GROUP BY
4. ❌ **Operation precedence issue** → "list" wins over "count"

**Pattern Not Detected:**
- "list every X" + "and the number of Y" should be treated as single aggregate query, not just "list"

---

## Root Cause Summary

### Primary Root Cause: **Operation Detection Priority Bug**

The `_detect_operation_and_dims` function has conflicting pattern priorities:

```python
# planner.py lines 78-85
if any(w in text for w in ["list", "show", "display"]) and any(w in text for w in ["unique", "distinct", "all"]):
    return "list", dims  # ← Detected first

if any(w in text for w in ["each", "per"]) or any(text.count(f"by {w}") for w in ["broker", "venue", "participant"]):
    return "aggregate", dims  # ← Detected second, but "list" already returned!
```

**Problem:** When a query contains BOTH "list" and "each", the "list" operation is returned early, preventing "aggregate" detection.

### Secondary Root Cause: **Missing "Count Per Entity" Pattern**

The system has:
- ✅ `build_count(dimension)` → Global count (no GROUP BY)
- ✅ `build_aggregate(dimensions, metric)` → Grouped aggregation (with GROUP BY)
- ❌ No pattern detector for: "for each X, count Y" → aggregate with COUNT metric

### Tertiary Root Cause: **GenAI Hallucination on Empty Results**

Query #2 shows the GenAI synthesizer creates confident but false narratives when `results_count = 0`. This is a critical data integrity issue.

---

## Recommended Fixes

### Fix 1: **Add "Count Per Entity" Pattern Detection**

**File:** `planner.py` lines 58-70 (before other patterns)

```python
def _detect_operation_and_dims(tags: Dict) -> Tuple[str, List[str]]:
    text = (tags.get("_text") or "").lower()
    dims = []

    # NEW: "for each X, count/how many Y" pattern
    # Must be checked BEFORE "list" pattern
    count_per_pattern = re.search(r'\b(for each|each|per)\s+(broker|brokers?|venue|venues?|executing.?bd)\b.*\b(how many|count|number of)\s+(broker|brokers?|venue|venues?|executing.?bd)\b', text)
    if count_per_pattern:
        entity1 = count_per_pattern.group(2)  # The "for each" entity
        entity2 = count_per_pattern.group(4)  # The "count" entity

        # Map to dimension names
        if 'broker' in entity1 or 'executing' in entity1:
            dims = ["executing_bd"]
        elif 'venue' in entity1:
            dims = ["venues"]

        # This should use aggregate with COUNT metric, not standalone count
        return "aggregate", dims
```

### Fix 2: **Modify Dimension Inference for Aggregate Operations**

**File:** `planner.py` lines 335-345

```python
# After detecting operation = "aggregate"
if op == "aggregate":
    # NEW: Detect COUNT requests in aggregate context
    if any(phrase in text for phrase in ["how many", "count", "number of"]):
        # This is COUNT(DISTINCT entity) per group
        # Don't switch to "count" operation, stay with "aggregate"
        intent.aggregation = "COUNT"

        # Detect what to count
        if "venue" in text and "executing_bd" in intent.dimensions:
            intent.metric = "venues"  # Will be handled specially
        elif "broker" in text and "venues" in intent.dimensions:
            intent.metric = "executing_bd"
```

### Fix 3: **Extend `build_aggregate` to Support COUNT Metrics**

**File:** `sql_templates.py` - Modify `_metric_select` function

```python
def _metric_select(table: str, intent: QueryIntent) -> str:
    # ... existing code ...

    # NEW: Handle COUNT metrics in aggregate context
    if intent.aggregation == "COUNT" and intent.metric:
        # COUNT(DISTINCT dimension)
        column = intent.metric
        if column == "venue":
            column = "venues"  # Normalize
        return f"COUNT(DISTINCT {_safe_ident(column)}) AS {column}_count"
```

### Fix 4: **Add Two-Level Aggregation Support**

**File:** `planner.py` - New operation type

```python
def _detect_operation_and_dims(tags: Dict) -> Tuple[str, List[str]]:
    text = (tags.get("_text") or "").lower()

    # NEW: "on average, ... for each X, how many Y" pattern
    if "average" in text or "on average" in text:
        if any(phrase in text for phrase in ["for each", "each", "per"]):
            if any(phrase in text for phrase in ["how many", "count", "number of"]):
                # Two-level aggregation: AVG(COUNT(...) per group)
                return "nested_average_count", dims
```

**File:** `sql_templates.py` - New template

```python
def build_nested_average_count(intent: QueryIntent, table: str,
                                 partition_dim: str, count_dim: str) -> str:
    """
    Build nested query: Average of (COUNT per group)

    Example: "On average, how many venues did a broker get PFOF from?"
    """
    where = _time_filters(table, intent)
    where.append(f"data_type = 'venue'")
    where_clause = " AND ".join(where) if where else "TRUE"

    return f"""
WITH entity_counts AS (
  SELECT {partition_dim}, COUNT(DISTINCT {count_dim}) AS count_per_entity
  FROM {table}
  WHERE {where_clause}
  GROUP BY {partition_dim}
)
SELECT AVG(count_per_entity) AS average_count
FROM entity_counts;
""".strip()
```

### Fix 5: **Prevent GenAI Hallucination on Empty Results**

**File:** `hybrid_query_handler.py` - Add safety check before synthesis

```python
def _generate_narrative_response(user_input: str, query_results: Dict, intent: QueryIntent) -> str:
    # NEW: Safety check
    total_results = sum(
        qr.get("row_count", 0)
        for qr in query_results.values()
        if isinstance(qr, dict)
    )

    if total_results == 0:
        return "No data found matching your query criteria. Please try adjusting the time period or filters."

    # Existing synthesis logic...
```

---

## Testing Plan

### Test Case 1: "For Each + Count" Pattern
```python
queries = [
    "In April 2024, each broker received PFOF from how many venues?",
    "For each executing_bd in Q2 2024, how many venues did they use?",
    "How many venues per broker in 2024?",
]

for q in queries:
    sql = plan_single_sql(q, {...})
    assert "GROUP BY executing_bd" in sql
    assert "COUNT(DISTINCT venues)" in sql
```

### Test Case 2: Two-Level Aggregation
```python
query = "On average, how many venues did a broker get PFOF from in April 2024?"
sql = plan_single_sql(query, {...})
assert "WITH" in sql  # CTE for subquery
assert "AVG(count_per_entity)" in sql
assert "GROUP BY executing_bd" in sql
```

### Test Case 3: Empty Results Safety
```python
query = "PFOF for FakeCompany123 in April 2024"
results = {"pfof": {"results": [], "row_count": 0}}
narrative = _generate_narrative_response(query, results, intent)
assert "No data found" in narrative
assert "FakeCompany123" not in narrative  # Don't invent data
```

---

## Impact Assessment

| Issue | Severity | Frequency | User Impact | Fix Complexity |
|-------|----------|-----------|-------------|----------------|
| Missing GROUP BY | **Critical** | Very High | Wrong answers | Medium |
| GenAI hallucination | **Critical** | Low | False data | Low |
| Two-level aggregation | High | Medium | Wrong answers | High |
| Pattern precedence | High | High | Wrong operation | Low |
| Missing COUNT in list | Medium | Low | Incomplete data | Medium |

---

## Priority Recommendations

### P0 (Critical - Ship Blocker)
1. ✅ **Fix "for each X, count Y" pattern** (Fix 1)
2. ✅ **Prevent GenAI hallucination** (Fix 5)

### P1 (High - Should Fix Soon)
3. ✅ **Support COUNT in aggregate** (Fix 2 & 3)
4. ✅ **Fix operation precedence** (Reorder pattern checks)

### P2 (Nice to Have)
5. ⚠️ **Two-level aggregation** (Fix 4) - Complex, defer if needed

---

## Conclusion

All 5 queries suffer from variations of the same bug: **The system fails to properly combine "for each [entity]" grouping with "count [other_entity]" aggregation**.

The fixes are straightforward:
1. Detect the combined pattern earlier in the pipeline
2. Use `build_aggregate` with COUNT instead of `build_count`
3. Ensure dimensions are preserved when COUNT is requested
4. Add safety checks to prevent hallucination

**Estimated Fix Time:** 4-6 hours for P0 and P1 fixes
**Testing Time:** 2-3 hours
**Total:** ~1 day of work to resolve all critical issues
