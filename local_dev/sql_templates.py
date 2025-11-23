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
    if caps.time.quarter_col and q is not None:
        where.append(f"{caps.time.quarter_col} = '{int(q)}'")

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
        if metric == "date":
            # For earliest/latest, selection handled in earliest_latest template
            return "1 AS _noop"
    elif table == "finra_ats":
        if metric == "volume":
            return "SUM(total_shares) AS total_shares"
    # Default noop
    return "1 AS _noop"


def build_distinct(intent: QueryIntent, table: str, column: str) -> str:
    caps = get_capabilities(table)
    if not caps:
        raise ValueError(f"Unknown table: {table}")
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
    dims = validate_dimensions(table, intent.dimensions or [])
    selects: List[str] = []
    if dims:
        selects.extend(dims)
    selects.append(_metric_select(table, intent))
    where = _time_filters(table, intent)
    if table == "executing_bd_606" and (intent.metric or "").lower() == "pfof":
        where.append("data_type = 'venue'")
    where_clause = " AND ".join(where) if where else "TRUE"
    group_by = f"GROUP BY {', '.join(dims)}\n" if dims else ""
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
        if (intent.metric or "").lower() == "pfof":
            intent.order_by = "total_pfof_usd"
        elif (intent.metric or "").lower() == "volume":
            intent.order_by = "total_shares" if table != "executing_bd_606" else "estimated_volume"
    intent.limit = intent.top_n
    intent.order_desc = True
    return build_aggregate(intent, table)


def build_top_per_group(intent: QueryIntent, table: str, partition_dim: str) -> str:
    caps = get_capabilities(table)
    if not caps:
        raise ValueError(f"Unknown table: {table}")
    if partition_dim not in caps.allowed_dimensions:
        raise ValueError(f"Invalid partition dimension: {partition_dim}")
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
    measure_alias = "total_pfof_usd" if (intent.metric or "").lower() == "pfof" else "total_shares"
    base_sql = build_aggregate(inner_intent, table).rstrip(";")
    # Use row_number per group
    return (
        f"WITH base AS (\n{base_sql}\n)\n"
        f", ranked AS (\n"
        f"  SELECT *, ROW_NUMBER() OVER (PARTITION BY {partition_dim} ORDER BY {measure_alias} DESC NULLS LAST) AS rn\n"
        f"  FROM base\n"
        f")\n"
        f"SELECT * FROM ranked WHERE rn = 1\n"
        f"ORDER BY {partition_dim};"
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


