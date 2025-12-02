from __future__ import annotations

"""
sql_templates.py
Reusable SQL templates for common operations:
 - distinct (list/unique)
 - aggregate (sum/count/avg) with optional breakdowns
 - topN (ORDER BY aggregate LIMIT N)
 - top-per-group (ROW_NUMBER per partition)
 - earliest/latest (MIN/MAX date buckets)
"""

from typing import List, Optional, Dict

from query_intent import QueryIntent
from capability_registry import (
    get_capabilities,
    validate_dimensions,
    requires_monthly_data_bucketing,
    allowed_metric,
)
from value_normalizer import normalize_value


def _safe_ident(name: str) -> str:
    return name.replace('"', "").replace(";", "")


def _time_filters(table: str, intent: QueryIntent) -> List[str]:
    caps = get_capabilities(table)
    if not caps:
        return []
    where = []
    y = intent.period.get("year")
    m = intent.period.get("month")
    q = intent.period.get("quarter")

    # executing_bd_606, finra_ats have explicit year/month/quarter columns
    if caps.time.year_col and y is not None:
        where.append(f"{caps.time.year_col} = {int(y)}")
    if caps.time.month_col and m is not None:
        where.append(f"{caps.time.month_col} = '{int(m)}'")

    # Handle quarter filtering
    if q is not None:
        if caps.time.quarter_col:
            # Table has explicit quarter column
            where.append(f"{caps.time.quarter_col} = '{int(q)}'")
        elif caps.time.month_col and not m:
            # Table has month column but no quarter column - convert quarter to months
            quarter_months = {
                1: [1, 2, 3],
                2: [4, 5, 6],
                3: [7, 8, 9],
                4: [10, 11, 12]
            }
            if q in quarter_months:
                months_in_q = quarter_months[q]
                # Use IN clause for quarter months
                month_list = ','.join(f"'{m}'" for m in months_in_q)
                where.append(f"{caps.time.month_col} IN ({month_list})")

    # monthly_data uses 'day' and requires EXTRACT
    if caps.time.day_col:
        if y is not None:
            where.append(f"EXTRACT(YEAR FROM {caps.time.day_col}) = {int(y)}")
        if m is not None:
            where.append(f"EXTRACT(MONTH FROM {caps.time.day_col}) = {int(m)}")
        if q is not None:
            where.append(f"EXTRACT(QUARTER FROM {caps.time.day_col}) = {int(q)}")

    return where


def _pfof_sum_expr(table: str) -> str:
    # Only defined for executing_bd_606
    if table == "executing_bd_606":
        return (
            "COALESCE(netpmtpaidrecvmarketordersusd, 0) + "
            "COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) + "
            "COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) + "
            "COALESCE(netpmtpaidrecvotherordersusd, 0)"
        )
    # Fallback for unknown: let caller pass explicit select if needed
    return "0"


