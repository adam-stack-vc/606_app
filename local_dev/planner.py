from __future__ import annotations

"""
planner.py
Maps QueryIntent + tags to a single-shot SQL using templates.
Default path for most questions; falls back to complex only when multi-part.
"""

from typing import Dict, Optional, Tuple

from query_intent import QueryIntent
from sql_templates import (
    build_distinct,
    build_aggregate,
    build_top_n,
    build_top_per_group,
    build_earliest_latest,
)
from capability_registry import allowed_metric

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
    if any(k in text for k in ["market", "total shares", "notional", "trade count", "market participant"]):
        return "monthly_data"
    # Default to 606 for broker/venue/PFOF/rate/volume-estimation
    return "executing_bd_606"


def _detect_operation_and_dims(tags: Dict) -> Tuple[str, list]:
    text = (tags.get("_text") or "").lower()
    dims = []
    # list/distinct
    if any(w in text for w in ["list", "show", "display"]) and any(w in text for w in ["unique", "distinct", "all"]):
        return "list", dims
    # explicit grouping hints: 'each', 'per', 'by <entity>'
    if any(w in text for w in ["each", "per"]) or any(text.count(f"by {w}") for w in ["broker", "venue", "participant"]):
        # Do not force an operation here; let dims be added and use aggregate
        # Dims will be inferred below in plan_single_sql
        return "aggregate", dims
    # top N
    if any(w in text for w in ["top", "highest", "most", "largest"]):
        return "topN", dims
    # earliest/latest
    if any(w in text for w in ["earliest", "first"]):
        return "earliest", dims
    if any(w in text for w in ["latest", "newest", "most recent"]):
        return "latest", dims
    # top-per-group
    if any(phrase in text for phrase in ["for each stock group", "per stock group", "by stock group"]):
        dims = ["stock_group", "executing_bd"]
        return "top_per_group", dims
    # fall back to aggregate
    if any(w in text for w in ["sum", "total", "aggregate", "across"]):
        return "aggregate", dims
    # default aggregate (most safe)
    return "aggregate", dims


def _infer_dimension_from_text(table: str, tags: Dict) -> Optional[str]:
    text = (tags.get("_text") or "").lower()
    if "executing broker" in text or "executing brokers" in text or "brokers" in text:
        return "executing_bd" if table == "executing_bd_606" else None
    if "venues" in text or "venue" in text:
        return "venues" if table == "executing_bd_606" else None
    if "market participant" in text and table == "monthly_data":
        return "market_participant"
    return None


def plan_single_sql(user_input: str, tags: Dict) -> Optional[str]:
    """
    Build a single-shot SQL if possible; returns None if indeterminate.
    """
    tags = dict(tags or {})
    tags["_text"] = user_input
    intent = QueryIntent.from_tags(tags)
    table = _detect_table(tags)

    # Metric defaults
    if not intent.metric:
        if table == "executing_bd_606":
            # Prefer PFOF for broker/venue questions
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
        import os
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

    # Earliest/Latest
    if op in ("earliest", "latest"):
        return build_earliest_latest(intent, table, earliest=(op == "earliest"))

    # Top N
    if op == "topN":
        # If user said "top 3", try to infer n
        import re
        m = re.search(r"top\\s+(\\d+)", user_input.lower())
        if m:
            intent.top_n = int(m.group(1))
        intent.top_n = intent.top_n or 10
        return build_top_n(intent, table)

    # Top per group
    if op == "top_per_group":
        partition_dim = "stock_group"
        return build_top_per_group(intent, table, partition_dim)

    # Aggregate default (with or without dims)
    if not allowed_metric(table, intent.metric):
        return None
    return build_aggregate(intent, table)


