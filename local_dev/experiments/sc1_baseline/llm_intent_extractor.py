from __future__ import annotations

"""
llm_intent_extractor.py
Uses LLM to extract structured intent from natural language queries.
Replaces manual pattern detection while keeping deterministic SQL templates.
"""

import os
import json
from typing import Optional, Dict
from openai import OpenAI
from dotenv import load_dotenv

from query_intent import QueryIntent
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


def _build_examples() -> str:
    """Build example query → intent mappings for few-shot learning."""
    examples = [
        {
            "query": "Who paid Robinhood PFOF in June 2024",
            "intent": {
                "table": "executing_bd_606",
                "operation": "aggregate",
                "metric": "pfof",
                "aggregation": "SUM",
                "dimensions": ["venues"],
                "entities": {"executing_bd": "Robinhood"},
                "period": {"year": 2024, "month": 6},
                "filters": {"data_type": "venue"}
            }
        },
        {
            "query": "PFOF from Citadel in April 2024",
            "intent": {
                "table": "executing_bd_606",
                "operation": "aggregate",
                "metric": "pfof",
                "aggregation": "SUM",
                "dimensions": [],
                "entities": {"venue": "Citadel"},
                "period": {"year": 2024, "month": 4},
                "filters": {"data_type": "venue"}
            }
        },
        {
            "query": "Top 5 brokers by PFOF in 2024",
            "intent": {
                "table": "executing_bd_606",
                "operation": "topN",
                "metric": "pfof",
                "aggregation": "SUM",
                "dimensions": ["executing_bd"],
                "period": {"year": 2024},
                "filters": {"data_type": "venue"},
                "limit": 5,
                "order_desc": True
            }
        },
        {
            "query": "For each quarter, top market participant by total shares in 2024",
            "intent": {
                "table": "monthly_data",
                "operation": "top_per_group",
                "metric": "volume",
                "aggregation": "SUM",
                "dimensions": ["quarter", "market_participant"],
                "period": {"year": 2024},
                "limit": 1,
                "order_desc": True
            }
        },
        {
            "query": "List distinct quarters for 2024 ATS data",
            "intent": {
                "table": "finra_ats",
                "operation": "list",
                "dimensions": ["quarter"],
                "period": {"year": 2024}
            }
        },
        {
            "query": "Compare PFOF and estimated volume by broker in 2024",
            "intent": {
                "table": "executing_bd_606",
                "operation": "aggregate",
                "metric": "pfof_and_volume",
                "aggregation": "SUM",
                "dimensions": ["executing_bd"],
                "period": {"year": 2024},
                "filters": {"data_type": "venue"}
            }
        },
        {
            "query": "What brokers traded in Q2 2024",
            "intent": {
                "table": "executing_bd_606",
                "operation": "list",
                "dimensions": ["executing_bd"],
                "period": {"year": 2024, "quarter": 2}
            }
        },
        {
            "query": "Total trades for each ATS in 2024",
            "intent": {
                "table": "finra_ats",
                "operation": "aggregate",
                "metric": "trades",
                "aggregation": "SUM",
                "dimensions": ["ats_name"],
                "period": {"year": 2024}
            }
        },
        {
            "query": "Which month had the lowest PFOF for Citadel in 2024",
            "intent": {
                "table": "executing_bd_606",
                "operation": "topN",
                "metric": "pfof",
                "aggregation": "SUM",
                "dimensions": ["month"],
                "entities": {"executing_bd": "Citadel"},
                "period": {"year": 2024},
                "filters": {"data_type": "venue"},
                "limit": 1,
                "order_desc": False
            }
        },
        {
            "query": "Top venue per broker by PFOF in 2024",
            "intent": {
                "table": "executing_bd_606",
                "operation": "top_per_group",
                "metric": "pfof",
                "aggregation": "SUM",
                "dimensions": ["executing_bd", "venues"],
                "period": {"year": 2024},
                "filters": {"data_type": "venue"},
                "limit": 1,
                "order_desc": True
            }
        },
        {
            "query": "How many venues did Robinhood use in 2024",
            "intent": {
                "table": "executing_bd_606",
                "operation": "count",
                "count_dimension": "venue",
                "entities": {"executing_broker": "Robinhood"},
                "period": {"year": 2024},
                "filters": {"data_type": "venue"}
            }
        },
        {
            "query": "Average PFOF per venue for Robinhood in 2024",
            "intent": {
                "table": "executing_bd_606",
                "operation": "per_entity_average",
                "metric": "pfof",
                "aggregation": "SUM",
                "per_entity": "venue",
                "entities": {"executing_broker": "Robinhood"},
                "period": {"year": 2024},
                "filters": {"data_type": "venue"}
            }
        }
    ]

    return "\n\n".join([
        f"Query: {ex['query']}\nIntent: {json.dumps(ex['intent'], indent=2)}"
        for ex in examples
    ])


