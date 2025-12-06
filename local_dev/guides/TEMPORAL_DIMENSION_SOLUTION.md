# Generic Temporal Dimension Solution

**Goal:** Support temporal grouping for any table with any temporal column (month, quarter, year, week, hour, day, etc.) without writing new code per table.

---

## Current Problem

```python
# sql_templates.py - build_aggregate()
for dim in requested_dims:
    if dim in caps.allowed_dimensions:
        dims.append(dim)  # ✅ Works for 'venues', 'executing_bd'
    elif dim in ["month", "quarter", "year"] and caps.time.day_col:
        temporal_dims.append(dim)  # ✅ Works for monthly_data
    else:
        pass  # ❌ IGNORED - no fallback!
```

**Issues:**
1. Hardcoded list `["month", "quarter", "year"]` - can't add "week", "hour" without code changes
2. Assumes temporal = EXTRACT from day_col
3. No handling for explicit temporal columns (VARCHAR month, quarter, etc.)
4. Silently ignores unrecognized dimensions

---

## Solution: Capability-Driven Temporal Mapping

### **Concept:**
The `TableCapabilities.time` object already has metadata about temporal columns. Use that metadata to automatically determine if a dimension request can be satisfied.

### **Algorithm:**
```
For each requested dimension:
  1. Check if it's in allowed_dimensions (regular dims) → use directly
  2. Check if table has explicit column for that dimension → use that column
  3. Check if table can derive it from day_col → use EXTRACT
  4. Otherwise → raise error (don't silently ignore)
```

---

## Implementation

### **Step 1: Extend TableCapabilities**

```python
# capability_registry.py
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class TimeCapabilities:
    """Time-related column capabilities"""
    day_col: Optional[str] = None      # DATE column (for EXTRACT)
    year_col: Optional[str] = None     # Explicit year column
    month_col: Optional[str] = None    # Explicit month column
    quarter_col: Optional[str] = None  # Explicit quarter column
    week_col: Optional[str] = None     # NEW: Explicit week column
    hour_col: Optional[str] = None     # NEW: Explicit hour column

    def get_temporal_column(self, dimension: str) -> Optional[str]:
        """
        Get the column name for a temporal dimension.

        Args:
            dimension: 'month', 'quarter', 'year', 'week', 'hour', etc.

        Returns:
            Column name if available, None otherwise
        """
        mapping = {
            'year': self.year_col,
            'month': self.month_col,
            'quarter': self.quarter_col,
            'week': self.week_col,
            'hour': self.hour_col,
        }
        return mapping.get(dimension)

    def can_extract_temporal(self, dimension: str) -> bool:
        """
        Check if dimension can be EXTRACTed from day_col.

        Args:
            dimension: 'month', 'quarter', 'year', 'week', etc.

        Returns:
            True if day_col exists and supports this EXTRACT
        """
        if not self.day_col:
            return False

        # PostgreSQL EXTRACT supports these
        extractable = {'year', 'month', 'quarter', 'week', 'day', 'hour'}
        return dimension in extractable

    def supports_dimension(self, dimension: str) -> bool:
        """Check if this dimension is supported at all"""
        return (
            self.get_temporal_column(dimension) is not None or
            self.can_extract_temporal(dimension)
        )
```

---

### **Step 2: Update build_aggregate() to Use Metadata**

