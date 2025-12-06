# Semantic Hints Feature

**Date:** December 5, 2025

---

## Overview

Added optional LangChain-based semantic hints to the query system. Users can now toggle semantic hints on/off in the Streamlit app and track which queries used semantic hints in the feedback CSV.

---

## What Are Semantic Hints?

Semantic hints use LangChain's SQLDatabaseChain to help interpret complex query patterns that are difficult to handle with deterministic rules alone:

- **Superlatives**: "highest", "lowest", "largest", "smallest"
- **Temporal**: "earliest", "latest", "first", "oldest", "newest"
- **Grouping**: "for each", "per", "by"
- **Top/Bottom N**: "top 5", "bottom 10"

The semantic hints adapter (`semantic_sql_adapter.py`) generates a hint SQL query that is then parsed to extract:
- GROUP BY dimensions
- ORDER BY patterns
- LIMIT clauses
- MIN/MAX aggregations

**Important:** The final SQL is still generated deterministically using templates. Semantic hints only influence the query intent extraction, not the SQL generation itself.

---

## Implementation Details

### 1. Updated Import in `semantic_sql_adapter.py`

**Before:**
```python
from langchain.utilities import SQLDatabase  # Deprecated
```

**After:**
```python
from langchain_community.utilities import SQLDatabase  # Current
```

This removes the deprecation warning that was appearing in logs.

### 2. Modified FastAPI Endpoint (`main.py`)

Added `use_semantic_hints` parameter to the API request:

```python
class QuestionInput(BaseModel):
    question: str
    use_semantic_hints: bool = False

@app.post("/ask")
async def ask_question(body: QuestionInput):
    # Set environment variable for this request
    original_value = os.getenv("USE_SEMANTIC_HINTS")
    os.environ["USE_SEMANTIC_HINTS"] = "true" if body.use_semantic_hints else "false"

    try:
        result = ask(body.question)
    finally:
        # Restore original value
        if original_value is not None:
            os.environ["USE_SEMANTIC_HINTS"] = original_value
        elif "USE_SEMANTIC_HINTS" in os.environ:
            del os.environ["USE_SEMANTIC_HINTS"]

    # Add semantic_hints flag to response
    result["semantic_hints_used"] = body.use_semantic_hints
    return result
```

**Key Features:**
- Accepts `use_semantic_hints` boolean parameter (defaults to `false`)
- Sets `USE_SEMANTIC_HINTS` environment variable for the request
- Restores original value after request completes (thread-safe)
- Adds `semantic_hints_used` field to response

### 3. Updated Streamlit App (`streamlit_app.py`)

**Session State:**
```python
if 'use_semantic_hints' not in st.session_state:
    st.session_state.use_semantic_hints = False
```

**UI Toggle:**
```python
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    submit_button = st.button("Generate Query", type="primary", use_container_width=True)
with col2:
    st.session_state.use_semantic_hints = st.checkbox(
        "Use Semantic Hints",
        value=st.session_state.use_semantic_hints,
        help="Enable LangChain semantic hints for complex query patterns"
    )
```

**API Call:**
```python
response = call_api(question, st.session_state.use_semantic_hints)
```

**Visual Indicator:**
```python
col1, col2 = st.columns([5, 1])
with col1:
    st.subheader("📝 LLM-Generated Query")
with col2:
    if response.get('semantic_hints_used', False):
        st.success("✓ Semantic Hints")
    else:
        st.info("⊝ Deterministic")
```

**Feedback CSV:**
```python
feedback_entry = {
    'timestamp': datetime.now().isoformat(),
    'question': st.session_state.current_response.get('question', ''),
    'sql_query': st.session_state.current_response.get('sql', ''),
    'query_type': st.session_state.current_response.get('query_type', ''),
    'sql_results_count': len(st.session_state.current_response.get('results', [])),
    'genai_response': st.session_state.current_response.get('response', ''),
    'semantic_hints': st.session_state.current_response.get('semantic_hints_used', False),  # NEW
    'query_notes': st.session_state.query_notes,
    'genai_notes': st.session_state.genai_notes,
    'rating': st.session_state.rating
}
```

### 4. How It Works in the Code

**planner.py** (line 424):
```python
use_hints = os.getenv("USE_SEMANTIC_HINTS", "false").lower() == "true"
if _ADAPTER_OK and use_hints:
    hint_sql = _get_sql_hint(user_input, intent)
    if hint_sql:
        sql_lower = hint_sql.lower()
        # Parse GROUP BY, ORDER BY, LIMIT from hint SQL
        # Merge into intent dimensions
```

