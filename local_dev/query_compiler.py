from typing import Dict, List, Optional, Any
import json
import os
from query_models import StructuredIntent, Period, Filters
from value_normalizer import normalize_value

# -----------------------------------------------------------------------------
# Entity Mapping Helpers
# -----------------------------------------------------------------------------

_ENTITY_MAPPINGS = None

def _load_entity_mappings():
    """Load entity mappings from entity_mappings.json"""
    global _ENTITY_MAPPINGS
    if _ENTITY_MAPPINGS is None:
        # Assuming json is in the same dir
        config_path = os.path.join(os.path.dirname(__file__), "entity_mappings.json")
        try:
            with open(config_path, "r") as f:
                _ENTITY_MAPPINGS = json.load(f)
        except FileNotFoundError:
            _ENTITY_MAPPINGS = {}
    return _ENTITY_MAPPINGS

def _map_entity_to_column(entity_type: str, table: str) -> Optional[str]:
    entity_map = _load_entity_mappings()
    return entity_map.get(table, {}).get(entity_type.lower())

# -----------------------------------------------------------------------------
# Table Detection
# -----------------------------------------------------------------------------

def _get_table_for_intent(intent: StructuredIntent) -> str:
    # Ported from planner.py _detect_table logic + heuristic refinements
    
    # ATS questions
    if "ats_name" in intent.dimensions or (intent.filters and intent.filters.ats_name):
        return "finra_ats"
    if intent.metric == "volume" and "ats_name" in intent.dimensions:
        return "finra_ats"
    
    # Market/trades/notional questions (monthly_data)
    # Check dimensions or metric hint
    if "market_participant" in intent.dimensions or (intent.filters and intent.filters.market_participant):
        return "monthly_data"
    if intent.metric in ["trades", "tape_a", "tape_b", "tape_c", "tape"]:
        return "monthly_data"
    if intent.metric == "volume" and not ("executing_bd" in intent.dimensions or "venues" in intent.dimensions or intent.filters.executing_bd or intent.filters.venues):
        # Volume without broker context usually means market volume
        return "monthly_data"

    # Default to 606 for broker/venue/PFOF/rate/volume-estimation
    return "executing_bd_606"

# -----------------------------------------------------------------------------
# SQL Generation Helpers
# -----------------------------------------------------------------------------

def _safe_ident(name: str) -> str:
    return name.replace('"', "").replace(";", "")

def _time_filters(table: str, intent: StructuredIntent) -> List[str]:
    # Simplified capabilities logic
    # executing_bd_606, finra_ats have explicit year/month/quarter columns
    # monthly_data uses 'day'
    
    wheres = []
    y = intent.period.year
    m = intent.period.month
    q = intent.period.quarter
    
    if table == "monthly_data":
        if y is not None:
            wheres.append(f"EXTRACT(YEAR FROM day) = {int(y)}")
        if m is not None:
            wheres.append(f"EXTRACT(MONTH FROM day) = {int(m)}")
        if q is not None:
            wheres.append(f"EXTRACT(QUARTER FROM day) = {int(q)}")
    else:
        # Tables with explicit columns (executing_bd_606, finra_ats)
        if y is not None:
            wheres.append(f"year = {int(y)}")
        if m is not None:
            # Month is often string/varchar in these tables
            wheres.append(f"month = '{int(m)}'")
        
        if q is not None:
            # Check if table supports quarter directly? 
            # finra_ats does. executing_bd_606 generally doesn't have quarter col, but logic in sql_templates maps it.
            if table == "finra_ats":
                 wheres.append(f"quarter = '{int(q)}'")
            elif table == "executing_bd_606":
                # Map quarter to months
                quarter_months = {
                    1: [1, 2, 3],
                    2: [4, 5, 6],
                    3: [7, 8, 9],
                    4: [10, 11, 12]
                }
                if q in quarter_months:
                    months = quarter_months[q]
                    month_list = ','.join(f"'{mon}'" for mon in months)
                    wheres.append(f"month IN ({month_list})")

    return wheres

