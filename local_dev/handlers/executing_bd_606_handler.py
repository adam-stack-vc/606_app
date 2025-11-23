# handlers/executing_bd_606_handler.py
from typing import Dict

def generate_top_cph_brokers_query(query_tags: Dict) -> str:
    """Return top 3 brokers by maximum CPH across *_cph columns within each stock_group for a given month/year."""
    where_conditions = ["data_type = 'venue'"]
    year = query_tags.get('year')
    month = query_tags.get('month')
    if year:
        where_conditions.append(f"year = {year}")
    if month:
        # month is stored as VARCHAR; use string literal
        where_conditions.append(f"month = '{month}'")
    # Only consider rows with a valid stock_group and broker
    where_conditions.extend([
        "stock_group IS NOT NULL",
        "stock_group != ''",
        "executing_bd IS NOT NULL",
        "executing_bd != ''"
    ])

    where_clause = " AND ".join(where_conditions)

    return f"""
WITH base AS (
  SELECT
    executing_bd,
    stock_group,
    GREATEST(
      COALESCE(netpmtpaidrecvmarketorderscph, 0),
      COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0),
      COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0),
      COALESCE(netpmtpaidrecvotherorderscph, 0)
    ) AS cph_row
  FROM executing_bd_606
  WHERE {where_clause}
), agg AS (
  SELECT
    executing_bd,
    stock_group,
    MAX(cph_row) AS cph_max
  FROM base
  GROUP BY executing_bd, stock_group
), ranked AS (
  SELECT
    executing_bd,
    stock_group,
    cph_max,
    ROW_NUMBER() OVER (PARTITION BY stock_group ORDER BY cph_max DESC NULLS LAST) AS rn
  FROM agg
)
SELECT executing_bd, stock_group, cph_max
FROM ranked
WHERE rn <= 3
ORDER BY stock_group, cph_max DESC;
"""

def generate_top_pfof_broker_per_stock_group_query(query_tags: Dict) -> str:
    """Return the top broker by total PFOF USD within each stock_group for an optional month/year filter."""
    where_conditions = ["data_type = 'venue'"]
    year = query_tags.get('year')
    month = query_tags.get('month')
    if year:
        where_conditions.append(f"year = {year}")
    if month:
        where_conditions.append(f"month = '{month}'")
    where_conditions.extend([
        "stock_group IS NOT NULL",
        "stock_group != ''",
        "executing_bd IS NOT NULL",
        "executing_bd != ''"
    ])

    where_clause = " AND ".join(where_conditions)

    return f"""
WITH base AS (
  SELECT
    executing_bd,
    stock_group,
    SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) +
        COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
        COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
        COALESCE(netpmtpaidrecvotherordersusd, 0)) AS total_pfof_usd
  FROM executing_bd_606
  WHERE {where_clause}
  GROUP BY executing_bd, stock_group
), ranked AS (
  SELECT
    executing_bd,
    stock_group,
    total_pfof_usd,
    ROW_NUMBER() OVER (PARTITION BY stock_group ORDER BY total_pfof_usd DESC NULLS LAST) AS rn
  FROM base
)
SELECT executing_bd, stock_group, total_pfof_usd
FROM ranked
WHERE rn = 1
ORDER BY stock_group;
"""

def generate_top_pfof_broker_per_order_type_query(query_tags: Dict) -> str:
    """Return the top broker by total PFOF USD within each order type for an optional month/year filter."""
    where_conditions = ["data_type = 'venue'"]
    year = query_tags.get('year')
    month = query_tags.get('month')
    if year:
        where_conditions.append(f"year = {year}")
    if month:
        where_conditions.append(f"month = '{month}'")
    where_conditions.extend([
        "executing_bd IS NOT NULL",
        "executing_bd != ''"
    ])

    where_clause = " AND ".join(where_conditions)

    return f"""
WITH exploded AS (
  SELECT executing_bd, 'market' AS order_type, COALESCE(netpmtpaidrecvmarketordersusd, 0) AS usd
  FROM executing_bd_606 WHERE {where_clause}
  UNION ALL
  SELECT executing_bd, 'marketable_limit' AS order_type, COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) AS usd
  FROM executing_bd_606 WHERE {where_clause}
  UNION ALL
  SELECT executing_bd, 'nonmarketable_limit' AS order_type, COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) AS usd
  FROM executing_bd_606 WHERE {where_clause}
  UNION ALL
  SELECT executing_bd, 'other' AS order_type, COALESCE(netpmtpaidrecvotherordersusd, 0) AS usd
  FROM executing_bd_606 WHERE {where_clause}
), agg AS (
  SELECT executing_bd, order_type, SUM(usd) AS total_pfof_usd
  FROM exploded
  GROUP BY executing_bd, order_type
), ranked AS (
  SELECT executing_bd, order_type, total_pfof_usd,
         ROW_NUMBER() OVER (PARTITION BY order_type ORDER BY total_pfof_usd DESC NULLS LAST) AS rn
  FROM agg
)
SELECT executing_bd, order_type, total_pfof_usd
FROM ranked
WHERE rn = 1
ORDER BY order_type;
"""

