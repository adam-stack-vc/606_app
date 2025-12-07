from __future__ import annotations

"""
llm_intent_extractor.py
Uses LLM to extract structured intent from natural language queries.
Updated to return StructuredIntent Pydantic models for the Neuro-Symbolic engine.
"""

import os
import json
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# Import the Pydantic models
from query_models import StructuredIntent, Period, Filters
from capability_registry import REGISTRY

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _build_schema_context() -> str:
    """Build schema context from capability registry for LLM prompt."""
    schema_lines = []

    for table_name, caps in REGISTRY.items():
        schema_lines.append(f"\n## Table: {table_name}")
        if caps.notes:
            schema_lines.append(f"Purpose: {caps.notes}")

        schema_lines.append(f"Dimensions (GROUP BY): {', '.join(sorted(caps.allowed_dimensions))}")
        schema_lines.append(f"Metrics: {', '.join(sorted(caps.allowed_metrics))}")

        # Time columns
        time_cols = []
        if caps.time.year_col:
            time_cols.append(f"year ({caps.time.year_col})")
        if caps.time.month_col:
            time_cols.append(f"month ({caps.time.month_col})")
        if caps.time.quarter_col:
            time_cols.append(f"quarter ({caps.time.quarter_col})")
        if caps.time.day_col:
            time_cols.append(f"day ({caps.time.day_col})")
        if time_cols:
            schema_lines.append(f"Time columns: {', '.join(time_cols)}")

    return "\n".join(schema_lines)


SYSTEM_PROMPT = """You are an expert at extracting structured intent from natural language database queries about SEC Rule 606 financial data.

Your task is to analyze the user's question and return a JSON object representing the query intent. This intent will be used to generate deterministic SQL using a strict compiler.

# Available Tables and Schema
{schema_context}

# Operation Types
- **list**: Return distinct values (e.g., "list all brokers", "show venues")
- **aggregate**: Sum/count/avg across rows, optionally grouped by dimensions (e.g., "total PFOF by broker")
- **topN**: Top N results ordered by metric (e.g., "top 5 brokers by PFOF")
- **top_per_group**: Top N within each group (e.g., "top venue per broker", "top participant per quarter")
- **count**: Count distinct entities (e.g., "how many venues did X use") - use count_dimension field
- **per_entity_average**: Average metric per entity (e.g., "average PFOF per venue") - use per_entity field
- **earliest**: Earliest record by time (e.g., "first month with data", "when did it start")
- **latest**: Latest record by time (e.g., "most recent quarter", "last available data")
- **cross_table_list**: List entities across all tables (e.g., "list all entities", "show all market participants")
- **multi**: Complex queries requiring join/synthesis across tables (e.g., ratios between tables, market share)
- **string_length**: Longest/shortest name

# Metric Types
- **pfof**: Payment for order flow (executing_bd_606 only)
- **volume**: Estimated volume from cents-per-hundred (executing_bd_606) OR total shares/notional (monthly_data, finra_ats)
- **trades**: Trade count (monthly_data, finra_ats)
- **pfof_and_volume**: Both PFOF and estimated volume (executing_bd_606 only)
- **tape_a**: NYSE-listed stocks volume
- **tape_b**: NASDAQ-listed stocks volume
- **tape_c**: Other listings including ETFs
- **tape**: All tapes combined (monthly_data)
- **venues**: Used for counting venues

# Critical Rules
1. **Estimated Volume**: If the user asks for "estimated volume" or "volume" from a broker (executing_bd_606), SET metric="volume". The compiler will handle the complex calculation.
2. **Earliest/Latest**: If the user asks for "earliest month", "first month", "when did X start", use operation="earliest". Do NOT use "aggregate".
3. **List Venues**: If asking to "list venues for broker X", use operation="list" and dimensions=["venues"].
4. **Multi-Table Ratios**: If the user asks for a **ratio**, **percentage**, or **comparison** involving "PFOF" (606 table) and "Total Market Volume" or "Tape Volume" (monthly_data table), you MUST use **operation="multi"**.
   - Example: "Ratio of PFOF to Tape A volume" -> operation="multi"
   - Example: "Robinhood's share of total market volume" -> operation="multi"
   - Do NOT try to calculate this in a single query.
5. **Entity Filters**:
   - "PFOF **from** [entity]" → entity is a **venue** (filters.venues)
   - "PFOF **for** [entity]" → entity is a **broker** (filters.executing_bd)
   - "Robinhood" is always a broker (executing_bd).
   - "Citadel" is always a venue/wholesaler (venues).

# Response Format
Return ONLY a valid JSON object matching this structure:
{{
  "metric": "pfof|volume|trades|...",
  "operation": "aggregate|topN|list|earliest|latest|multi|...",
  "dimensions": ["dimension1", "dimension2"],
  "period": {{ "year": 2024, "month": 6, "quarter": 2 }},
  "filters": {{
    "data_type": "venue",
    "executing_bd": "Robinhood",
    "venues": "Citadel",
    "stock_group": "SP500",
    "ats_name": "UBS ATS",
    "market_participant": "NASDAQ"
  }},
  "top_n": 5,
  "order_by": "metric_name",
  "order_desc": true,
  "count_dimension": "venue", 
  "per_entity": "venue",
  "is_longest": true,
  "entities": {{ "venue": "Citadel" }} 
}}

Examples:
1. "What was the estimated volume for Robinhood in Q1 2024?"
   -> metric="volume", operation="aggregate", period={{year:2024, quarter:1}}, filters={{executing_bd: "Robinhood"}}
2. "Earliest month with non-zero PFOF in 2025"
   -> metric="pfof", operation="earliest", period={{year:2025}}
3. "List venues used by Robinhood"
   -> operation="list", dimensions=["venues"], filters={{executing_bd: "Robinhood"}}
4. "What month had the highest ratio of PFOF to Tape A volume?"
   -> operation="multi"
"""


def extract_intent_with_llm(user_input: str, model: str = "gpt-4o-mini") -> Optional[StructuredIntent]:
    """
    Use LLM to extract structured intent from natural language query.
    Returns a Pydantic StructuredIntent object.
    """
    try:
        schema_context = _build_schema_context()
        
        system_prompt = SYSTEM_PROMPT.format(
            schema_context=schema_context
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"},
            temperature=0.0, 
            max_tokens=500
        )

        intent_json = json.loads(response.choices[0].message.content)
        
        # Validate and parse with Pydantic
        return StructuredIntent(**intent_json)

    except Exception as e:
        print(f"LLM intent extraction failed: {e}")
        return None