SYSTEM_PROMPT = """You are an expert at extracting structured intent from natural language database queries about SEC Rule 606 financial data.

Your task is to analyze the user's question and return a JSON object representing the query intent. This intent will be used to generate deterministic SQL using templates.

# Available Tables and Schema
{schema_context}

# Operation Types
- **list**: Return distinct values (e.g., "list all brokers", "show venues")
- **aggregate**: Sum/count/avg across rows, optionally grouped by dimensions (e.g., "total PFOF by broker")
- **topN**: Top N results ordered by metric (e.g., "top 5 brokers by PFOF")
- **top_per_group**: Top N within each group (e.g., "top venue per broker", "top participant per quarter")
- **count**: Count distinct entities (e.g., "how many venues did X use") - use count_dimension field
- **per_entity_average**: Average metric per entity (e.g., "average PFOF per venue") - use per_entity field
- **earliest**: Earliest record by time (e.g., "first month with data")
- **latest**: Latest record by time (e.g., "most recent quarter")
- **cross_table_list**: List entities across all tables
- **string_length**: Longest/shortest name

# Metric Types
- **pfof**: Payment for order flow (executing_bd_606 only)
- **volume**: Total shares/notional (monthly_data, finra_ats) or estimated volume from cents-per-hundred (executing_bd_606)
- **trades**: Trade count (monthly_data, finra_ats)
- **pfof_and_volume**: Both PFOF and estimated volume (executing_bd_606 only)
- **tape_a**: NYSE-listed stocks volume (synonyms: NYSE, NYSE stocks, NYSE listed)
- **tape_b**: NASDAQ-listed stocks volume (synonyms: NASDAQ, Nasdaq stocks, NASDAQ listed)
- **tape_c**: Other listings including ETFs (synonyms: ETF, ETFs, ETF listings)
- **tape**: All tapes combined (monthly_data)

# Entity Recognition and Preposition Rules
**CRITICAL: Use prepositions to determine entity type:**
- "PFOF **from** [entity]" → venue (wholesaler paying PFOF)
  Example: "PFOF from Citadel" → entities.venue = "Citadel"
- "PFOF **for** [entity]" → executing_bd (broker receiving PFOF)
  Example: "PFOF for Robinhood" → entities.executing_bd = "Robinhood"

**Entity Type Mappings:**
- **Brokers (executing_bd)**: Robinhood, Charles Schwab, TD Ameritrade, Webull, E*TRADE
- **Venues/Wholesalers (venue)**: Citadel, Virtu, Wolverine, Two Sigma, Jane Street, Goldman Sachs, Morgan Stanley
- **Market participants**: Exchange names on monthly_data (e.g., "NYSE", "NASDAQ")
- **ATS names**: Alternative trading systems on finra_ats (e.g., "SIGMA X2", "UBS ATS")

# Filters
- **data_type**: Always "venue" for PFOF queries on executing_bd_606
- **stock_group**: Price group filter (executing_bd_606). Synonyms: category, stock type, security type. Values like "SP500" can be written as "S&P 500", "S&P", etc.
- **tier**: ATS tier filter (finra_ats)

# Interrogative Patterns
- "Who paid..." → aggregate with venues dimension
- "What brokers..." → list or aggregate with executing_bd dimension
- "Which month..." → topN with month dimension

# Examples
{examples}

# Response Format
Return ONLY a valid JSON object with these fields (omit null/empty fields):
{{
  "table": "table_name",
  "operation": "aggregate|topN|list|top_per_group|count|per_entity_average|earliest|latest",
  "metric": "pfof|volume|trades|...",
  "aggregation": "SUM|COUNT|AVG|MIN|MAX",
  "dimensions": ["dimension1", "dimension2"],
  "entities": {{"entity_type": "entity_name"}},
  "period": {{"year": 2024, "month": 6, "quarter": 2}},
  "filters": {{"filter_key": "filter_value"}},
  "limit": 5,
  "order_desc": true,
  "count_dimension": "venue|executing_broker|market_participant|ATS",
  "per_entity": "venue|executing_broker|market_participant|ATS"
}}

Rules:
1. Infer table from context (brokers/venues → executing_bd_606, market participants → monthly_data, ATS → finra_ats)
2. For PFOF queries, always include filters.data_type = "venue"
3. For "who paid" queries, use aggregate operation with venues dimension
4. For "top X per Y" queries, use top_per_group with dimensions [Y, X]
5. For temporal grouping ("for each quarter"), include temporal dimension first
6. For superlatives with temporal ("which month had lowest"), use topN with order_desc=false for "lowest"
7. For "how many X" queries, use count operation with count_dimension
8. For "average X per Y" queries, use per_entity_average operation with per_entity
9. Entity types: use "venue", "executing_broker", "market_participant", or "ATS" (generic names that map to table columns)
"""