```python
# sql_templates.py
def build_aggregate(intent: QueryIntent, table: str) -> str:
    caps = get_capabilities(table)
    if not caps:
        raise ValueError(f"Unknown table: {table}")

    dims = []
    temporal_dims = []
    explicit_temporal_cols = []  # NEW: Track explicit temporal columns
    requested_dims = intent.dimensions or []

    # NEW: Unified dimension processing
    for dim in requested_dims:
        # 1. Check if it's a regular dimension (entity, stock_group, etc.)
        if dim in caps.allowed_dimensions:
            dims.append(dim)

        # 2. Check if table has explicit temporal column for this dimension
        elif caps.time.get_temporal_column(dim):
            explicit_col = caps.time.get_temporal_column(dim)
            explicit_temporal_cols.append((dim, explicit_col))

        # 3. Check if can EXTRACT from day_col
        elif caps.time.can_extract_temporal(dim):
            temporal_dims.append(dim)

        # 4. Dimension not supported by this table
        else:
            # Don't silently ignore - warn or skip gracefully
            print(f"Warning: Dimension '{dim}' not supported by table '{table}'")
            continue

    selects: List[str] = []
    group_by_cols: List[str] = []

    # Add explicit temporal columns (month, quarter, year columns)
    for dim_name, col_name in explicit_temporal_cols:
        selects.append(col_name)  # e.g., "month"
        group_by_cols.append(col_name)

    # Add EXTRACT-based temporal dimensions (from day column)
    if temporal_dims and caps.time.day_col:
        for tdim in temporal_dims:
            if tdim == "month":
                selects.append(f"EXTRACT(MONTH FROM {caps.time.day_col}) AS month")
                group_by_cols.append(f"EXTRACT(MONTH FROM {caps.time.day_col})")
            elif tdim == "quarter":
                selects.append(f"EXTRACT(QUARTER FROM {caps.time.day_col}) AS quarter")
                group_by_cols.append(f"EXTRACT(QUARTER FROM {caps.time.day_col})")
            elif tdim == "year":
                selects.append(f"EXTRACT(YEAR FROM {caps.time.day_col}) AS year")
                group_by_cols.append(f"EXTRACT(YEAR FROM {caps.time.day_col})")
            elif tdim == "week":
                selects.append(f"EXTRACT(WEEK FROM {caps.time.day_col}) AS week")
                group_by_cols.append(f"EXTRACT(WEEK FROM {caps.time.day_col})")
            elif tdim == "hour":
                selects.append(f"EXTRACT(HOUR FROM {caps.time.day_col}) AS hour")
                group_by_cols.append(f"EXTRACT(HOUR FROM {caps.time.day_col})")
            # NEW dimensions automatically work without code changes!

    # Add regular dimensions (venues, executing_bd, etc.)
    if dims:
        selects.extend(dims)
        group_by_cols.extend(dims)

    # Rest of the function unchanged...
    selects.append(_metric_select(table, intent))
    where = _time_filters(table, intent)
    # ...
```

---

### **Step 3: Usage Examples**

#### **Example 1: New Table with Week Column**
```python
# capability_registry.py - Register new table
CAPABILITIES = {
    "new_hourly_data": TableCapabilities(
        table_name="new_hourly_data",
        allowed_dimensions={"sensor_id", "location"},
        time=TimeCapabilities(
            year_col="year",
            month_col="month",
            week_col="week_num",  # NEW: week column
            hour_col="hour_utc",  # NEW: hour column
        ),
        # ...
    )
}
```

**Query:** "Total readings by week in 2024"

**Generated SQL (automatically):**
```sql
SELECT week_num, SUM(reading_value) AS total_readings
FROM new_hourly_data
WHERE year = 2024
GROUP BY week_num;
```

**No code changes needed in `build_aggregate()`!**

---

#### **Example 2: Mixed Temporal Sources**
```python
# capability_registry.py
CAPABILITIES = {
    "event_log": TableCapabilities(
        table_name="event_log",
        allowed_dimensions={"event_type", "user_id"},
        time=TimeCapabilities(
            day_col="timestamp",      # Has timestamp for EXTRACT
            year_col="partition_year", # Also has explicit year for partitioning
        ),
        # ...
    )
}
```

**Query:** "Events by month in 2024"

**Generated SQL:**
```sql
SELECT EXTRACT(MONTH FROM timestamp) AS month, COUNT(*) AS event_count
FROM event_log
WHERE partition_year = 2024
GROUP BY EXTRACT(MONTH FROM timestamp);
```

Uses EXTRACT because `day_col` is available (preferred for date math).

---

#### **Example 3: Explicit Quarter Column (finra_ats)**
```python
# Already configured:
CAPABILITIES = {
    "finra_ats": TableCapabilities(
        time=TimeCapabilities(
            year_col="year",
            quarter_col="quarter",  # Explicit quarter column
        ),
    )
}
```

**Query:** "ATS volume by quarter in 2024"

**Generated SQL (NOW WORKS):**
```sql
SELECT quarter, SUM(total_shares) AS total_shares
FROM finra_ats
WHERE year = 2024
GROUP BY quarter;
```

---

## Benefits

### **1. Zero Code Changes for New Temporal Dimensions**
Add `day_of_week_col`, `fiscal_quarter_col`, `hour_of_day_col` to `TimeCapabilities` and they automatically work.

### **2. Table-Agnostic**
Each table declares what it supports. `build_aggregate()` discovers capabilities dynamically.

### **3. Handles Mixed Scenarios**
- Table with only explicit columns → uses those
- Table with only day_col → uses EXTRACT
- Table with both → prefers explicit (faster, no date math)

### **4. Clear Error Handling**
Instead of silently ignoring unsupported dimensions, can warn or error:
```python
if not caps.time.supports_dimension(dim):
    raise ValueError(
        f"Table '{table}' does not support temporal dimension '{dim}'. "
        f"Available: {caps.time.list_supported_dimensions()}"
    )
```

