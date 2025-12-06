# query_framework.py

import os
import re
import json
from typing import List
import pandas as pd

# -----------------------------
# Schema Loader
# -----------------------------
def load_schema_from_json(filename: str = "606_schema.json") -> str:
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, "r") as f:
        schema = json.load(f)
    return json.dumps(schema, indent=2)

# -----------------------------
# Broker Alias Utilities
# -----------------------------
def load_broker_aliases(filename: str = "executing_bd_aliases.json") -> dict:
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, "r") as f:
        return json.load(f)

def resolve_executing_bd(user_input: str, alias_map: dict) -> str:
    lowered = user_input.lower()
    # Handle nested structure where aliases are under "executing_bd_map" key
    broker_map = alias_map.get("executing_bd_map", alias_map)
    for canonical, aliases in broker_map.items():
        if any(alias.lower() in lowered for alias in aliases):
            return canonical
    return ""

# -----------------------------
# Venue Alias Utilities (Database-based)
# -----------------------------
def resolve_venue_from_db(user_input: str) -> str:
    """Resolve venue alias to canonical name using database table."""
    import psycopg2
    from dotenv import load_dotenv
    
    load_dotenv()
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", 5432),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        cursor = conn.cursor()
        
        # Search for aliases that are contained in the user input
        lowered = user_input.lower()
        cursor.execute(
            "SELECT canonical_name FROM venue_mapping WHERE LOWER(alias) = ANY(string_to_array(%s, ' ')) LIMIT 1",
            (lowered,)
        )
        result = cursor.fetchone()
        
        # If no exact word match, try partial matches
        if not result:
            cursor.execute(
                "SELECT canonical_name FROM venue_mapping WHERE LOWER(alias) = ANY(string_to_array(%s, ' ')) LIMIT 1",
                (lowered.replace('?', '').replace(',', '').replace('.', ''),)
            )
            result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result[0] if result else ""
        
    except Exception as e:
        print(f"Error resolving venue from database: {e}")
        return ""

def resolve_venue(user_input: str, alias_map: dict = None) -> str:
    """Resolve venue alias to canonical name (now uses database)."""
    return resolve_venue_from_db(user_input)

# -----------------------------
# Prompt Template Generator
# -----------------------------
def build_system_prompt(schema_doc: str, guidance_rules: List[str]) -> str:
    rules = "\n".join(f"- {r}" for r in guidance_rules)
    return f"""You are a SQL expert.

Schema:
{schema_doc}

Instructions:
{rules}
"""

# -----------------------------
# Default Guidance Rules
# -----------------------------
DEFAULT_GUIDANCE_RULES = [
    "Use `stock_group` instead of `order_type`.",
    "If user says 'not paid', filter rows where all PFOF-related USD fields are 0 or null.",
    "If user says 'volume', estimate it from cph and usd using volume = (usd / cph) * 100.",
    "If user asks about 'order type', interpret that as referring to marketablelimitpct, nonmarketablelimitpct, and otherpct.",
    "If asked about stocks, use stock_group IN ('SP500', 'OtherStocks').",
    "If asked about options, use stock_group = 'Options'.",
    "Use DISTINCT when listing brokers, venues, or other categories.",
    "Always include WHERE column IS NOT NULL AND column != ''.",
    "Use GROUP BY and SUM(...) for total PFOF queries.",
    "Use AVG(..._cph) for rate-based queries.",
    "executing_bd is the broker that routes the order (usually receives PFOF).",
    "venues is the broker that executes the order (usually receives volume).",
    "If the user asks 'who got the most orders' or mentions 'venue', interpret that as venues field.",
    "When analyzing volume by venue, use the venues field and GROUP BY venues.",
    "When analyzing volume by broker, use the executing_bd field and GROUP BY executing_bd.",
    "If the user asks 'who paid for flow', ask for clarification unless context is clear.",
    "Only generate read-only SQL queries.",
    "When analyzing payment for order flow (PFOF), only include rows where data_type = 'venue'.",
    "To find brokers who received no PFOF, group by executing_bd and use HAVING SUM(COALESCE(..., 0)) = 0 for all PFOF USD fields.",
    "When asked to find the highest value across multiple *_cph columns, unpivot using a CTE and UNION ALL to track the highest per row.",
    "Exclude invalid numeric comparisons like column != ''.",
    "when executing_bd is part of the WHERE clause, include it in the GROUP BY clause.",
    "When venue names are mentioned, use the exact canonical venue name from the database, not aliases or common names.",
    "If multiple venues share the same parent organization (like CBOE, Nasdaq, NYSE), consider using IN clauses with all related venue names when appropriate.",
    "Respond with only the SQL query. Do not include code fences, explanations, or comments — just valid SQL."
]