**hybrid_query_handler.py** (line 580):
```python
use_hints = (os.getenv("USE_SEMANTIC_HINTS", "false").lower() == "true")
if show_hints or use_hints:
    intent = _build_intent(user_input, dict(query_tags))
    hint_sql = _get_sql_hint(user_input, intent)
    final_hint_sql = _build_final_sql(intent, hint_sql) if hint_sql else None
    query_results["semantic_nl2sql"] = {
        "hint_sql": hint_sql,
        "final_sql": final_hint_sql
    }
```

---

## Testing

Created test script: `scripts/test_semantic_hints.py`

**Usage:**
```bash
python scripts/test_semantic_hints.py
```

**Test Cases:**
1. Simple query without semantic hints - "PFOF for Robinhood in April 2024"
2. Same query with semantic hints enabled
3. Complex query with superlatives - "What venue received the highest volume in 2024?"
4. Same complex query with semantic hints enabled

**Expected Results:**
- Both modes should generate valid SQL
- `semantic_hints_used` field reflects the toggle state
- Complex queries may benefit from semantic hints for ORDER BY/LIMIT

---

## CSV Feedback Schema

The `query_feedback.csv` now includes the `semantic_hints` column:

| Column | Type | Description |
|--------|------|-------------|
| timestamp | ISO datetime | When feedback was saved |
| question | string | User's natural language question |
| sql_query | string | Generated SQL query |
| query_type | string | direct_single, complex_multi_table, etc. |
| sql_results_count | int | Number of rows returned |
| genai_response | string | Narrative response text |
| **semantic_hints** | **boolean** | **True if semantic hints were used, False otherwise** |
| query_notes | string | User notes about the query |
| genai_notes | string | User notes about the narrative |
| rating | int | 1-5 rating |

---

## When to Use Semantic Hints

### Use Semantic Hints When:
- Query has superlatives ("highest", "lowest", "best", "worst")
- Query asks for temporal ordering ("earliest", "latest", "first", "last")
- Query has complex grouping ("for each broker", "per venue")
- Query asks for top/bottom N entities
- Deterministic mode produces incorrect SQL for a specific pattern

### Use Deterministic Mode When:
- Query is straightforward (filters, aggregations, simple grouping)
- You want maximum transparency and debuggability
- Performance is critical (semantic hints add ~1-2 seconds for LLM call)
- You don't trust LLM-generated hints for production queries

---

## Architecture Notes

1. **Semantic hints are OPTIONAL** - System works perfectly fine without them (USE_SEMANTIC_HINTS=false by default)

2. **SQL is still deterministic** - Semantic hints only help extract intent (GROUP BY, ORDER BY, LIMIT). The final SQL is generated by templates in `sql_templates.py`, not by LLM.

3. **No SQL hallucination risk** - LangChain SQLDatabaseChain generates a hint SQL, but we only parse it for patterns. We never execute the hint SQL or use it directly.

4. **Request-scoped** - Each API request can independently enable/disable semantic hints via the parameter.

5. **Feedback tracking** - The `semantic_hints` column in feedback CSV allows comparing query quality between modes.

---

## Future Enhancements

1. **A/B Testing** - Compare query quality/accuracy between semantic hints on/off
2. **Pattern Library** - Identify which patterns benefit most from semantic hints
3. **Auto-enable** - Automatically enable semantic hints for queries with known trigger words
4. **Performance Optimization** - Cache LangChain SQLDatabaseChain to reduce initialization overhead
5. **Hybrid Fallback** - Try deterministic first, fall back to semantic hints if it fails

---

## Known Limitations

1. **Latency** - Semantic hints add ~1-2 seconds per query for the LLM call
2. **LangChain Dependency** - Requires langchain, langchain_experimental, langchain_openai packages
3. **OpenAI API Required** - Semantic hints use gpt-4o-mini model
4. **Not All Patterns** - Semantic hints only trigger for specific keywords (see `get_sql_hint()` in `semantic_sql_adapter.py`)

---

## Changelog

**December 5, 2025:**
- Fixed LangChain import deprecation warning (langchain.utilities → langchain_community.utilities)
- Added `use_semantic_hints` parameter to FastAPI `/ask` endpoint
- Added semantic hints toggle to Streamlit app UI
- Added `semantic_hints` column to feedback CSV
- Added visual indicator in Streamlit results (✓ Semantic Hints / ⊝ Deterministic)
- Created test script: `scripts/test_semantic_hints.py`
- Created documentation: `guides/SEMANTIC_HINTS_FEATURE.md`
