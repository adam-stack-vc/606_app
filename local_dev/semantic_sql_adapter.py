
"""
semantic_sql_adapter.py
Hybrid NL2SQL semantic layer for the 606 App
Integrates:
- QueryIntent
- LangChain SQLDatabaseChain (semantic hints only)
- Direction + time disambiguation
- Deterministic SQL builder
"""

import os
from langchain_experimental.sql import SQLDatabaseChain
from langchain.utilities import SQLDatabase
from langchain_openai import ChatOpenAI

from context_direction import disambiguate_context
from query_intent import QueryIntent

# ----------------------------------------------------------
# Load restricted DB environment
# ----------------------------------------------------------

def load_db():
    return SQLDatabase.from_uri(
        os.getenv("DB_URI"),
        include_tables=[
            "executing_bd_606",
            "venue_mapping",
            "broker_profiles",
            "monthly_data"
        ]
    )

db = load_db()

# ----------------------------------------------------------
# LangChain SQL chain (semantic patterns only)
# ----------------------------------------------------------

llm = ChatOpenAI(model="gpt-4o-mini")

sql_chain = SQLDatabaseChain.from_llm(
    llm,
    db,
    verbose=False,
    return_intermediate_steps=True
)

# ----------------------------------------------------------
# Wrapper: Get semantic SQL hint (no execution!)
# ----------------------------------------------------------

def get_sql_hint(question: str, intent: QueryIntent):
    """
    Only call LangChain when we need help interpreting:
    - earliest, latest, first, oldest
    - for each entity
    - top/bottom N
    - superlatives
    """
    trigger_words = [
        "earliest", "latest", "first", "oldest", "newest",
        "for each", "per", "by",
        "top", "bottom",
        "largest", "highest", "lowest"
    ]
    if any(w in question.lower() for w in trigger_words):
        try:
            result = sql_chain.generate_sql(question)
            return result
        except Exception:
            return None
    return None

# ----------------------------------------------------------
# Main orchestrator
# ----------------------------------------------------------

def build_intent_from_user_input(user_input: str, tags: dict) -> QueryIntent:
    tags = disambiguate_context(user_input, tags)
    return QueryIntent.from_tags(tags)   # Requires .from_tags constructor


def merge_sql_hint(intent: QueryIntent, sql_hint: str):
    """
    Parse LangChain SQL and map:
    - GROUP BY
    - ORDER BY
    - LIMIT
    - MIN/MAX aggregations
    Into intent fields.
    """
    if not sql_hint:
        return intent

    sql_lower = sql_hint.lower()

    # GROUP BY
    if "group by" in sql_lower:
        group_part = sql_lower.split("group by")[1].split()[0].strip(",;")
        intent.dimensions.append(group_part)

    # Aggregations
    if "min(" in sql_lower:
        intent.metric = "date"
        intent.aggregation = "MIN"

    if "max(" in sql_lower:
        intent.metric = "date"
        intent.aggregation = "MAX"

    # LIMIT
    if "limit" in sql_lower:
        try:
            limit_val = int(sql_lower.split("limit")[1].strip(" ;"))
            intent.limit = limit_val
        except:
            pass

    return intent


def build_final_sql(intent: QueryIntent, sql_hint: str = None):
    """
    Build deterministic final SQL using:
    - intent fields
    - (optional) sql_hint semantic patterns
    """
    intent = merge_sql_hint(intent, sql_hint)

    # Example template (you will customize per table)
    table = "executing_bd_606"

    select_fields = []
    where_clause = []
    group_by = []

    # Entities
    if "executing_bd" in intent.entities:
        where_clause.append(f"executing_bd = '{intent.entities['executing_bd']}'")
    if "venue" in intent.entities:
        where_clause.append(f"venue = '{intent.entities['venue']}'")

    # Time filters
    if intent.period.get("year"):
        where_clause.append(f"year = {intent.period['year']}")
    if intent.period.get("month"):
        where_clause.append(f"month = {intent.period['month']}")

    # Metric logic
    if intent.metric == "volume":
        select_fields.append("SUM(total_usd) AS total_usd")
        select_fields.append("AVG(cph) AS avg_cph")
        select_fields.append("ROUND((SUM(total_usd) / AVG(cph)) * 100, 2) AS estimated_volume")

    elif intent.metric == "pfof":
        select_fields.append("SUM(total_usd) AS total_payment_usd")

    elif intent.metric == "date" and getattr(intent, "aggregation", None):
        agg = intent.aggregation
        select_fields.append(f"{agg}(routedate) AS date_value")

    # Group by
    for dim in intent.dimensions:
        group_by.append(dim)
        select_fields.append(dim)

    # Build final SQL
    sql = f"""
SELECT {', '.join(select_fields)}
FROM {table}
"""

    if where_clause:
        sql += "WHERE " + " AND ".join(where_clause) + "\n"

    if group_by:
        sql += "GROUP BY " + ", ".join(group_by) + "\n"

    if getattr(intent, "limit", None):
        sql += f"LIMIT {intent.limit}\n"

    return sql.strip()