def _metric_select(table: str, intent: QueryIntent) -> str:
    metric = (intent.metric or "").lower()
    agg = (intent.aggregation or "SUM").upper()

    if table == "executing_bd_606":
        if metric == "pfof_and_volume":
            # Multi-metric: both PFOF and estimated volume
            pfof_expr = f"{agg}({_pfof_sum_expr(table)}) AS total_pfof_usd"
            volume_expr = (
                "CASE WHEN AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) + "
                "COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) + "
                "COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) + "
                "COALESCE(netpmtpaidrecvotherorderscph, 0)) > 0 "
                f"THEN ROUND(({_pfof_sum_expr(table)}::numeric / "
                "AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) + "
                "COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) + "
                "COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) + "
                "COALESCE(netpmtpaidrecvotherorderscph, 0))) * 100, 2) "
                "ELSE 0 END AS estimated_volume"
            )
            return f"{pfof_expr}, {volume_expr}"
        if metric == "pfof":
            return f"{agg}({_pfof_sum_expr(table)}) AS total_pfof_usd"
        if metric == "rate":
            # Average across *_cph columns
            return (
                "AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) + "
                "COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) + "
                "COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) + "
                "COALESCE(netpmtpaidrecvotherorderscph, 0)) AS avg_cph"
            )
        if metric == "volume":
            # Estimated volume (usd/cph)*100 averaged across rows
            return (
                "CASE WHEN AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) + "
                "COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) + "
                "COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) + "
                "COALESCE(netpmtpaidrecvotherorderscph, 0)) > 0 "
                f"THEN ROUND(({_pfof_sum_expr(table)}::numeric / "
                "AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) + "
                "COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) + "
                "COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) + "
                "COALESCE(netpmtpaidrecvotherorderscph, 0))) * 100, 2) "
                "ELSE 0 END AS estimated_volume"
            )
    elif table == "monthly_data":
        if metric == "volume":
            return "SUM(total_shares) AS total_shares"
        if metric == "trades":
            return "SUM(total_trades) AS total_trades"
        if metric == "tape_a" or metric == "tape a":
            return "SUM(tape_a_shares) AS tape_a_shares"
        if metric == "tape_b" or metric == "tape b":
            return "SUM(tape_b_shares) AS tape_b_shares"
        if metric == "tape_c" or metric == "tape c":
            return "SUM(tape_c_shares) AS tape_c_shares"
        if metric == "tape":
            # Return all three tapes
            return "SUM(tape_a_shares) AS tape_a_shares, SUM(tape_b_shares) AS tape_b_shares, SUM(tape_c_shares) AS tape_c_shares"
        if metric == "date":
            # For earliest/latest, selection handled in earliest_latest template
            return "1 AS _noop"
    elif table == "finra_ats":
        if metric == "volume":
            return "SUM(total_shares) AS total_shares"
        if metric == "trades":
            return "SUM(total_trades) AS total_trades"
    # Default noop
    return "1 AS _noop"


def build_distinct(intent: QueryIntent, table: str, column: str | list[str]) -> str:
    """
    Build a SELECT DISTINCT query for one or more columns.

    Args:
        intent: QueryIntent with filters
        table: Table name
        column: Single column name or list of column names

    Returns:
        SQL query string
    """
    caps = get_capabilities(table)
    if not caps:
        raise ValueError(f"Unknown table: {table}")

    # Handle multiple columns
    if isinstance(column, list):
        columns = column
    else:
        columns = [column]

    # Build SELECT expressions for each column
    select_exprs = []
    order_exprs = []

    for col in columns:
        # Check if this is a temporal dimension (month/quarter/year) on a table with day column
        is_temporal = col in ["month", "quarter", "year"]

        if is_temporal and caps.time.day_col:
            # Use EXTRACT for temporal dimensions
            if col == "month":
                select_exprs.append(f"EXTRACT(MONTH FROM {caps.time.day_col}) AS month")
                order_exprs.append("month")
            elif col == "quarter":
                select_exprs.append(f"EXTRACT(QUARTER FROM {caps.time.day_col}) AS quarter")
                order_exprs.append("quarter")
            elif col == "year":
                select_exprs.append(f"EXTRACT(YEAR FROM {caps.time.day_col}) AS year")
                order_exprs.append("year")
        elif is_temporal and (caps.time.quarter_col or caps.time.month_col or caps.time.year_col):
            # Table has explicit temporal columns
            if col == "quarter" and caps.time.quarter_col:
                select_exprs.append(f"{caps.time.quarter_col}")
                order_exprs.append(f"{caps.time.quarter_col}")
            elif col == "month" and caps.time.month_col:
                select_exprs.append(f"{caps.time.month_col}")
                order_exprs.append(f"{caps.time.month_col}")
            elif col == "year" and caps.time.year_col:
                select_exprs.append(f"{caps.time.year_col}")
                order_exprs.append(f"{caps.time.year_col}")
        else:
            # Regular column
            select_exprs.append(f"{_safe_ident(col)}")
            order_exprs.append(f"{_safe_ident(col)}")

    where = _time_filters(table, intent)
    # Add NOT NULL checks for all columns
    for col in columns:
        if col not in ["month", "quarter", "year"]:  # temporal columns handled separately
            where.append(f"{_safe_ident(col)} IS NOT NULL")
            where.append(f"{_safe_ident(col)} != ''")

    where_clause = " AND ".join(where) if where else "TRUE"

    return (
        f"SELECT DISTINCT {', '.join(select_exprs)}\n"
        f"FROM {table}\n"
        f"WHERE {where_clause}\n"
        f"ORDER BY {', '.join(order_exprs)};"
    )


