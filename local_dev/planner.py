from __future__ import annotations

"""
planner.py
Maps QueryIntent + tags to a single-shot SQL using templates.
Default path for most questions; falls back to complex only when multi-part.

Now supports LLM-based intent extraction (controlled by USE_LLM_INTENT env var).
"""

import os
import re
from typing import Dict, Optional, Tuple

from query_intent import QueryIntent
from sql_templates import (
    build_distinct,
    build_aggregate,
    build_top_n,
    build_top_per_group,
    build_earliest_latest,
    build_string_length,
    build_cross_table_entity_list,
    build_count,
    build_per_entity_average,
)
from capability_registry import allowed_metric

# Optional LLM-based intent extraction
try:
    from llm_intent_extractor import extract_intent_with_llm  # type: ignore
    _LLM_EXTRACTOR_OK = True
except Exception:
    _LLM_EXTRACTOR_OK = False

# Optional semantic-hints adapter (helps shape GROUP BY / ORDER BY / LIMIT only)
try:
    from semantic_sql_adapter import (  # type: ignore
        get_sql_hint as _get_sql_hint,
        build_intent_from_user_input as _build_intent,  # unused here but kept for parity
    )
    _ADAPTER_OK = True
except Exception:
    _ADAPTER_OK = False


def _detect_table(tags: Dict) -> str:
    text = (tags.get("_text") or "").lower()
    # ATS questions
    if any(k in text for k in ["ats", "alternative trading system", "dark pool"]):
        return "finra_ats"
    # Market/trades/notional questions
    if any(k in text for k in ["market", "total shares", "notional", "trade count", "market participant", "total trades", " trades ", " trade "]):
        return "monthly_data"
    # Default to 606 for broker/venue/PFOF/rate/volume-estimation
    return "executing_bd_606"


