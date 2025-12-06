# Critical Fix: Venue Resolution False Positives

## Problem

The venue resolution function was causing false positives by matching partial words instead of complete aliases.

### Examples of False Matches:

| Query | Word Matched | Alias in DB | False Venue Detected |
|-------|-------------|-------------|---------------------|
| "Compare PFOF **and** volume by broker" | "and" | "engl**and**er" part of "israel englander" | Israel A. Englander & Co., Inc. |
| "Top venue **per** broker" | "per" | "**per**shing" | Pershing |
| "PFOF for each broker in **2024**" | Would match any venue with numbers | Various | Random venues |

### Root Cause

**File:** `multi_table_query_framework.py:764-784`

The original algorithm:
```python
# BROKEN CODE (before fix)
words = user_input.lower().split()
for word in words:
    clean_word = re.sub(r'[^\w]', '', word)
    if len(clean_word) < 3 or clean_word in generic_words:
        continue

    # ❌ SUBSTRING SEARCH - matches partial words!
    cursor.execute(
        "SELECT canonical_name FROM venue_mapping WHERE alias ILIKE %s LIMIT 1",
        (f"%{clean_word}%",)  # ← Problem: %word% matches substrings
    )
```

**Why it fails:**
1. Splits query into individual words: `["compare", "pfof", "and", "estimated", ...]`
2. For each word, does SQL: `WHERE alias ILIKE '%word%'`
3. Substring matching means:
   - `%and%` matches "engl**and**er"
   - `%per%` matches "**per**shing"
   - `%israel%` matches "**israel** englander"
   - Any short word could match part of a longer alias

## Solution

Replace substring matching with **word-boundary regex matching** of complete aliases.

### New Algorithm

**File:** `multi_table_query_framework.py:764-810`

```python
# FIXED CODE
# 1. Load all venue mappings from database
cursor.execute("SELECT canonical_name, aliases FROM venue_mapping")
venue_mappings = cursor.fetchall()

text = user_input.lower()

# 2. Define comprehensive generic words list
generic_words = {'each', 'broker', 'brokers', 'venue', 'venues', 'exchange',
                'market', 'volume', 'pfof', 'estimated', 'options', 'option',
                'stocks', 'stock', 'shares', 'share', 'tape', 'top', 'per',
                'highest', 'lowest', 'most', 'least', 'compare', 'and', 'by',
                'for', 'in', 'the', 'a', 'an', 'is', 'are', 'was', 'were',
                'total', 'sum', 'count', 'avg', 'average'}

# 3. Try to match complete aliases using word boundaries
for canonical_name, aliases_json in venue_mappings:
    aliases = json.loads(aliases_json)

    for alias in aliases:
        alias_lower = alias.lower().strip()

        # Skip single-word aliases that are generic
        if ' ' not in alias_lower and alias_lower in generic_words:
            continue

        # Skip very short aliases (< 3 chars)
        if len(alias_lower) < 3:
            continue

        # ✅ WORD BOUNDARY MATCHING - matches complete words/phrases only!
        pattern = r'\b' + re.escape(alias_lower) + r'\b'
        if re.search(pattern, text):
            return canonical_name
```

### Key Improvements

1. **Word Boundary Matching (`\b`):**
   - `\bisrael englander\b` matches "israel englander" as a complete phrase ✓
   - Won't match "and" inside "engl**and**er" ✓
   - Won't match "per" inside "**per**shing" ✓

2. **Generic Words Filter:**
   - Skips single-word aliases that are generic terms
   - Prevents matching common words like "and", "per", "by", "for", etc.

3. **Multi-word Phrase Support:**
   - "israel englander" is matched as a complete phrase
   - More accurate for multi-word venue names

4. **Length Check:**
   - Skips aliases shorter than 3 characters
   - Avoids false positives from very short aliases

## Additional Safeguards

Added skip conditions to prevent venue resolution in grouping contexts:

```python
# Skip queries grouping "by venue"
if re.search(r'\bby\s+(venue|venues|exchange|market)\b', text):
    return None

# Skip queries grouping "by broker"
if re.search(r'\bby\s+(broker|brokers?|executing)', text):
    return None

# Skip top-per-group patterns
if re.search(r'\btop\b.*\b(venue|venues)\b.*\bper\b', text):
    return None
```

**Rationale:** When a query says "by broker" or "by venue", it's asking to GROUP BY that dimension, not filter to a specific entity.

## Test Cases

### Before Fix (Broken) vs After Fix (Working)

| Query | Before | After |
|-------|--------|-------|
| "Compare PFOF and volume by broker in 2024" | ❌ Detected "Israel A. Englander" from word "and" | ✅ No venue detected |
| "Top venue per broker by PFOF" | ❌ Detected "Pershing" from word "per" | ✅ No venue detected |
| "PFOF for Citadel in April 2024" | ✅ Detected Citadel correctly | ✅ Detects Citadel correctly |
| "Volume for Israel Englander in Q2" | ✅ Detected (but for wrong reason) | ✅ Detects "israel englander" phrase |
| "Total PFOF for each venue in 2024" | ✅ Skipped (generic phrase) | ✅ Skipped (generic phrase) |

## Impact

### Queries Fixed:
- ✅ "Compare PFOF and estimated volume by broker in 2024"
- ✅ "Top venue per broker by PFOF in 2024"
- ✅ Any query with "and", "per", "by" in grouping context
- ✅ Queries mentioning partial words that happen to be substrings of venue aliases

### False Positives Eliminated:
- Single common words no longer match venue aliases
- Grouping queries ("by broker", "per venue") no longer detect venues
- Partial word matches eliminated

### Performance:
- Slightly slower (loads all venues from DB instead of word-by-word search)
- But more accurate and prevents false positives
- Acceptable tradeoff given the improved accuracy

## Related Issue: Broker Resolution

Broker resolution (`resolve_executing_bd`) **already used word boundaries** (line 847):
```python
pattern = r'\b' + re.escape(alias.lower()) + r'\b'
```

So broker resolution didn't have the same substring matching bug. This fix brings venue resolution to parity with broker resolution.

## Files Modified

1. **multi_table_query_framework.py**
   - Lines 764-810: Rewrote venue resolution algorithm
   - Lines 751-753: Added "by broker" skip condition
   - Lines 772-778: Expanded generic words list

## Recommendation

Consider applying similar word-boundary logic to:
- ATS name resolution (if it exists)
- Market participant resolution (if it exists)
- Any other entity resolution functions

## Testing Commands

```python
# Test 1: Should NOT detect venue
"Compare PFOF and estimated volume by broker in 2024"
# Expected: No venue filter, groups by executing_bd

# Test 2: Should NOT detect venue
"Top venue per broker by PFOF in 2024"
# Expected: No venue filter, top-per-group query

# Test 3: SHOULD detect venue
"PFOF for Citadel in April 2024"
# Expected: WHERE venues = 'Citadel Securities LLC'

# Test 4: SHOULD detect venue (phrase)
"Total volume for Israel Englander in Q2 2024"
# Expected: WHERE venues = 'Israel A. Englander & Co., Inc.'
```

---

## Summary

**Before:** Substring matching caused false positives when common words appeared in queries
**After:** Word-boundary matching ensures only complete alias phrases are matched
**Result:** Eliminates false venue detection in grouping/aggregation queries