def _build_distinct_single_column_legacy(intent: QueryIntent, table: str, column: str) -> str:
    """Legacy single-column version - keeping for reference but not used"""
    caps = get_capabilities(table)
    if not caps:
        raise ValueError(f"Unknown table: {table}")

    # Check if this is a temporal dimension (month/quarter/year) on a table with day column
    is_temporal = column in ["month", "quarter", "year"]

    if is_temporal and caps.time.day_col:
        # Use EXTRACT for temporal dimensions
        if column == "month":
            select_expr = f"EXTRACT(MONTH FROM {caps.time.day_col}) AS month"
            order_expr = "month"
        elif column == "quarter":
            select_expr = f"EXTRACT(QUARTER FROM {caps.time.day_col}) AS quarter"
            order_expr = "quarter"
        elif column == "year":
            select_expr = f"EXTRACT(YEAR FROM {caps.time.day_col}) AS year"
            order_expr = "year"

        where = _time_filters(table, intent)
        where_clause = " AND ".join(where) if where else "TRUE"

        return (
            f"SELECT DISTINCT {select_expr}\n"
            f"FROM {table}\n"
            f"WHERE {where_clause}\n"
            f"ORDER BY {order_expr};"
        )
    elif is_temporal and (caps.time.quarter_col or caps.time.month_col or caps.time.year_col):
        # Table has explicit temporal columns
        if column == "quarter" and caps.time.quarter_col:
            col = caps.time.quarter_col
        elif column == "month" and caps.time.month_col:
            col = caps.time.month_col
        elif column == "year" and caps.time.year_col:
            col = caps.time.year_col
        else:
            raise ValueError(f"Table {table} does not support temporal dimension: {column}")
    else:
        # Regular column
        col = _safe_ident(column)

    where = _time_filters(table, intent)
    where.append(f"{col} IS NOT NULL")
    where.append(f"{col} != ''")
    where_clause = " AND ".join(where) if where else "TRUE"
    return (
        f"SELECT DISTINCT {col}\n"
        f"FROM {table}\n"
        f"WHERE {where_clause}\n"
        f"ORDER BY {col};"
    )


