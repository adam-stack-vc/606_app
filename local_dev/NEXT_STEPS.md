# Suggested Next Steps for Accuracy Improvement

The Neuro-Symbolic engine has significantly improved stability (71% benchmark pass rate). To reach >90% accuracy, follow these steps:

## 1. Refine Entity Resolution (RAG)
*   **Problem:** The current system relies on the LLM knowing that "Citadel" is a venue. If a user asks about a less famous firm, the LLM might guess wrong.
*   **Solution:** Implement a "Pre-Check" tool. Before intent extraction, search the database:
    *   `search_entity("UnknownFirm")` -> Returns "Found in `venues` column".
    *   Inject this context into the LLM prompt: "Context: 'UnknownFirm' is a Venue."

## 2. Expand Benchmark Coverage
*   **Problem:** The current benchmark (46 questions) covers PFOF and Volume well, but lacks edge cases for "String Length", "Cross-Table Lists", and "Complex Filtering".
*   **Action:** Add 20+ more questions to `eval/nl_sql_pairs_additional.jsonl` specifically targeting:
    *   "Longest broker name"
    *   "Brokers with PFOF > $1M" (HAVING clauses)
    *   "Venues used by both Robinhood and Schwab"

## 3. Handle "HAVING" Clauses
*   **Gap:** The `StructuredIntent` model currently supports `WHERE` filters nicely, but lacks a dedicated field for `HAVING` (filters on aggregates).
*   **Action:**
    *   Add `having: Optional[str]` to `StructuredIntent` in `query_models.py`.
    *   Update `query_compiler.py` to generate `HAVING` clauses when this field is present.

## 4. Multi-Table Neuro-Symbolic Support
*   **Gap:** Complex multi-table joins currently fallback to the legacy `hybrid_query_handler.py`.
*   **Action:** Enhance `StructuredIntent` to support a `subqueries` list (already present in the model but unused). Implement logic in `query_compiler.py` to compile these into `WITH` clauses or `JOIN`s.

## 5. Feedback Loop Integration
*   **Action:** Connect the "Thumbs Down" button in the Streamlit app to a "Training Set".
*   When a query fails, human review should generate the *correct* `StructuredIntent` JSON.
*   Add this example to `llm_intent_extractor.py`'s few-shot examples to prevent regression.
