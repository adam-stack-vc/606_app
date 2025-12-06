# How to Integrate a New Table

Adding a new table (e.g., `options_flow_data`) to the Neuro-Symbolic system requires updates in 3 places.

## 1. Define the Schema (`capability_registry.py`)
Register the table so the system knows its columns and capabilities.

```python
# capability_registry.py
REGISTRY["options_flow_data"] = TableCapabilities(
    columns=["ticker", "expiry", "strike", "premium"],
    allowed_metrics=["premium", "contracts_traded"],
    allowed_dimensions=["ticker", "expiry"],
    time=TimeCapabilities(day_col="trade_date")
)
```

## 2. Update the Intent Model (`query_models.py`)
Update the Pydantic models to allow filtering by the new table's columns.

```python
# query_models.py
class Filters(BaseModel):
    # ... existing filters ...
    ticker: Optional[str] = None  # <--- Add this
    expiry: Optional[str] = None  # <--- Add this
```

## 3. Teach the LLM (`llm_intent_extractor.py`)
Add a description and examples to the System Prompt so the LLM knows when to use this table.

```python
# llm_intent_extractor.py (SYSTEM_PROMPT)
"""
...
- **premium**: Total option premium (options_flow_data)
...
Rules:
...
10. For questions about "options", "calls", "puts", use table "options_flow_data".
"""
```

## 4. Implement SQL Logic (`query_compiler.py`)
Tell the compiler how to generate SQL for this table.

```python
# query_compiler.py

def _get_table_for_intent(intent):
    # ...
    if intent.metric == "premium":
        return "options_flow_data"
    # ...

def _metric_select(table, intent):
    # ...
    if table == "options_flow_data":
        if intent.metric == "premium":
            return "SUM(premium) AS total_premium"
    # ...
```

## 5. Verify
Run a test question: "Total premium for AAPL calls in 2024".
1.  Check if LLM extracts `table="options_flow_data"` and `filters.ticker="AAPL"`.
2.  Check if Compiler generates `SELECT SUM(premium)... FROM options_flow_data...`.