def build_aggregate(intent: QueryIntent, table: str) -> str:
    caps = get_capabilities(table)
    if not caps:
        raise ValueError(f"Unknown table: {table}")

    # Handle temporal dimensions specially for tables with day columns
    dims = []
    temporal_dims = []
    requested_dims = intent.dimensions or []

    for dim in requested_dims:
        if dim in caps.allowed_dimensions:
            dims.append(dim)
        elif dim in ["month", "quarter", "year"] and caps.time.day_col:
            # Table uses day column, need EXTRACT for temporal dimensions
            temporal_dims.append(dim)
        elif dim not in ["month", "quarter", "year"]:
            # Regular dimension but not allowed - validate will filter it
            if dim in caps.allowed_dimensions:
                dims.append(dim)

    selects: List[str] = []
    group_by_cols: List[str] = []

    # Add temporal dimensions with EXTRACT
    if temporal_dims and caps.time.day_col:
        for tdim in temporal_dims:
            if tdim == "month":
                selects.append(f"EXTRACT(MONTH FROM {caps.time.day_col}) AS month")
                group_by_cols.append(f"EXTRACT(MONTH FROM {caps.time.day_col})")
            elif tdim == "quarter":
                selects.append(f"EXTRACT(QUARTER FROM {caps.time.day_col}) AS quarter")
                group_by_cols.append(f"EXTRACT(QUARTER FROM {caps.time.day_col})")
            elif tdim == "year":
                selects.append(f"EXTRACT(YEAR FROM {caps.time.day_col}) AS year")
                group_by_cols.append(f"EXTRACT(YEAR FROM {caps.time.day_col})")

    # Add regular dimensions
    if dims:
        selects.extend(dims)
        group_by_cols.extend(dims)

    selects.append(_metric_select(table, intent))
    where = _time_filters(table, intent)
    if table == "executing_bd_606" and (intent.metric or "").lower() == "pfof":
        where.append("data_type = 'venue'")

    # Add entity filters (e.g., executing_bd, venue)
    if intent.entities:
        for entity_key, entity_value in intent.entities.items():
            if entity_value:
                # Map entity names to actual column names
                # venue -> venues (plural in executing_bd_606 table)
                column_name = "venues" if entity_key == "venue" else entity_key

                if column_name in caps.allowed_dimensions:
                    # Escape single quotes in value
                    safe_value = entity_value.replace("'", "''")
                    where.append(f"{column_name} = '{safe_value}'")

    # Add additional filters from intent.filters
    # Common filters: stock_group, market_participant, ats_name, tier
    if intent.filters:
        for filter_key, filter_value in intent.filters.items():
            if filter_value:
                # Check if this is a valid column for the table
                if filter_key in caps.columns or filter_key in caps.allowed_dimensions:
                    # Normalize value (e.g., "S&P 500" → "SP500")
                    normalized_value = normalize_value(filter_key, str(filter_value))
                    # Escape single quotes in value
                    safe_value = normalized_value.replace("'", "''")
                    where.append(f"{filter_key} = '{safe_value}'")

    where_clause = " AND ".join(where) if where else "TRUE"
    group_by = f"GROUP BY {', '.join(group_by_cols)}\n" if group_by_cols else ""
    order = ""
    if intent.order_by:
        order = f"ORDER BY {intent.order_by} {'DESC' if intent.order_desc else 'ASC'}\n"
    limit = f"LIMIT {int(intent.limit)}\n" if intent.limit else ""
    return (
        f"SELECT {', '.join(selects)}\n"
        f"FROM {table}\n"
        f"WHERE {where_clause}\n"
        f"{group_by}"
        f"{order}"
        f"{limit}".rstrip() + ";"
    )


def build_top_n(intent: QueryIntent, table: str) -> str:
    # Use aggregate and enforce order/limit
    if not intent.top_n:
        raise ValueError("topN requires intent.top_n")
    if not intent.order_by:
        # Default order_by for known metrics
        metric_lower = (intent.metric or "").lower()
        if metric_lower == "pfof":
            intent.order_by = "total_pfof_usd"
        elif metric_lower == "volume":
            intent.order_by = "total_shares" if table != "executing_bd_606" else "estimated_volume"
        elif metric_lower == "trades":
            intent.order_by = "total_trades"
        elif metric_lower in ["tape_a", "tape a"]:
            intent.order_by = "tape_a_shares"
        elif metric_lower in ["tape_b", "tape b"]:
            intent.order_by = "tape_b_shares"
        elif metric_lower in ["tape_c", "tape c"]:
            intent.order_by = "tape_c_shares"
    intent.limit = intent.top_n
    # Only override order_desc if not already set
    if intent.order_desc is None:
        intent.order_desc = True
    return build_aggregate(intent, table)


