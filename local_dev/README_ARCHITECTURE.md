# 606 Query System Architecture

This system allows users to query SEC Rule 606 financial data using natural language. It employs a **Neuro-Symbolic Architecture** that combines the linguistic power of Large Language Models (LLMs) with the reliability of a deterministic SQL compiler.

## Architecture Overview

### 1. The Neuro-Symbolic Engine
Unlike traditional "Text-to-SQL" systems that ask an LLM to write raw SQL (which is error-prone), this system uses a two-step process:

1.  **Intent Extraction (The "Neuro" Part):** An LLM (`gpt-4o-mini`) analyzes the user's question and extracts a **Structured Intent** (JSON). It does *not* write SQL. It identifies:
    *   **Metric:** PFOF, Volume, Trades, etc.
    *   **Operation:** Aggregate, TopN, Top-Per-Group, Count, etc.
    *   **Filters:** Broker="Robinhood", Venue="Citadel", Year=2024.
    *   **Dimensions:** Group by "month", "venue", etc.

2.  **SQL Compilation (The "Symbolic" Part):** A deterministic Python compiler (`query_compiler.py`) takes this JSON object and generates syntactically perfect SQL. It handles:
    *   **Schema Rules:** Knows which columns belong to which tables.
    *   **Complex Logic:** Correctly constructs `PARTITION BY` clauses for "top venue per broker".
    *   **Entity Resolution:** Automatically maps "Citadel" to `venues` column and "Robinhood" to `executing_bd`.

### 2. Core Components

*   `planner.py`: The entry point. Orchestrates the extraction and compilation process.
*   `llm_intent_extractor.py`: Handles the prompt engineering to get clean JSON from the LLM. Uses `StructuredIntent` Pydantic models.
*   `query_models.py`: Defines the strict Pydantic schemas (`StructuredIntent`, `Filters`, `Period`) that the LLM must adhere to.
*   `query_compiler.py`: The heavy lifter. Contains the logic to turn an Intent object into a SQL string.
*   `hybrid_query_handler.py`: A legacy router that still handles some very complex multi-step queries (like "Compare X and Y").

## Workflow

1.  **User Input:** "Who paid Robinhood the most PFOF in Jan 2024?"
2.  **Extraction:** `llm_intent_extractor.py` prompts GPT-4o-mini.
3.  **Intent Object:**
    ```json
    {
      "metric": "pfof",
      "operation": "topN",
      "filters": { "executing_bd": "Robinhood", "data_type": "venue" },
      "period": { "year": 2024, "month": 1 },
      "dimensions": ["venues"],
      "top_n": 1
    }
    ```
4.  **Compilation:** `query_compiler.py` receives this object.
    *   Selects table `executing_bd_606`.
    *   Builds `WHERE` clause from filters + period.
    *   Builds `ORDER BY` from metric logic.
5.  **Execution:** The generated SQL is run against the PostgreSQL database.
6.  **Synthesis:** An LLM summarizes the rows into a natural language answer.

## Multi-Table vs. Single-Table

*   **Single-Table Queries:** Handled entirely by the Neuro-Symbolic Planner described above. This covers 90% of questions (PFOF analysis, market volume, ATS stats).
*   **Multi-Table Queries:** Queries that require joining data across domains (e.g., "Compare Robinhood's PFOF to overall market volume") are currently routed to `hybrid_query_handler.py`. This uses a "Chain of Thought" approach to run multiple independent queries and synthesize the results.

## Adding New Capabilities

To add a new feature (e.g., a new metric):
1.  Update `query_models.py` to allow the new metric name in the `Literal`.
2.  Update `llm_intent_extractor.py` system prompt to explain the new metric.
3.  Update `query_compiler.py` to define the SQL snippet for that metric in `_metric_select`.