def _detect_operation_and_dims(tags: Dict) -> Tuple[str, list]:
    text = (tags.get("_text") or "").lower()
    dims = []
    # Special: cross-table entity listing (e.g., "list all entities across the system")
    if re.search(r'\b(entities|names|participants)\b.*\b(across|system|all tables)\b', text) or \
       re.search(r'\b(across|system)\b.*\b(entities|names|participants)\b', text):
        return "cross_table_list", dims
    # Special: string length queries like "longest name" or "shortest name"
    if re.search(r'\b(longest|shortest)\b.*\bname\b', text):
        return "string_length", dims
    # Interrogative queries: "who", "what", "which" often ask for lists/breakdowns
    # "who paid..." = list of payers (venues)
    # "what brokers/venues..." = list of entities
    if text.startswith("who ") or text.startswith("what ") or text.startswith("which "):
        # Exclude "which [time]" with superlatives (those are topN)
        if not (("which month" in text or "what month" in text or "which quarter" in text or "what quarter" in text or "which year" in text or "what year" in text) and
                any(w in text for w in ["lowest", "highest", "most", "largest", "smallest", "biggest"])):
            # This is likely asking for a list/breakdown by dimension
            return "aggregate", dims  # Will infer dimension later
    # list/distinct
    if any(w in text for w in ["list", "show", "display"]) and any(w in text for w in ["unique", "distinct", "all"]):
        return "list", dims
    # explicit grouping hints: 'each', 'per', 'by <entity>'
    if any(w in text for w in ["each", "per"]) or any(text.count(f"by {w}") for w in ["broker", "venue", "participant"]):
        # Do not force an operation here; let dims be added and use aggregate
        # Dims will be inferred below in plan_single_sql
        return "aggregate", dims
    # "which month/quarter/year" with superlative (lowest/highest)
    if ("which month" in text or "what month" in text) and any(w in text for w in ["lowest", "highest", "most", "largest", "smallest", "biggest"]):
        return "topN", ["month"]
    if ("which quarter" in text or "what quarter" in text) and any(w in text for w in ["lowest", "highest", "most", "largest", "smallest", "biggest"]):
        return "topN", ["quarter"]
    # top N / superlatives
    if any(w in text for w in ["top", "highest", "most", "largest", "biggest"]):
        return "topN", dims
    if any(w in text for w in ["lowest", "smallest", "minimum", "least"]):
        return "topN", dims
    # earliest/latest
    if any(w in text for w in ["earliest", "first"]):
        return "earliest", dims
    if any(w in text for w in ["latest", "newest", "most recent"]):
        return "latest", dims
    # top-per-group patterns: "top X per Y", "for each Y", etc.
    if any(phrase in text for phrase in ["for each stock group", "per stock group", "by stock group"]):
        dims = ["stock_group", "executing_bd"]
        return "top_per_group", dims
    # "for each quarter/month/year, top..." or "top ... per quarter/month/year"
    if re.search(r'\bfor each (quarter|month|year)\b', text) and any(w in text for w in ["top", "highest", "most", "largest", "biggest"]):
        # Extract the partition dimension (quarter/month/year)
        match = re.search(r'\bfor each (quarter|month|year)\b', text)
        if match:
            dims = [match.group(1)]
            return "top_per_group", dims
    if re.search(r'\btop\b.*\bper (quarter|month|year)\b', text):
        match = re.search(r'\bper (quarter|month|year)\b', text)
        if match:
            dims = [match.group(1)]
            return "top_per_group", dims
    # "top venue per broker" or "for each broker, top venue"
    if re.search(r'\btop\b.*\bper (broker|brokers?|executing.?bd)\b', text) or re.search(r'\bfor each (broker|brokers?|executing.?bd)\b.*\btop\b', text):
        dims = ["executing_bd"]
        return "top_per_group", dims
    if re.search(r'\btop\b.*\bper (venue|venues)\b', text) or re.search(r'\bfor each (venue|venues)\b.*\btop\b', text):
        dims = ["venues"]
        return "top_per_group", dims
    # fall back to aggregate
    if any(w in text for w in ["sum", "total", "aggregate", "across"]):
        return "aggregate", dims
    # default aggregate (most safe)
    return "aggregate", dims


def _infer_dimension_from_text(table: str, tags: Dict) -> Optional[str]:
    text = (tags.get("_text") or "").lower()

    # Check for temporal dimensions first (most specific)
    if re.search(r'\bquarters?\b', text):
        return "quarter"
    if re.search(r'\bmonths?\b', text):
        return "month"
    if re.search(r'\byears?\b', text):
        return "year"

    # Interrogative patterns that indicate dimension
    # "who paid [broker]" or "who received" in PFOF context = venues dimension
    if text.startswith("who "):
        if any(w in text for w in ["paid", "pay", "payment", "pfof", "received", "receive"]):
            # If broker mentioned, user wants to know which venues
            # If venue mentioned, user wants to know which brokers
            if any(w in text for w in ["broker", "brokers", "executing"]):
                return "venues" if table == "executing_bd_606" else None
            elif any(w in text for w in ["venue", "venues", "exchange"]):
                return "executing_bd" if table == "executing_bd_606" else None
            # Default: if PFOF context, probably asking about venues
            if table == "executing_bd_606":
                return "venues"

    # "what brokers/venues..." = list those entities
    if text.startswith("what "):
        if any(w in text for w in ["broker", "brokers", "executing"]):
            return "executing_bd" if table == "executing_bd_606" else None
        if any(w in text for w in ["venue", "venues", "exchange"]):
            return "venues" if table == "executing_bd_606" else None

    # Entity dimensions
    if "executing broker" in text or "executing brokers" in text or "brokers" in text or "broker" in text:
        return "executing_bd" if table == "executing_bd_606" else None
    if "venues" in text or "venue" in text:
        return "venues" if table == "executing_bd_606" else None
    if "market participant" in text and table == "monthly_data":
        return "market_participant"
    if "ats" in text and table == "finra_ats":
        return "ats_name"
    return None