def build_top_per_group(intent: QueryIntent, table: str, partition_dim: str) -> str:
    caps = get_capabilities(table)
    if not caps:
        raise ValueError(f"Unknown table: {table}")

    # Check if partition_dim is temporal (month/quarter/year) or regular dimension
    is_temporal = partition_dim in ["month", "quarter", "year"]

    if not is_temporal and partition_dim not in caps.allowed_dimensions:
        raise ValueError(f"Invalid partition dimension: {partition_dim}")

    # For temporal dimensions on tables with day column, we need EXTRACT in PARTITION BY
    if is_temporal and caps.time.day_col:
        # Build the EXTRACT expression for the partition
        if partition_dim == "month":
            partition_expr = f"EXTRACT(MONTH FROM {caps.time.day_col})"
        elif partition_dim == "quarter":
            partition_expr = f"EXTRACT(QUARTER FROM {caps.time.day_col})"
        elif partition_dim == "year":
            partition_expr = f"EXTRACT(YEAR FROM {caps.time.day_col})"
    else:
        partition_expr = partition_dim

    # Build base aggregate by (partition_dim, maybe entity dim)
    dims = [partition_dim]
    # if caller pre-sets a second dim (e.g., executing_bd), keep it
    extra_dims = [d for d in (intent.dimensions or []) if d != partition_dim]
    if extra_dims:
        dims.extend(extra_dims[:1])  # keep one extra dimension
    inner_intent = QueryIntent(
        topic=intent.topic,
        metric=intent.metric,
        direction=intent.direction,
        entities=intent.entities.copy(),
        period=intent.period.copy(),
        dimensions=dims,
        filters=intent.filters.copy(),
        aggregation="SUM",
    )
    metric_lower = (intent.metric or "").lower()
    if metric_lower == "pfof":
        measure_alias = "total_pfof_usd"
    elif metric_lower == "trades":
        measure_alias = "total_trades"
    else:
        measure_alias = "total_shares"
    base_sql = build_aggregate(inner_intent, table).rstrip(";")
    # Use row_number per group
    return (
        f"WITH base AS (\n{base_sql}\n)\n"
        f", ranked AS (\n"
        f"  SELECT *, ROW_NUMBER() OVER (PARTITION BY {partition_expr} ORDER BY {measure_alias} DESC NULLS LAST) AS rn\n"
        f"  FROM base\n"
        f")\n"
        f"SELECT * FROM ranked WHERE rn = 1\n"
        f"ORDER BY {partition_expr};"
    )


def build_earliest_latest(intent: QueryIntent, table: str, earliest: bool = True) -> str:
    caps = get_capabilities(table)
    if not caps:
        raise ValueError(f"Unknown table: {table}")
    where = _time_filters(table, intent)
    where_clause = " AND ".join(where) if where else "TRUE"
    order_dir = "ASC" if earliest else "DESC"

    if table == "executing_bd_606":
        # order by (year, month::int)
        return (
            "WITH by_month AS (\n"
            "  SELECT year, month, "
            f"         {_pfof_sum_expr(table)} AS total_pfof_usd\n"
            "  FROM executing_bd_606\n"
            "  WHERE data_type = 'venue'\n"
            "  GROUP BY year, month\n"
            ")\n"
            "SELECT year, month, total_pfof_usd\n"
            "FROM by_month\n"
            "WHERE total_pfof_usd > 0\n"
            f"ORDER BY year {order_dir}, (NULLIF(month,'')::int) {order_dir}\n"
            "LIMIT 1;"
        )
    # monthly_data: use EXTRACT(YEAR/MONTH)
    if requires_monthly_data_bucketing(table):
        day_col = caps.time.day_col or "day"
        return (
            "WITH by_month AS (\n"
            f"  SELECT EXTRACT(YEAR FROM {day_col}) AS year,\n"
            f"         EXTRACT(MONTH FROM {day_col}) AS month,\n"
            "         SUM(total_shares) AS total_shares\n"
            f"  FROM {table}\n"
            f"  WHERE {where_clause}\n"
            f"  GROUP BY EXTRACT(YEAR FROM {day_col}), EXTRACT(MONTH FROM {day_col})\n"
            ")\n"
            "SELECT year, month, total_shares\n"
            "FROM by_month\n"
            f"ORDER BY year {order_dir}, month {order_dir}\n"
            "LIMIT 1;"
        )
    # finra_ats: earliest by year/quarter
    if table == "finra_ats":
        return (
            "SELECT year, quarter, SUM(total_shares) AS total_shares\n"
            "FROM finra_ats\n"
            f"WHERE {where_clause}\n"
            "GROUP BY year, quarter\n"
            f"ORDER BY year {order_dir}, quarter {order_dir}\n"
            "LIMIT 1;"
        )
    # Fallback
    return f"SELECT 1 AS _noop FROM {table} WHERE FALSE;"