def _build_filters(intent: StructuredIntent, table: str) -> List[str]:
    """
    Build comprehensive WHERE clauses including time and normalized entity filters.
    Used by all builder functions to ensure consistency.
    """
    wheres = _time_filters(table, intent)
    
    # Pydantic Filters object
    if intent.filters.executing_bd:
        safe_val = normalize_value("executing_bd", intent.filters.executing_bd).replace("'", "''")
        wheres.append(f"executing_bd = '{safe_val}'")
    if intent.filters.venues:
        safe_val = normalize_value("venues", intent.filters.venues).replace("'", "''")
        wheres.append(f"venues = '{safe_val}'")
    if intent.filters.stock_group:
        safe_val = normalize_value("stock_group", intent.filters.stock_group).replace("'", "''")
        wheres.append(f"stock_group = '{safe_val}'")
    if intent.filters.ats_name:
        safe_val = normalize_value("ats_name", intent.filters.ats_name).replace("'", "''")
        wheres.append(f"ats_name = '{safe_val}'")
    if intent.filters.market_participant:
        safe_val = normalize_value("market_participant", intent.filters.market_participant).replace("'", "''")
        wheres.append(f"market_participant = '{safe_val}'")
    if intent.filters.data_type:
        wheres.append(f"data_type = '{intent.filters.data_type}'")
    
    # Handle dynamic extra entities from intent.entities dict (legacy compatibility)
    for k, v in intent.entities.items():
        col = _map_entity_to_column(k, table) or k
        if col == "venue": col = "venues"
        if col == "broker": col = "executing_bd"
        if v:
            safe_val = normalize_value(col, str(v)).replace("'", "''")
            # Avoid duplicate filters
            if f"{col} = '{safe_val}'" not in wheres:
                wheres.append(f"{col} = '{safe_val}'")

    # Specific logic for PFOF
    if table == "executing_bd_606" and intent.metric == "pfof":
        if "data_type = 'venue'" not in wheres:
            wheres.append("data_type = 'venue'")
            
    return wheres

def _pfof_sum_expr() -> str:
    return (
        "COALESCE(netpmtpaidrecvmarketordersusd, 0) + "
        "COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) + "
        "COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) + "
        "COALESCE(netpmtpaidrecvotherordersusd, 0)"
    )

def _metric_select(table: str, intent: StructuredIntent) -> str:
    metric = (intent.metric or "").lower()
    # Handle count distinct special case
    if intent.operation == "aggregate_with_count" and metric:
        col = metric
        if col == "venue": col = "venues"
        elif col == "broker": col = "executing_bd"
        return f"COUNT(DISTINCT {_safe_ident(col)}) AS {metric}_count"

    agg = "SUM" # Default aggregation

    if table == "executing_bd_606":
        pfof_sum = _pfof_sum_expr()
        if metric == "pfof_and_volume":
             # Return both
             return f"SUM({pfof_sum}) AS total_pfof_usd, CASE WHEN AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) + COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) + COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) + COALESCE(netpmtpaidrecvotherorderscph, 0)) > 0 THEN ROUND((SUM({pfof_sum})::numeric / AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) + COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) + COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) + COALESCE(netpmtpaidrecvotherorderscph, 0))) * 100, 2) ELSE 0 END AS estimated_volume"
        if metric == "pfof":
            return f"SUM({pfof_sum}) AS total_pfof_usd"
        if metric == "volume":
            # Estimated volume logic
            return f"CASE WHEN AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) + COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) + COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) + COALESCE(netpmtpaidrecvotherorderscph, 0)) > 0 THEN ROUND((SUM({pfof_sum})::numeric / AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) + COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) + COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) + COALESCE(netpmtpaidrecvotherorderscph, 0))) * 100, 2) ELSE 0 END AS estimated_volume"
        if metric == "rate":
             return "AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) + COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) + COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) + COALESCE(netpmtpaidrecvotherorderscph, 0)) AS avg_cph"
        if metric == "venues":
             return "COUNT(DISTINCT venues) AS venues_count"

    elif table == "monthly_data":
        if metric == "volume":
            return "SUM(total_shares) AS total_shares"
        if metric == "trades":
            return "SUM(total_trades) AS total_trades"
        if "tape" in metric:
            if metric == "tape":
                return "SUM(tape_a_shares) AS tape_a_shares, SUM(tape_b_shares) AS tape_b_shares, SUM(tape_c_shares) AS tape_c_shares"
            col = f"{metric.replace(' ', '_')}_shares"
            return f"SUM({col}) AS {col}"
        if metric == "avg_trade_size":
             return "ROUND(SUM(total_shares)::numeric / NULLIF(SUM(total_trades),0), 2) AS average_trade_size"

    elif table == "finra_ats":
        if metric == "volume":
            return "SUM(total_shares) AS total_shares"
        if metric == "trades":
            return "SUM(total_trades) AS total_trades"

    return "1 AS _noop"

# -----------------------------------------------------------------------------
# Operation Builders
# -----------------------------------------------------------------------------

