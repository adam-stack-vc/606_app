# Cross-Table Enrichment Feature

Automatically enriches `executing_bd_606` query results with market context from `monthly_data`.

## Overview

When users ask questions about PFOF or broker activity, the system now automatically:
1. Executes the primary query on `executing_bd_606` 
2. Extracts the time period (year/month) from the query
3. Aggregates `monthly_data` for that period
4. Compares with other periods for ranking
5. Returns enriched insights alongside the primary results

## Key Features

### ✅ Non-Blocking Design
- **Primary query always succeeds** even if enrichment fails
- Enrichment wrapped in try-catch at multiple levels
- Falls back gracefully without affecting user experience

### 🐛 Debug Mode
- **Currently enabled** to show enrichment errors
- Set `debug=True` in `query.py` line 128
- Shows error details when enrichment fails
- **Later**: Set `debug=False` to hide errors in production

### 📊 Automatic Context
When successful, enrichment provides:
- Total market volume for the period
- Ranking vs other periods (e.g., "#1 highest volume")
- Notional value traded
- Tape breakdown (NYSE vs NASDAQ percentages)

## Example Output

### Query
```
"What month in 2024 did Robinhood get paid the most PFOF?"
```

### Response
```json
{
  "sql": "SELECT month, SUM(...) FROM executing_bd_606 WHERE ...",
  "results": [
    {"month": "12", "total_paid": 110995406.72}
  ],
  "insights": [
    "📊 2024-12 had the **highest equity trading volume** of the year",
    "📈 Total market volume: **256.5B shares** traded",
    "💰 Total notional value: **$12.8T**",
    "📊 Tape breakdown: NYSE 33.1% | NASDAQ 49.5%"
  ],
  "enrichment": {
    "has_enrichment": true,
    "time_period": {"year": 2024, "month": 12},
    "monthly_context": { ... }
  }
}
```

## Files Added

### `cross_table_enrichment.py`
Main enrichment module with 4 key functions:

1. **`extract_time_period(sql, results)`**
   - Extracts year/month from SQL WHERE clauses or result columns
   - Handles multiple date formats

2. **`get_monthly_volume_stats(year, month=None)`**
   - Queries `monthly_data` table for aggregated stats
   - Calculates rankings vs other periods
   - Returns volume, notional, trade counts

3. **`generate_context_insights(monthly_stats, month=None)`**
   - Converts raw stats into human-readable insights
   - Formats large numbers (billions, trillions)
   - Generates markdown-formatted messages

4. **`enrich_with_monthly_data(sql, results, debug=True)`**
   - Main entry point (non-blocking)
   - Orchestrates extraction, querying, and insight generation
   - Returns enriched data or safe fallback

## Files Modified

### `query.py`
- Added `from cross_table_enrichment import enrich_with_monthly_data`
- Wrapped enrichment call in try-catch (lines 122-146)
- Returns enrichment data in response
- **Debug mode currently ON** (line 128: `debug=True`)

## How It Works

```
User Query
    ↓
Primary SQL Generated (OpenAI)
    ↓
Primary Query Executed ✅ ALWAYS SUCCEEDS
    ↓
    ├→ Extract time period from SQL/results
    ↓
    ├→ Query monthly_data for that period
    ↓
    ├→ Calculate rankings and stats
    ↓
    ├→ Generate insights
    ↓
Return: Primary Results + Enrichment + Insights
```

## Testing

Run test script:
```bash
cd /Users/adamsussman/Documents/606_app/aws_app
python3 test_enrichment.py
```

Tests 3 scenarios:
1. Monthly PFOF query (should extract year + month)
2. Annual PFOF query (should extract year only)
3. Query with no results (primary succeeds, enrichment handles gracefully)

## Configuration

### Enable/Disable Debug Mode

**Current:** Debug mode ON (shows errors)
```python
# query.py line 128
enriched = enrich_with_monthly_data(sql, cleaned_results, debug=True)
```

**Production:** Hide enrichment errors
```python
# query.py line 128
enriched = enrich_with_monthly_data(sql, cleaned_results, debug=False)
```

### Customize Insights

Edit `generate_context_insights()` in `cross_table_enrichment.py`:
- Modify formatting (line 168-205)
- Add/remove insight types
- Change ranking thresholds
- Customize markdown formatting

## Database Schema Used

### monthly_data table
- `day` (date) - Trading day
- `market_participant` (varchar) - Exchange/venue
- `total_shares` (numeric) - Total share volume
- `total_notional` (numeric) - Total dollar volume
- `total_trade_count` (numeric) - Number of trades
- `tape_a/b/c_shares` (numeric) - Volume by tape

### executing_bd_606 table
- `year`, `month` - Time period columns
- Used for extracting time period from primary queries

## Future Enhancements

- [ ] Add more time period extraction patterns
- [ ] Support date ranges (Q1, H1, etc.)
- [ ] Add broker market share calculations
- [ ] Compare broker PFOF vs their volume share
- [ ] Add volatility/market condition indicators
- [ ] Support "compared to previous period" insights

## Error Handling

### Level 1: Inside `enrich_with_monthly_data()`
```python
try:
    # Extract, query, generate
except Exception as e:
    return safe_fallback(with_error_if_debug)
```

### Level 2: Inside `query.py`
```python
try:
    enriched = enrich_with_monthly_data(...)
except Exception as e:
    enrichment_result = {"error": str(e)}
```

### Result
✅ **Primary query ALWAYS returns**
✅ Enrichment failures logged but don't block response
✅ Debug mode shows what went wrong