def extract_intent_with_llm(user_input: str, model: str = "gpt-4o-mini") -> Optional[QueryIntent]:
    """
    Use LLM to extract structured intent from natural language query.

    Args:
        user_input: Natural language query
        model: OpenAI model to use (default: gpt-4o-mini for speed/cost)

    Returns:
        QueryIntent object or None if extraction fails
    """
    try:
        schema_context = _build_schema_context()
        examples = _build_examples()

        system_prompt = SYSTEM_PROMPT.format(
            schema_context=schema_context,
            examples=examples
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=500
        )

        intent_json = json.loads(response.choices[0].message.content)

        # Convert JSON to QueryIntent object
        return _json_to_query_intent(intent_json)

    except Exception as e:
        print(f"LLM intent extraction failed: {e}")
        return None


def _json_to_query_intent(intent_json: Dict) -> QueryIntent:
    """Convert LLM JSON response to QueryIntent object."""
    # Extract table (store separately, not in QueryIntent)
    table = intent_json.pop("table", None)

    # Build QueryIntent from remaining fields
    intent = QueryIntent(
        operation=intent_json.get("operation"),
        metric=intent_json.get("metric"),
        aggregation=intent_json.get("aggregation"),
        dimensions=intent_json.get("dimensions", []),
        entities=intent_json.get("entities", {}),
        period=intent_json.get("period", {}),
        filters=intent_json.get("filters", {}),
        limit=intent_json.get("limit"),
        order_desc=intent_json.get("order_desc", True),
        top_n=intent_json.get("top_n"),
        count_dimension=intent_json.get("count_dimension"),
        per_entity=intent_json.get("per_entity")
    )

    # Store table as a tag for planner to use
    intent.topic = table  # Reuse topic field to store table name

    return intent


if __name__ == "__main__":
    # Test queries
    test_queries = [
        "Who paid Robinhood PFOF in June 2024",
        "Top 5 brokers by PFOF in 2024",
        "For each quarter, top market participant by total shares in 2024",
        "What brokers traded in Q2 2024",
        "Compare PFOF and estimated volume by broker in 2024"
    ]

    print("Testing LLM Intent Extractor\n" + "="*50)
    for query in test_queries:
        print(f"\nQuery: {query}")
        intent = extract_intent_with_llm(query)
        if intent:
            print(f"Table: {intent.topic}")
            print(f"Operation: {intent.operation}")
            print(f"Metric: {intent.metric}")
            print(f"Dimensions: {intent.dimensions}")
            print(f"Entities: {intent.entities}")
            print(f"Period: {intent.period}")
            print(f"Filters: {intent.filters}")
        else:
            print("Failed to extract intent")
