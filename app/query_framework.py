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
    for canonical, aliases in alias_map.items():
        if any(alias.lower() in lowered for alias in aliases):
            return canonical
    return ""

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
    "venue is the broker that executes the order (usually receives volume).",
    "If the user asks 'who got the most orders', interpret that as venue.",
    "If the user asks 'who paid for flow', ask for clarification unless context is clear.",
    "Only generate read-only SQL queries.",
    "When analyzing payment for order flow (PFOF), only include rows where data_type = 'venue'.",
    "To find brokers who received no PFOF, group by executing_bd and use HAVING SUM(COALESCE(..., 0)) = 0 for all PFOF USD fields.",
    "When asked to find the highest value across multiple *_cph columns, unpivot using a CTE and UNION ALL to track the highest per row.",
    "Exclude invalid numeric comparisons like column != ''.",
    "when executing_bd is part of the WHERE clause, include it in the GROUP BY clause.",
    "Respond with only the SQL query. Do not include code fences, explanations, or comments — just valid SQL."
]

# -----------------------------
# Classifier
# -----------------------------
def classify_query(user_input: str) -> dict:
    tags = {
        "mentions_volume": any(k in user_input.lower() for k in ["volume", "number of trades", "how many"]),
        "mentions_pfof": "pfof" in user_input.lower() or "payment for order flow" in user_input.lower(),
        "mentions_order_type": "order type" in user_input.lower(),
        "ambiguous_paid": "who paid" in user_input.lower(),
        "mentions_rate": any(k in user_input.lower() for k in ["rate", "cents per", "per share"]),
        "mentions_max": any(k in user_input.lower() for k in ["highest", "maximum"]),
        "mentions_zero_pfof": any(k in user_input.lower() for k in ["not paid", "no pfof", "zero flow", "received no"]),
        "mentions_combined_metric": any(k in user_input.lower() for k in ["divide payment", "ratio of payment to cph", "payment over cph", "payment per rate", "calculate volune"]),
        "year": 2024 if "2024" in user_input else None,
        "stock_group": "SP500" if "sp500" in user_input.upper() else None
    }

    # Add broker resolution
    alias_map = load_broker_aliases()
    resolved = resolve_executing_bd(user_input, alias_map)
    if resolved:
        tags["executing_bd"] = resolved

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
    sql = re.sub(r"\b(AND|OR)\s*(GROUP BY|ORDER BY|LIMIT)", r"\2", sql, flags=re.IGNORECASE)

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
def generate_payment_to_cph_ratio_query(year: int = 2024, stock_group: str = 'SP500') -> str:
    return f"""
SELECT 
  executing_bd,
  CASE
    WHEN
     (
       AVG(
        COALESCE(netpmtpaidrecvmarketorderscph, 0) +
        COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) +
        COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) +
        COALESCE(netpmtpaidrecvotherorderscph, 0)
      )
    ) <= 0
    THEN 'could not calculate because values are indivisible'
    ELSE
      ROUND(
      (
      SUM(
        COALESCE(netpmtpaidrecvmarketordersusd, 0) +
        COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
        COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
        COALESCE(netpmtpaidrecvotherordersusd, 0)
      ) 
      ) /
      NULLIF(
        AVG(
          COALESCE(netpmtpaidrecvmarketorderscph, 0) +
          COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) +
          COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) +
          COALESCE(netpmtpaidrecvotherorderscph, 0)
        ), 0
      ), 4
    )::text
  END AS payment_to_cph_ratio
FROM executing_bd_606
WHERE
  year = {year} AND
  stock_group = '{stock_group}' AND
  data_type = 'venue' AND
  executing_bd IS NOT NULL AND
  executing_bd != ''
GROUP BY executing_bd;
"""