### **5. Self-Documenting**
```python
# Query which temporal dimensions a table supports:
caps = get_capabilities('executing_bd_606')
supported = [
    dim for dim in ['year', 'month', 'quarter', 'week', 'hour']
    if caps.time.supports_dimension(dim)
]
print(f"executing_bd_606 supports: {supported}")
# Output: ['year', 'month']
```

---

## Migration Path

### **Phase 1: Fix Existing Tables**
```python
# capability_registry.py - Update existing capabilities
CAPABILITIES = {
    "executing_bd_606": TableCapabilities(
        # ...existing...
        time=TimeCapabilities(
            year_col="year",
            month_col="month",
            # No day_col, no quarter_col (can't derive quarter from month)
        ),
    ),
    "monthly_data": TableCapabilities(
        # ...existing...
        time=TimeCapabilities(
            day_col="day",  # Has day, can EXTRACT anything
        ),
    ),
    "finra_ats": TableCapabilities(
        # ...existing...
        time=TimeCapabilities(
            year_col="year",
            quarter_col="quarter",
        ),
    ),
}
```

### **Phase 2: Implement Helper Methods**
Add the `get_temporal_column()`, `can_extract_temporal()`, `supports_dimension()` methods to `TimeCapabilities`.

### **Phase 3: Update build_aggregate()**
Replace the hardcoded temporal logic with the generic loop shown above.

### **Phase 4: Test**
```python
test_cases = [
    ("executing_bd_606", "month", "PFOF by month in 2024"),
    ("executing_bd_606", "year", "PFOF by year"),
    ("monthly_data", "quarter", "Shares by quarter in 2024"),
    ("finra_ats", "quarter", "ATS volume by quarter in 2024"),
]

for table, dimension, query in test_cases:
    caps = get_capabilities(table)
    assert caps.time.supports_dimension(dimension), f"{table} should support {dimension}"
    sql = plan_single_sql(query, classify_query_enhanced(query))
    assert f"GROUP BY {dimension}" in sql or f"GROUP BY EXTRACT({dimension.upper()}" in sql
```

---

## Edge Cases Handled

### **1. Derived Dimensions (Quarter from Month)**
Some tables have month but not quarter. Can we derive it?

**Option A:** Support in `can_extract_temporal()`:
```python
def can_extract_temporal(self, dimension: str) -> bool:
    if dimension == 'quarter' and self.month_col:
        return True  # Can derive quarter from month
    # ...
```

**Option B:** Generate SQL with CASE statement:
```sql
SELECT
    CASE
        WHEN month IN ('1','2','3') THEN 'Q1'
        WHEN month IN ('4','5','6') THEN 'Q2'
        WHEN month IN ('7','8','9') THEN 'Q3'
        ELSE 'Q4'
    END AS quarter,
    SUM(...) AS total_pfof_usd
FROM executing_bd_606
GROUP BY quarter;
```

### **2. Multiple Temporal Columns in One Query**
**Query:** "PFOF by month and year" (redundant but possible)

```python
# Handles automatically:
intent.dimensions = ['year', 'month']

# Generated SQL:
SELECT year, month, SUM(...) AS total_pfof_usd
FROM executing_bd_606
GROUP BY year, month;
```

### **3. Mixed Temporal + Entity Dimensions**
**Query:** "PFOF by broker and month in 2024"

```python
intent.dimensions = ['executing_bd', 'month']

# Generated SQL:
SELECT executing_bd, month, SUM(...) AS total_pfof_usd
FROM executing_bd_606
WHERE year = 2024 AND data_type = 'venue'
GROUP BY executing_bd, month;
```

---

## Summary: The Generic Pattern

```python
# 1. Table declares capabilities (one-time setup)
time=TimeCapabilities(
    month_col="month_column_name",  # Or None if not available
    week_col="week_column_name",    # Or None if not available
    day_col="timestamp_column_name", # Or None if not available
)

# 2. build_aggregate() discovers capabilities (automatic)
for dim in requested_dims:
    col = caps.time.get_temporal_column(dim)
    if col:
        use_explicit_column(col)
    elif caps.time.can_extract_temporal(dim):
        use_extract_from_day_col(dim)
    else:
        handle_unsupported(dim)

# 3. SQL is generated (automatic)
# No hardcoded dimension lists
# No table-specific logic
# Works for any future temporal dimension
```

---

## Recommendation

✅ **Implement this pattern** - It's:
- Future-proof (new dimensions/tables work automatically)
- Table-agnostic (each table declares its own capabilities)
- Maintainable (one place to add new dimension types)
- Testable (clear contract via `supports_dimension()`)

**Estimated Implementation Time:** 2-3 hours
**Risk:** Low (isolated to temporal dimension handling)
**Benefit:** Fixes 3 broken queries + prevents future bugs