def build_string_length(intent: QueryIntent, table: str, column: str, longest: bool = True) -> str:
    """Build SQL to find the row with the longest or shortest string in a column"""
    caps = get_capabilities(table)
    if not caps:
        raise ValueError(f"Unknown table: {table}")

    col = _safe_ident(column)
    where = _time_filters(table, intent)

    # Add additional filters if present
    if intent.filters:
        for filter_key, filter_value in intent.filters.items():
            if filter_value:
                if filter_key in caps.columns or filter_key in caps.allowed_dimensions:
                    safe_value = str(filter_value).replace("'", "''")
                    where.append(f"{filter_key} = '{safe_value}'")

    where.append(f"{col} IS NOT NULL")
    where.append(f"{col} != ''")
    where_clause = " AND ".join(where) if where else "TRUE"

    order_dir = "DESC" if longest else "ASC"

    return (
        f"SELECT {col}, LENGTH({col}) AS name_length\n"
        f"FROM {table}\n"
        f"WHERE {where_clause}\n"
        f"ORDER BY LENGTH({col}) {order_dir}\n"
        "LIMIT 1;"
    )


def build_cross_table_entity_list(intent: QueryIntent, limit: int = 30) -> str:
    """Build SQL to list unique entity names across all three tables (executing_bd_606, monthly_data, finra_ats)"""
    # Extract year filter if present
    year_filter = ""
    if intent.period.get("year"):
        year_val = int(intent.period["year"])
        year_filter = f" WHERE year = {year_val}"

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
        f"LIMIT {int(limit)};"
    )


# Load entity mappings from config file
import json
import os as _os
from pathlib import Path as _Path

_ENTITY_MAPPINGS = None

def _load_entity_mappings():
    """Load entity mappings from entity_mappings.json"""
    global _ENTITY_MAPPINGS
    if _ENTITY_MAPPINGS is None:
        config_path = _Path(__file__).parent / "entity_mappings.json"
        with open(config_path, "r") as f:
            _ENTITY_MAPPINGS = json.load(f)
    return _ENTITY_MAPPINGS


def _map_entity_to_column(entity_type: str, table: str) -> Optional[str]:
    """
    Map generic entity types to table-specific column names.

    Args:
        entity_type: Generic entity name (e.g., "venue", "executing_broker", "market_participant", "ATS")
        table: Table name

    Returns:
        Column name or None if not applicable for this table
    """
    entity_map = _load_entity_mappings()
    return entity_map.get(table, {}).get(entity_type.lower())