def generate_earliest_pfof_month_query() -> str:
    """Earliest month/year in dataset where total PFOF > 0."""
    return """
WITH by_month AS (
  SELECT
    year,
    month,
    SUM(
      COALESCE(netpmtpaidrecvmarketordersusd, 0) +
      COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
      COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
      COALESCE(netpmtpaidrecvotherordersusd, 0)
    ) AS total_pfof_usd
  FROM executing_bd_606
  WHERE data_type = 'venue'
  GROUP BY year, month
)
SELECT
  year,
  month,
  total_pfof_usd
FROM by_month
WHERE total_pfof_usd > 0
ORDER BY year ASC, (NULLIF(month, '')::int) ASC
LIMIT 1;
"""

def generate_earliest_pfof_by_broker_query() -> str:
    """Earliest month/year per broker where PFOF > 0."""
    return """
WITH by_broker_month AS (
  SELECT
    executing_bd,
    year,
    month,
    SUM(
      COALESCE(netpmtpaidrecvmarketordersusd, 0) +
      COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
      COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
      COALESCE(netpmtpaidrecvotherordersusd, 0)
    ) AS total_pfof_usd
  FROM executing_bd_606
  WHERE data_type = 'venue'
    AND executing_bd IS NOT NULL AND executing_bd != ''
  GROUP BY executing_bd, year, month
), first_paid AS (
  SELECT
    executing_bd,
    year,
    month,
    total_pfof_usd,
    ROW_NUMBER() OVER (
      PARTITION BY executing_bd
      ORDER BY year ASC, (NULLIF(month,'')::int) ASC
    ) AS rn
  FROM by_broker_month
  WHERE total_pfof_usd > 0
)
SELECT executing_bd, year, month, total_pfof_usd
FROM first_paid
WHERE rn = 1
ORDER BY year ASC, (NULLIF(month,'')::int) ASC
LIMIT 50;
"""

def generate_longest_broker_venue_streak_query() -> str:
    """Compute the longest consecutive month streak with PFOF > 0 for each broker→venue pair and return the top results."""
    return """
WITH monthly AS (
  SELECT
    executing_bd,
    venues,
    year,
    NULLIF(month,'')::int AS month_num,
    SUM(
      COALESCE(netpmtpaidrecvmarketordersusd, 0) +
      COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
      COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
      COALESCE(netpmtpaidrecvotherordersusd, 0)
    ) AS total_pfof_usd
  FROM executing_bd_606
  WHERE data_type = 'venue'
    AND executing_bd IS NOT NULL AND executing_bd != ''
    AND venues IS NOT NULL AND venues != ''
    AND month IS NOT NULL AND month != ''
  GROUP BY executing_bd, venues, year, NULLIF(month,'')::int
), filtered AS (
  SELECT *, (year * 12 + month_num) AS month_index
  FROM monthly
  WHERE total_pfof_usd > 0
), streaks AS (
  SELECT
    executing_bd,
    venues,
    year,
    month_num,
    month_index,
    (month_index - ROW_NUMBER() OVER (PARTITION BY executing_bd, venues ORDER BY year, month_num)) AS grp
  FROM filtered
), agg AS (
  SELECT
    executing_bd,
    venues,
    MIN(year) AS start_year,
    MIN(month_num) AS start_month,
    MAX(year) AS end_year,
    MAX(month_num) AS end_month,
    COUNT(*) AS streak_length
  FROM streaks
  GROUP BY executing_bd, venues, grp
)
SELECT *
FROM agg
ORDER BY streak_length DESC, executing_bd, venues
LIMIT 10;
"""


def generate_top_pfof_broker_per_quarter_query(query_tags: Dict) -> str:
    """Top broker by total PFOF USD per quarter in a given year."""
    year = query_tags.get('year', 2024)
    return f"""
WITH per_broker_quarter AS (
  SELECT
    CASE
      WHEN month IN ('1','2','3') THEN 1
      WHEN month IN ('4','5','6') THEN 2
      WHEN month IN ('7','8','9') THEN 3
      WHEN month IN ('10','11','12') THEN 4
    END AS quarter,
    executing_bd,
    SUM(
      COALESCE(netpmtpaidrecvmarketordersusd, 0)
    + COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0)
    + COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0)
    + COALESCE(netpmtpaidrecvotherordersusd, 0)
    ) AS total_pfof_usd
  FROM executing_bd_606
  WHERE data_type = 'venue' AND year = {year}
    AND month IS NOT NULL AND month != ''
    AND executing_bd IS NOT NULL AND executing_bd != ''
  GROUP BY quarter, executing_bd
), ranked AS (
  SELECT
    quarter, executing_bd, total_pfof_usd,
    ROW_NUMBER() OVER (PARTITION BY quarter ORDER BY total_pfof_usd DESC NULLS LAST) AS rn
  FROM per_broker_quarter
)
SELECT quarter, executing_bd, total_pfof_usd
FROM ranked
WHERE rn = 1
ORDER BY quarter;
"""