def build_cross_table_list(intent: StructuredIntent, limit: int = 30) -> str:
    year_filter = ""
    if intent.period.year:
        year_filter = f" WHERE year = {intent.period.year}"
    
    return (
        "WITH all_entities AS (\n"
        "  SELECT DISTINCT executing_bd AS entity_name, 'Broker' AS entity_type\n"
        "  FROM executing_bd_606\n"
        f" {year_filter}\n"
        "  UNION\n"
        "  SELECT DISTINCT venues AS entity_name, 'Venue' AS entity_type\n"
        "  FROM executing_bd_606\n"
        f" {year_filter if year_filter else ''}\n"
        "  UNION\n"
        "  SELECT DISTINCT market_participant AS entity_name, 'Market Participant' AS entity_type\n"
        "  FROM monthly_data\n"
        f" {year_filter.replace('year', 'EXTRACT(YEAR FROM day)') if year_filter else ''}\n"
        "  UNION\n"
        "  SELECT DISTINCT ats_name AS entity_name, 'ATS' AS entity_type\n"
        "  FROM finra_ats\n"
        f" {year_filter if year_filter else ''}\n"
        ")\n"
        "SELECT entity_name, entity_type\n"
        "FROM all_entities\n"
        "WHERE entity_name IS NOT NULL AND entity_name != ''\n"
        "ORDER BY entity_name ASC\n"
        f"LIMIT {limit};"
    )

def build_string_length(intent: StructuredIntent, table: str, column: str) -> str:
    wheres = _build_filters(intent, table)
    where_clause = " AND ".join(wheres) if wheres else "TRUE"
    order_dir = "DESC" if intent.is_longest else "ASC"
    
    return (
        f"SELECT {column}, LENGTH({column}) AS name_length\n"
        f"FROM {table}\n"
        f"WHERE {where_clause} AND {column} IS NOT NULL\n"
        f"ORDER BY LENGTH({column}) {order_dir}\n"
        "LIMIT 1;"
    )

def build_per_entity_average(intent: StructuredIntent, table: str) -> str:
    per_entity = intent.per_entity or "venues" # fallback
    entity_col = "venues" if per_entity == "venues" else per_entity
    if entity_col == "broker": entity_col = "executing_bd"
    
    metric_select = _metric_select(table, intent)
    # Extract expression from metric select (naive split)
    metric_expr = metric_select.split(" AS ")[0]
    metric_alias = f"{intent.metric}_per_{per_entity}"
    
    wheres = _build_filters(intent, table)
    where_clause = " AND ".join(wheres) if wheres else "TRUE"
    
    return (
        f"SELECT\n"
        f"  {metric_select},\n"
        f"  COUNT(DISTINCT {entity_col}) AS {per_entity}_count,\n"
        f"  ({metric_expr}) / NULLIF(COUNT(DISTINCT {entity_col}), 0) AS {metric_alias}\n"
        f"FROM {table}\n"
        f"WHERE {where_clause};"
    )

def build_count(intent: StructuredIntent, table: str) -> str:
    count_dim = intent.count_dimension
    col = _map_entity_to_column(count_dim, table) or count_dim
    if col == "broker": col = "executing_bd"
    if col == "venue": col = "venues"
    
    wheres = _build_filters(intent, table)
    where_clause = " AND ".join(wheres) if wheres else "TRUE"
    
    return f"SELECT COUNT(DISTINCT {col}) AS {count_dim}_count FROM {table} WHERE {where_clause};"

def build_top_per_group(intent: StructuredIntent, table: str) -> str:
    # partition dim is first dimension
    partition_dim = intent.dimensions[0]
    
    # Handle temporal partition logic
    partition_expr = partition_dim
    if table == "monthly_data":
        if partition_dim == "month": partition_expr = "EXTRACT(MONTH FROM day)"
        elif partition_dim == "quarter": partition_expr = "EXTRACT(QUARTER FROM day)"
        elif partition_dim == "year": partition_expr = "EXTRACT(YEAR FROM day)"
        
    # Determine order by metric
    order_col = "total_pfof_usd"
    if intent.metric == "volume": order_col = "total_shares"
    
    metric_select = _metric_select(table, intent)
    
    # Recursively build base query
    selects = [partition_expr + f" AS {partition_dim}"]
    groups = [partition_expr]
    
    # Add other dims (the entity being ranked)
    for dim in intent.dimensions[1:]:
        selects.append(dim)
        groups.append(dim)
        
    selects.append(metric_select)
    
    wheres = _build_filters(intent, table)
        
    where_clause = " AND ".join(wheres) if wheres else "TRUE"
    group_clause = f"GROUP BY {', '.join(groups)}"
    
    inner_sql = f"SELECT {', '.join(selects)} FROM {table} WHERE {where_clause} {group_clause}"
    
    # Extract alias from metric_select for ordering
    if " AS " in metric_select:
        metric_alias = metric_select.split(" AS ")[1]
    else:
        metric_alias = "value"
        
    return (
        f"WITH base AS ({inner_sql}),\n"
        f"ranked AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY {partition_dim} ORDER BY {metric_alias} DESC NULLS LAST) as rn FROM base)\n"
        f"SELECT * FROM ranked WHERE rn = 1 ORDER BY {partition_dim};"
    )