def build_count(intent: QueryIntent, table: str, count_dimension: str) -> str:
    """
    Build a COUNT(DISTINCT ...) query.

    Example: "How many venues did Robinhood use?"
    → SELECT COUNT(DISTINCT venues) AS venue_count FROM ...

    Args:
        intent: QueryIntent with filters and period
        table: Table name
        count_dimension: Generic entity type to count (e.g., "venue", "broker")

    Returns:
        SQL query string
    """
    # Map generic entity type to column name
    column = _map_entity_to_column(count_dimension, table)
    if not column:
        raise ValueError(f"Cannot count {count_dimension} in table {table}")

    # Build WHERE clause
    where = _time_filters(table, intent)
    where.append(f"{_safe_ident(column)} IS NOT NULL")
    where.append(f"{_safe_ident(column)} != ''")

    # Add entity filters (e.g., WHERE executing_bd = 'Robinhood')
    for entity_key, entity_val in intent.entities.items():
        entity_col = _map_entity_to_column(entity_key, table)
        if entity_col and entity_val:
            safe_val = entity_val.replace("'", "''")
            where.append(f"{_safe_ident(entity_col)} = '{safe_val}'")

    # Add filters from intent
    for key, val in intent.filters.items():
        # Normalize value (e.g., "S&P 500" → "SP500")
        normalized_val = normalize_value(key, str(val))
        safe_val = normalized_val.replace("'", "''")
        where.append(f"{_safe_ident(key)} = '{safe_val}'")

    where_clause = " AND ".join(where) if where else "TRUE"

    count_alias = f"{count_dimension}_count"

    return (
        f"SELECT COUNT(DISTINCT {_safe_ident(column)}) AS {count_alias}\n"
        f"FROM {table}\n"
        f"WHERE {where_clause};"
    )


def build_per_entity_average(intent: QueryIntent, table: str, per_entity: str) -> str:
    """
    Build a per-entity average query: metric / COUNT(DISTINCT entity)

    Example: "Average PFOF per venue for Robinhood"
    → SELECT SUM(pfof) AS total_pfof, COUNT(DISTINCT venues) AS venue_count,
             SUM(pfof) / COUNT(DISTINCT venues) AS pfof_per_venue

    Args:
        intent: QueryIntent with metric and filters
        table: Table name
        per_entity: Generic entity type for denominator (e.g., "venue", "broker")

    Returns:
        SQL query string
    """
    # Map generic entity type to column name
    entity_column = _map_entity_to_column(per_entity, table)
    if not entity_column:
        raise ValueError(f"Cannot calculate per-{per_entity} average in table {table}")

    # Get metric expression using existing helper
    metric_select = _metric_select(table, intent)

    # Extract expression and alias (e.g., "SUM(...) AS total_pfof")
    # Split to get just the expression part for division
    if " AS " in metric_select:
        metric_expr_only = metric_select.split(" AS ")[0]
        metric_alias = metric_select.split(" AS ")[1].split(",")[0].strip()
    else:
        metric_expr_only = metric_select
        metric_alias = f"{intent.metric or 'metric'}_total"

    # Build WHERE clause
    where = _time_filters(table, intent)

    # Add entity filters (e.g., WHERE executing_bd = 'Robinhood')
    for entity_key, entity_val in intent.entities.items():
        entity_col = _map_entity_to_column(entity_key, table)
        if entity_col and entity_val:
            safe_val = entity_val.replace("'", "''")
            where.append(f"{_safe_ident(entity_col)} = '{safe_val}'")

    # Add filters from intent
    for key, val in intent.filters.items():
        # Normalize value (e.g., "S&P 500" → "SP500")
        normalized_val = normalize_value(key, str(val))
        safe_val = normalized_val.replace("'", "''")
        where.append(f"{_safe_ident(key)} = '{safe_val}'")

    where.append(f"{_safe_ident(entity_column)} IS NOT NULL")
    where.append(f"{_safe_ident(entity_column)} != ''")

    where_clause = " AND ".join(where) if where else "TRUE"

    count_alias = f"{per_entity}_count"
    avg_alias = f"{intent.metric or 'metric'}_per_{per_entity}"

    return (
        f"SELECT\n"
        f"  {metric_select},\n"
        f"  COUNT(DISTINCT {_safe_ident(entity_column)}) AS {count_alias},\n"
        f"  ({metric_expr_only}) / NULLIF(COUNT(DISTINCT {_safe_ident(entity_column)}), 0) AS {avg_alias}\n"
        f"FROM {table}\n"
        f"WHERE {where_clause};"
    )


