# Semantic Hints Testing Guide

**Date:** December 5, 2025

---

## Testing Completed

All semantic hints functionality has been tested and verified working end-to-end.

---

## Test Scripts

### 1. `scripts/test_semantic_hints.py`
Tests the FastAPI endpoint with semantic hints on/off.

**Usage:**
```bash
python scripts/test_semantic_hints.py
```

**Tests:**
- Simple query without semantic hints
- Same query with semantic hints enabled
- Complex query with superlatives (both modes)

### 2. `scripts/test_full_workflow.py`
Tests the complete workflow: API call → save feedback → read back CSV.

**Usage:**
```bash
python scripts/test_full_workflow.py
```

**Tests:**
- API call with semantic_hints=False
- API call with semantic_hints=True
- Saving feedback to CSV with proper quoting
- Reading back CSV with pandas
- Verifying semantic_hints column values

### 3. `scripts/fix_csv.py`
Fixes corrupted CSV files and migrates to new schema with semantic_hints column.

**Usage:**
```bash
python scripts/fix_csv.py
```

**What it does:**
- Backs up existing CSV to `query_feedback_broken.csv`
- Reads old format CSV (9 columns)
- Adds `semantic_hints` column (default: False)
- Writes clean CSV with proper QUOTE_ALL quoting
- Handles multiline SQL queries correctly

### 4. `scripts/test_streamlit_csv.py`
Tests CSV reading/writing logic used by Streamlit app.

**Usage:**
```bash
python scripts/test_streamlit_csv.py
```

**Tests:**
- Reading current CSV
- Checking header structure
- Validating field counts
- Testing migration logic

### 5. `scripts/test_streamlit_integration.py`
Tests actual Streamlit app functions and sidebar logic.

**Usage:**
```bash
python scripts/test_streamlit_integration.py
```

**Tests:**
- Reading production CSV
- Simulating new feedback entry
- Testing sidebar statistics (avg rating, etc.)
- CSV export functionality

---

## Manual Testing with Streamlit App

### Steps:

1. **Start FastAPI server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

2. **Start Streamlit app:**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Test without semantic hints:**
   - Enter question: "PFOF for Robinhood in April 2024"
   - Leave "Use Semantic Hints" checkbox unchecked
   - Click "Generate Query"
   - Verify badge shows "⊝ Deterministic"
   - Add notes and rating
   - Click "Save Feedback"
   - Verify feedback saved successfully

4. **Test with semantic hints:**
   - Enter question: "What venue received the highest volume in 2024?"
   - Check "Use Semantic Hints" checkbox
   - Click "Generate Query"
   - Verify badge shows "✓ Semantic Hints"
   - Add notes and rating
   - Click "Save Feedback"
   - Verify feedback saved successfully

5. **Verify CSV:**
   - Check sidebar shows correct total entries
   - Download feedback CSV
   - Open in spreadsheet app
   - Verify `semantic_hints` column shows True/False correctly
   - Verify multiline SQL queries are properly quoted

---

## CSV Migration

If you have an existing `query_feedback.csv` without the `semantic_hints` column:

1. **Automatic migration:**
   The Streamlit app will automatically detect missing column and migrate on next save.

2. **Manual migration:**
   ```bash
   python scripts/fix_csv.py
   ```

   This will:
   - Backup old file to `query_feedback_broken.csv`
   - Create new file with `semantic_hints` column
   - Set all existing rows to `semantic_hints=False`

---

## Troubleshooting

### Issue: CSV parsing error "Expected X fields, saw Y"

**Cause:** Multiline SQL queries not properly quoted.

**Fix:**
```bash
python scripts/fix_csv.py
```

### Issue: semantic_hints column missing in CSV

**Cause:** Using old CSV format.

**Fix:** Let Streamlit app auto-migrate on next save, or run:
```bash
python scripts/fix_csv.py
```

### Issue: semantic_hints always shows False

**Cause:** Not checking the "Use Semantic Hints" checkbox in Streamlit.

**Fix:** Check the checkbox before clicking "Generate Query".

### Issue: API doesn't return semantic_hints_used field

**Cause:** Old server version running.

**Fix:** Restart uvicorn server:
```bash
pkill -f uvicorn
uvicorn main:app --reload --port 8000
```

---

## Test Results

All tests passing as of December 5, 2025:

- ✅ FastAPI endpoint accepts `use_semantic_hints` parameter
- ✅ API response includes `semantic_hints_used` field
- ✅ Streamlit checkbox controls semantic hints
- ✅ Visual indicator shows correct mode (✓ or ⊝)
- ✅ CSV saves semantic_hints column correctly
- ✅ Pandas can read CSV with multiline SQL
- ✅ Sidebar statistics work correctly
- ✅ CSV export/download works
- ✅ Auto-migration from old format works
- ✅ QUOTE_ALL properly escapes SQL queries

---

## Performance Notes

**With Semantic Hints Enabled:**
- Adds ~1-2 seconds latency per query (LLM call to generate hints)
- Uses OpenAI API credits (gpt-4o-mini model)

**Without Semantic Hints (Deterministic):**
- No additional latency
- No LLM API calls (except for narrative synthesis)
- Faster and more predictable

---

## Next Steps

1. **A/B Testing:** Compare query quality between modes using feedback CSV
2. **Pattern Analysis:** Identify which query types benefit most from semantic hints
3. **Auto-enable:** Automatically enable semantic hints for queries with superlatives
4. **Cost Analysis:** Track OpenAI API usage for semantic hints