def _build_sql_from_intent(intent: QueryIntent, table: str, user_input: str) -> Optional[str]:
    """
    Build SQL from a QueryIntent using templates.
    This is the core SQL generation logic, used by both LLM and manual paths.
    """
    op = intent.operation

    # Cross-table entity listing
    if op == "cross_table_list":
        text_lower = user_input.lower()
        limit_match = re.search(r'\b(first|top)\s+(\d+)\b', text_lower)
        limit = int(limit_match.group(2)) if limit_match else 30
        return build_cross_table_entity_list(intent, limit)

    # String Length (longest/shortest name)
    if op == "string_length":
        text_lower = user_input.lower()
        column = None
        if "broker" in text_lower or "executing" in text_lower:
            column = "executing_bd" if table == "executing_bd_606" else None
        elif "venue" in text_lower:
            column = "venues" if table == "executing_bd_606" else None
        elif "ats" in text_lower and table == "finra_ats":
            column = "ats_name"
        elif "market participant" in text_lower and table == "monthly_data":
            column = "market_participant"

        if not column:
            if table == "executing_bd_606":
                column = "executing_bd"
            elif table == "monthly_data":
                column = "market_participant"
            elif table == "finra_ats":
                column = "ats_name"

        if column:
            is_longest = "longest" in text_lower
            return build_string_length(intent, table, column, is_longest)

    # Simple "list distinct" handling
    if op == "list":
        if intent.dimensions and len(intent.dimensions) > 0:
            return build_distinct(intent, table, intent.dimensions[0])
        return None

    # Count operation
    if op == "count":
        if intent.count_dimension:
            return build_count(intent, table, intent.count_dimension)
        return None

    # Per-entity average
    if op == "per_entity_average":
        if intent.per_entity:
            return build_per_entity_average(intent, table, intent.per_entity)
        return None

    # Earliest/Latest
    if op in ("earliest", "latest"):
        return build_earliest_latest(intent, table, earliest=(op == "earliest"))

    # Top N
    if op == "topN":
        if not intent.limit and not intent.top_n:
            intent.top_n = 1
        return build_top_n(intent, table)

    # Top per group
    if op == "top_per_group":
        partition_dim = intent.dimensions[0] if intent.dimensions else "stock_group"
        return build_top_per_group(intent, table, partition_dim)

    # Aggregate default (with or without dims)
    if op == "aggregate":
        if not allowed_metric(table, intent.metric):
            return None
        return build_aggregate(intent, table)

    return None