# -----------------------------------------------------------------------------
# Main Compiler
# -----------------------------------------------------------------------------

def compile_sql(intent: StructuredIntent) -> str:
    table = _get_table_for_intent(intent)
    
    # Dispatch to specialized builders
    if intent.operation == "cross_table_list":
        return build_cross_table_list(intent)
    
    if intent.operation == "string_length":
        # infer column from first dimension or heuristic
        col = intent.dimensions[0] if intent.dimensions else "executing_bd"
        return build_string_length(intent, table, col)
        
    if intent.operation == "per_entity_average":
        return build_per_entity_average(intent, table)
        
    if intent.operation == "count":
        return build_count(intent, table)
        
    if intent.operation == "top_per_group":
        return build_top_per_group(intent, table)
        
    if intent.operation == "multi":
        return "-- Complex multi-table query synthesis required"

    # Standard Aggregate / List / TopN / Earliest / Latest Logic
    selects = []
    groups = []
    
    # 1. Handle Dimensions & Grouping
    for dim in intent.dimensions:
        col_expr = dim
        # Map standard dims to columns
        if dim == "month":
            if table == "monthly_data": col_expr = "EXTRACT(MONTH FROM day)"
        elif dim == "quarter":
             if table == "monthly_data": col_expr = "EXTRACT(QUARTER FROM day)"
        elif dim == "year":
             if table == "monthly_data": col_expr = "EXTRACT(YEAR FROM day)"
        
        selects.append(f"{col_expr} as {dim}")
        groups.append(col_expr)

    # 2. Handle Filters (using common builder)
    wheres = _build_filters(intent, table)
    
    # Handle Aggregate with Count (SPECIAL CASE)
    metric_sql = _metric_select(table, intent)
    
    # 3. Construct Query Parts
    where_clause = " AND ".join(wheres) if wheres else "TRUE"
    group_clause = f"GROUP BY {', '.join(groups)}" if groups else ""
    
    # Add metric to select if not a pure list op
    full_selects = selects.copy()
    if intent.metric or intent.operation == "aggregate":
        full_selects.append(metric_sql)
    
    select_clause = ", ".join(full_selects)
    
    # 4. Ordering & Limits
    order_clause = ""
    limit_clause = ""
    
    if intent.operation == "topN":
        # Extract alias or expression for ordering
        if " AS " in metric_sql:
            order_col = metric_sql.split(" AS ")[1]
        else:
            order_col = "value"
        
        order_dir = "DESC" if intent.order_desc else "ASC"
        order_clause = f"ORDER BY {order_col} {order_dir}"
        limit_clause = f"LIMIT {intent.top_n}"
        
    elif intent.operation == "earliest" or intent.operation == "latest":
        order_dir = "ASC" if intent.operation == "earliest" else "DESC"
        # Sort by time dimensions
        if table == "monthly_data":
            return f"WITH by_month AS (SELECT EXTRACT(YEAR FROM day) as year, EXTRACT(MONTH FROM day) as month, {metric_sql} FROM {table} WHERE {where_clause} GROUP BY 1, 2) SELECT year, month, total_shares FROM by_month ORDER BY year {order_dir}, month {order_dir} LIMIT 1;"
        elif table == "executing_bd_606":
            return f"WITH by_month AS (SELECT year, month, {metric_sql} FROM {table} WHERE {where_clause} GROUP BY 1, 2) SELECT year, month, total_pfof_usd FROM by_month WHERE total_pfof_usd > 0 ORDER BY year {order_dir}, (NULLIF(month,'')::int) {order_dir} LIMIT 1;"
        
    elif intent.order_by:
        order_clause = f"ORDER BY {intent.order_by} {'DESC' if intent.order_desc else 'ASC'}"
        if intent.top_n:
            limit_clause = f"LIMIT {intent.top_n}"
            
    elif groups:
        order_clause = f"ORDER BY {groups[0]}"

    # Special handling for "List" operation (Distinct)
    if intent.operation == "list":
        return f"SELECT DISTINCT {', '.join(selects)} FROM {table} WHERE {where_clause} ORDER BY {', '.join(groups)} {limit_clause}"

    return f"SELECT {select_clause} FROM {table} WHERE {where_clause} {group_clause} {order_clause} {limit_clause}"