# -----------------------------
# Classifier
# -----------------------------
def classify_query(user_input: str) -> dict:
    text = user_input.lower()

    tags = {
        # --- Existing tags ---
        "mentions_volume": any(k in text for k in [
            "volume", "number of trades", "how many", "divide payment",
            "ratio of payment to cph", "payment over cph", "payment per rate",
            "calculate volume", "payment to cph ratio"
        ]),
        "mentions_pfof": "pfof" in text or "payment for order flow" in text,
        "mentions_order_type": "order type" in text,
        "ambiguous_paid": "who paid" in text,
        "mentions_rate": any(k in text for k in ["rate", "cents per", "per share"]),
        "mentions_max": any(k in text for k in ["highest", "maximum"]),
        "mentions_zero_pfof": any(k in text for k in ["not paid", "no pfof", "zero flow", "received no"]),

        # --- Time filters ---
        "mentions_month": any(k in text for k in [
            "month", "monthly", "last month", "this month"
        ]),
        "mentions_year": any(k in text for k in [
            "year", "annual", "this year", "last year", "yoy"
        ]),
        "mentions_quarter": any(k in text for k in [
            "quarter", "q1", "q2", "q3", "q4"
        ]),

        # --- Entity / dimension filters ---
        "mentions_broker": any(k in text for k in [
            "broker", "bd", "executing broker", "receiving broker"
        ]),
        "mentions_venue": any(k in text for k in [
            "venue", "exchange", "market center"
        ]),
        "mentions_trend": any(k in text for k in [
            "trend", "compare", "change over", "increase", "decrease"
        ]),

        # --- Specific year parsing ---
        "year": None,
        "month": None,
        "stock_group": "SP500" if any(k in user_input.upper() for k in ["SP500", "S&P 500", "S&P500"]) else None,
    }

    # --- Extract numeric year (e.g. 2023, 2024) ---
    match_year = re.search(r"\b(20[0-9]{2})\b", user_input)
    if match_year:
        tags["year"] = int(match_year.group(1))

    # --- Extract month if present ---
    months = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]
    for i, m in enumerate(months, start=1):
        if m in text:
            tags["month"] = i
            break

    # Add broker resolution
    broker_alias_map = load_broker_aliases()
    resolved_broker = resolve_executing_bd(user_input, broker_alias_map)
    if resolved_broker:
        tags["executing_bd"] = resolved_broker

    # Add venue resolution (now uses database)
    resolved_venue = resolve_venue(user_input)
    if resolved_venue:
        tags["venue"] = resolved_venue

    return tags

# -----------------------------
# Utility: Sanitize SQL
# -----------------------------
def sanitize_sql_output(sql: str) -> str:
    if "```" in sql:
        parts = sql.split("```")
        sql_candidates = [s for s in parts if "select" in s.lower()]
        if sql_candidates:
            sql = sql_candidates[0]

    if "select" in sql.lower():
        sql = sql[sql.lower().find("select"):]

    if sql.lower().startswith("sql\n"):
        sql = sql[4:]

    sql = re.sub(r"\b\w+\s*!=\s*''", "", sql)
    sql = re.sub(r"\bAND\s+AND\b", "AND", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bOR\s+OR\b", "OR", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\b(AND|OR)\s*(GROUP BY|ORDER BY|LIMIT)", r"\2", sql, flags=re.IGNORECASE)
    # Remove trailing AND/OR at the end of WHERE clauses
    sql = re.sub(r"\b(AND|OR)\s*;?\s*$", "", sql, flags=re.IGNORECASE)

    return sql.strip()
    
def clean_and_dedup(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows with nulls or empty strings in any column,
    then remove duplicates.
    """
    df = df.dropna(how="any")
    df = df[~df.apply(lambda row: row.astype(str).str.strip().eq("").any(), axis=1)]
    return df.drop_duplicates()

# -----------------------------
# Custom Query Generator
# -----------------------------

def generate_volume_estimation_query(year: int = 2024, stock_group: str = 'SP500', executing_bd: str = None, venue: str = None, query_by_venue: bool = False) -> str:
    """Generate query to estimate volume from cph and usd"""
    where_conditions = [
        f"year = {year}" if year is not None else "year IS NOT NULL",
        f"stock_group = '{stock_group}'" if stock_group is not None else "stock_group IS NOT NULL",
        "data_type = 'venue'"
    ]
    
    # Determine grouping and filtering based on query type
    if query_by_venue:
        # Query by venues field for venue-based volume analysis
        where_conditions.extend([
            "venues IS NOT NULL",
            "venues != ''"
        ])
        group_by_field = "venues"
        select_field = "venues"
        
        # Add venue filter if specified
        if venue:
            where_conditions.append(f"venues = '{venue}'")
    else:
        # Query by executing_bd field for broker-based volume analysis
        where_conditions.extend([
            "executing_bd IS NOT NULL",
            "executing_bd != ''"
        ])
        group_by_field = "executing_bd"
        select_field = "executing_bd"
        
        # Add executing_bd filter if specified
        if executing_bd:
            where_conditions.append(f"executing_bd = '{executing_bd}'")
    
    where_clause = " AND ".join(where_conditions)
    
    return f"""
SELECT 
  {select_field},
  SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) +
      COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
      COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
      COALESCE(netpmtpaidrecvotherordersusd, 0)) as total_usd,
  AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) +
      COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) +
      COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) +
      COALESCE(netpmtpaidrecvotherorderscph, 0)) as avg_cph,
  CASE 
    WHEN AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) +
             COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) +
             COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) +
             COALESCE(netpmtpaidrecvotherorderscph, 0)) > 0
    THEN ROUND((SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) +
                    COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
                    COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
                    COALESCE(netpmtpaidrecvotherordersusd, 0)) / 
                AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) +
                    COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) +
                    COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) +
                    COALESCE(netpmtpaidrecvotherorderscph, 0))) * 100, 2)
    ELSE 0
  END as estimated_volume
FROM executing_bd_606
WHERE {where_clause}
GROUP BY {group_by_field}
ORDER BY estimated_volume DESC
LIMIT 1;
"""