def plan_single_sql(user_input: str, tags: Dict) -> Optional[str]:
    """
    Build a single-shot SQL if possible; returns None if indeterminate.

    NEW: Tries LLM-based intent extraction first (if USE_LLM_INTENT=true),
    then falls back to manual pattern detection.
    """
    # Try LLM-based intent extraction first (if enabled)
    use_llm = os.getenv("USE_LLM_INTENT", "false").lower() == "true"
    if use_llm and _LLM_EXTRACTOR_OK:
        try:
            llm_intent = extract_intent_with_llm(user_input)
            if llm_intent:
                # LLM stores table name in topic field
                table = llm_intent.topic or "executing_bd_606"
                print(f"[LLM Intent] Table: {table}, Op: {llm_intent.operation}, Metric: {llm_intent.metric}, Dims: {llm_intent.dimensions}")

                sql = _build_sql_from_intent(llm_intent, table, user_input)
                if sql:
                    print(f"[LLM Success] Generated SQL using LLM intent")
                    return sql
                else:
                    print(f"[LLM Fallback] Intent extracted but SQL generation failed, trying manual detection")
        except Exception as e:
            print(f"[LLM Error] {e}, falling back to manual detection")

    # Manual pattern detection (original logic)
    tags = dict(tags or {})
    tags["_text"] = user_input
    intent = QueryIntent.from_tags(tags)
    table = _detect_table(tags)

    # Detect multi-metric queries (e.g., "compare PFOF and volume")
    text_lower = user_input.lower()
    is_multi_metric = False
    if ("pfof" in text_lower and ("volume" in text_lower or "estimated" in text_lower)) or \
       ("compare" in text_lower and "and" in text_lower):
        # Check if this is a comparison query with multiple metrics from same table
        if table == "executing_bd_606":
            is_multi_metric = True

    # Metric defaults
    if not intent.metric:
        # Check for specific metric mentions
        if is_multi_metric and table == "executing_bd_606":
            # Multi-metric query: PFOF and volume
            intent.metric = "pfof_and_volume"
            intent.aggregation = "SUM"
        elif "tape a" in text_lower:
            intent.metric = "tape_a"
            intent.aggregation = "SUM"
        elif "tape b" in text_lower:
            intent.metric = "tape_b"
            intent.aggregation = "SUM"
        elif "tape c" in text_lower:
            intent.metric = "tape_c"
            intent.aggregation = "SUM"
        elif tags.get("mentions_tape") and table == "monthly_data":
            intent.metric = "tape"  # All tapes
            intent.aggregation = "SUM"
        elif "trades" in text_lower or "trade count" in text_lower:
            intent.metric = "trades"
            intent.aggregation = "SUM"
        elif tags.get("mentions_volume"):
            intent.metric = "volume"
            intent.aggregation = "SUM"
        elif table == "executing_bd_606":
            # Default to PFOF for broker/venue questions if no metric mentioned
            intent.metric = "pfof"
            intent.aggregation = "SUM"
        elif table == "monthly_data":
            intent.metric = "volume"
            intent.aggregation = "SUM"
        elif table == "finra_ats":
            intent.metric = "volume"
            intent.aggregation = "SUM"

    # Operation & dimensions
    op, auto_dims = _detect_operation_and_dims(tags)
    intent.operation = op
    # Honor explicit dims if present; else derive
    if not intent.dimensions and auto_dims:
        intent.dimensions = auto_dims
    # If still no dims and phrasing implies per-entity breakdown, infer one
    if not intent.dimensions:
        inferred = _infer_dimension_from_text(table, tags)
        if inferred and op != "list":
            intent.dimensions = [inferred]

    # Optional semantic-hints: refine dimensions/order/limit from adapter hint SQL (no table/column invention)
    try:
        use_hints = os.getenv("USE_SEMANTIC_HINTS", "false").lower() == "true"
        if _ADAPTER_OK and use_hints:
            hint_sql = _get_sql_hint(user_input, intent)
            if hint_sql:
                sql_lower = hint_sql.lower()
                # GROUP BY
                if "group by" in sql_lower and not intent.dimensions:
                    # crude parse: take first identifier after group by
                    try:
                        group_part = sql_lower.split("group by", 1)[1].strip().split()[0].strip(",;")
                        if group_part in ("executing_bd", "venues", "market_participant", "stock_group"):
                            intent.dimensions = [group_part]
                    except Exception:
                        pass
                # ORDER BY
                if "order by" in sql_lower and not intent.order_by:
                    try:
                        order_part = sql_lower.split("order by", 1)[1].strip().split()[0].strip(",;")
                        intent.order_by = order_part
                        intent.order_desc = "desc" in sql_lower.split("order by", 1)[1][:20]
                    except Exception:
                        pass
                # LIMIT
                if "limit" in sql_lower and not intent.limit:
                    try:
                        lim = int(sql_lower.split("limit", 1)[1].strip().split()[0].strip(";"))
                        intent.limit = lim
                    except Exception:
                        pass
    except Exception:
        # Never fail the planner on hints
        pass

    # Simple “list distinct” handling
    if op == "list":
        dim = _infer_dimension_from_text(table, tags)
        if dim:
            return build_distinct(intent, table, dim)
        # If no dimension inferred, try common fields
        for candidate in (["executing_bd", "venues"] if table == "executing_bd_606" else ["market_participant"]):
            try:
                return build_distinct(intent, table, candidate)
            except Exception:
                continue
        return None

    # Cross-table entity listing
    if op == "cross_table_list":
        text_lower = user_input.lower()
        # Extract limit if specified (e.g., "first 10", "top 20")
        limit_match = re.search(r'\b(first|top)\s+(\d+)\b', text_lower)
        limit = int(limit_match.group(2)) if limit_match else 30
        return build_cross_table_entity_list(intent, limit)

    # String Length (longest/shortest name)
    if op == "string_length":
        text_lower = user_input.lower()
        # Determine which column to measure
        column = None
        if "broker" in text_lower or "executing" in text_lower:
            column = "executing_bd" if table == "executing_bd_606" else None
        elif "venue" in text_lower:
            column = "venues" if table == "executing_bd_606" else None
        elif "ats" in text_lower and table == "finra_ats":
            column = "ats_name"
        elif "market participant" in text_lower and table == "monthly_data":
            column = "market_participant"

        if not column:
            # Try to infer from table
            if table == "executing_bd_606":
                column = "executing_bd"
            elif table == "monthly_data":
                column = "market_participant"
            elif table == "finra_ats":
                column = "ats_name"

        if column:
            is_longest = "longest" in text_lower
            return build_string_length(intent, table, column, is_longest)

    # Earliest/Latest
    if op in ("earliest", "latest"):
        return build_earliest_latest(intent, table, earliest=(op == "earliest"))

    # Top N
    if op == "topN":
        # If user said "top 3", try to infer n
        import re
        m = re.search(r"top\s+(\d+)", user_input.lower())
        if m:
            intent.top_n = int(m.group(1))
        intent.top_n = intent.top_n or 1  # Default to 1 for "which month" queries

        # Check if this is a "lowest/minimum" query (reverse sort)
        text_lower = user_input.lower()
        if any(w in text_lower for w in ["lowest", "smallest", "minimum", "least"]):
            intent.order_desc = False

        return build_top_n(intent, table)

    # Top per group
    if op == "top_per_group":
        # Extract partition dimension from intent.dimensions (first dimension is the partition key)
        if intent.dimensions and len(intent.dimensions) > 0:
            partition_dim = intent.dimensions[0]
        else:
            # Fallback to stock_group for legacy queries
            partition_dim = "stock_group"

        # Infer the entity dimension being ranked (e.g., "market participant" in "top participant per quarter")
        text_lower = user_input.lower()
        if not intent.dimensions or len(intent.dimensions) < 2:
            # Try to infer what entity is being ranked
            if "market participant" in text_lower and table == "monthly_data":
                if not intent.dimensions:
                    intent.dimensions = [partition_dim, "market_participant"]
                elif len(intent.dimensions) == 1:
                    intent.dimensions.append("market_participant")
            elif ("broker" in text_lower or "executing" in text_lower) and table == "executing_bd_606":
                if not intent.dimensions:
                    intent.dimensions = [partition_dim, "executing_bd"]
                elif len(intent.dimensions) == 1:
                    intent.dimensions.append("executing_bd")
            elif "venue" in text_lower and table == "executing_bd_606":
                if not intent.dimensions:
                    intent.dimensions = [partition_dim, "venues"]
                elif len(intent.dimensions) == 1:
                    intent.dimensions.append("venues")
            elif "ats" in text_lower and table == "finra_ats":
                if not intent.dimensions:
                    intent.dimensions = [partition_dim, "ats_name"]
                elif len(intent.dimensions) == 1:
                    intent.dimensions.append("ats_name")

        return build_top_per_group(intent, table, partition_dim)

    # Aggregate default (with or without dims)
    if not allowed_metric(table, intent.metric):
        return None
    return build_aggregate(intent, table)


