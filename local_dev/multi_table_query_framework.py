# multi_table_query_framework.py

import os
import re
import json
from typing import List, Dict, Optional, Tuple
import pandas as pd

# -----------------------------
# Multi-Table Schema Management
# -----------------------------

def load_all_schemas(schemas_dir: str = "schemas") -> Dict[str, Dict]:
    """Load all table schemas from the schemas directory"""
    schemas = {}
    schemas_path = os.path.join(os.path.dirname(__file__), schemas_dir)
    
    for filename in os.listdir(schemas_path):
        if filename.endswith('_schema.json'):
            table_name = filename.replace('_schema.json', '')
            filepath = os.path.join(schemas_path, filename)
            with open(filepath, 'r') as f:
                schemas[table_name] = json.load(f)
    
    return schemas

def get_relevant_tables(query_tags: Dict, all_schemas: Dict[str, Dict]) -> List[str]:
    """Determine which tables are relevant based on query classification"""
    relevant_tables = []
    
    # Always include venue_mapping for alias resolution
    if 'venue_mapping' in all_schemas:
        relevant_tables.append('venue_mapping')
    
    # PFOF queries - main 606 table
    if query_tags.get('mentions_pfof') or query_tags.get('mentions_volume'):
        if 'executing_bd_606' in all_schemas:
            relevant_tables.append('executing_bd_606')
    
    # Volume/market data queries
    if query_tags.get('mentions_volume') or query_tags.get('mentions_trend'):
        if 'monthly_data' in all_schemas:
            relevant_tables.append('monthly_data')
        if 'finra_ats' in all_schemas:
            relevant_tables.append('finra_ats')
    
    # Venue/entity type queries
    if query_tags.get('mentions_venue') or query_tags.get('mentions_broker'):
        if 'entity_types' in all_schemas:
            relevant_tables.append('entity_types')
        if 'executing_bd_606' in all_schemas:
            relevant_tables.append('executing_bd_606')
    
    # Time-based queries
    if query_tags.get('mentions_month') or query_tags.get('mentions_year') or query_tags.get('mentions_quarter'):
        if 'monthly_data' in all_schemas:
            relevant_tables.append('monthly_data')
        if 'finra_ats' in all_schemas:
            relevant_tables.append('finra_ats')
        if 'executing_bd_606' in all_schemas:
            relevant_tables.append('executing_bd_606')
    
    # If no specific patterns match, include main tables
    if not relevant_tables:
        relevant_tables = ['executing_bd_606', 'venue_mapping']
    
    return relevant_tables

def build_table_schema_doc(table_name: str, schema: Dict) -> str:
    """Build a formatted schema document for a single table"""
    columns = []
    for col in schema['columns']:
        col_desc = f"  {col['name']:<30} | {col['type']:<15} | {col.get('description', '')}"
        if 'values' in col:
            col_desc += f" (values: {', '.join(col['values'])})"
        columns.append(col_desc)
    
    relationships = []
    if 'relationships' in schema:
        for rel in schema['relationships']:
            relationships.append(f"  -> {rel['target_table']} via {rel['join_condition']}")
    
    doc = f"""
Table: {table_name}
Description: {schema.get('description', '')}
Columns:
{chr(10).join(columns)}"""
    
    if relationships:
        doc += f"\nRelationships:\n{chr(10).join(relationships)}"
    
    if 'query_patterns' in schema:
        doc += f"\nCommon Query Patterns: {', '.join(schema['query_patterns'])}"
    
    return doc

def build_multi_table_schema_doc(relevant_tables: List[str], all_schemas: Dict[str, Dict]) -> str:
    """Build a comprehensive schema document for relevant tables only"""
    schema_docs = []
    
    for table_name in relevant_tables:
        if table_name in all_schemas:
            schema_docs.append(build_table_schema_doc(table_name, all_schemas[table_name]))
    
    return "\n".join(schema_docs)

# -----------------------------
# Enhanced Query Classification
# -----------------------------

def classify_query_enhanced(user_input: str) -> Dict:
    """Enhanced query classification with table routing"""
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

        # --- Table-specific patterns ---
        "mentions_ats": any(k in text for k in [
            "ats", "alternative trading system", "finra"
        ]),
        "mentions_virtu": any(k in text for k in [
            "virtu", "virtual", "virtu financial"
        ]),
        "mentions_tape": any(k in text for k in [
            "tape a", "tape b", "tape c", "tape"
        ]),
        "mentions_entity_type": any(k in text for k in [
            "entity type", "exchange", "market maker", "organization"
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

    return tags

# -----------------------------
# Multi-Table Prompt Builder
# -----------------------------

def build_multi_table_system_prompt(user_input: str, all_schemas: Dict[str, Dict]) -> str:
    """Build a targeted system prompt based on query analysis"""
    
    # Classify the query
    query_tags = classify_query_enhanced(user_input)
    
    # Get relevant tables
    relevant_tables = get_relevant_tables(query_tags, all_schemas)
    
    # Build schema document for relevant tables only
    schema_doc = build_multi_table_schema_doc(relevant_tables, all_schemas)
    
    # Build targeted guidance rules
    guidance_rules = build_targeted_guidance_rules(query_tags, relevant_tables)
    
    rules = "\n".join(f"- {r}" for r in guidance_rules)
    
    return f"""You are a SQL expert. You help users translate natural language questions into valid SQL queries.

Relevant Database Schema:
{schema_doc}

Instructions:
{rules}

IMPORTANT: Only use the tables and columns shown above. Do not reference tables not included in the schema.
"""

def build_targeted_guidance_rules(query_tags: Dict, relevant_tables: List[str]) -> List[str]:
    """Build targeted guidance rules based on query classification and relevant tables"""
    rules = [
        "Only generate read-only SQL queries.",
        "Always include WHERE column IS NOT NULL AND column != '' for text fields.",
        "Use DISTINCT when listing values from single columns.",
        "Use GROUP BY and SUM(...) for aggregation queries.",
        "Use AVG(...) for rate-based queries."
    ]
    
    # PFOF-specific rules
    if query_tags.get('mentions_pfof') and 'executing_bd_606' in relevant_tables:
        rules.extend([
            "For PFOF queries, use data_type = 'venue' in WHERE clause.",
            "executing_bd is the broker that routes orders (receives PFOF).",
            "venues is the venue that executes orders (pays PFOF).",
            "PFOF USD amounts are in columns ending with 'usd'.",
            "PFOF rates are in columns ending with 'cph' (cents per hundred)."
        ])
    
    # Volume-specific rules
    if query_tags.get('mentions_volume'):
        if 'executing_bd_606' in relevant_tables:
            rules.append("For volume estimation: volume = (usd / cph) * 100")
        if 'monthly_data' in relevant_tables:
            rules.extend([
                "For market volume, use total_shares or total_notional columns.",
                "Tape-specific analysis uses tape_a_shares, tape_b_shares, tape_c_shares."
            ])
    
    # Time-based rules
    if query_tags.get('mentions_month') or query_tags.get('mentions_year'):
        rules.extend([
            "For time filtering, use string comparison: WHERE month = '1' not WHERE month = 1",
            "Use date functions for time-based analysis."
        ])
    
    # Venue/broker rules
    if query_tags.get('mentions_venue') or query_tags.get('mentions_broker'):
        rules.extend([
            "Use venue_mapping table to resolve venue aliases to canonical names.",
            "When venue names are mentioned, use exact canonical names from venue_mapping.",
            "For broker analysis, use executing_bd field in executing_bd_606 table."
        ])
    
    # ATS-specific rules
    if query_tags.get('mentions_ats') and 'finra_ats' in relevant_tables:
        rules.extend([
            "For ATS analysis, use finra_ats table with quarterly data.",
            "Use ats_name for venue identification in ATS queries.",
            "Quarterly data is in year and quarter columns."
        ])
    
    return rules

# -----------------------------
# Query Routing
# -----------------------------

def route_query(user_input: str, all_schemas: Dict[str, Dict]) -> Tuple[str, List[str]]:
    """Route query to appropriate handler and return system prompt + relevant tables"""
    
    query_tags = classify_query_enhanced(user_input)
    relevant_tables = get_relevant_tables(query_tags, all_schemas)
    system_prompt = build_multi_table_system_prompt(user_input, all_schemas)
    
    return system_prompt, relevant_tables

# -----------------------------
# Backward Compatibility
# -----------------------------

def load_schema_from_json(filename: str = "606_schema.json") -> str:
    """Backward compatibility function - loads single table schema"""
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, "r") as f:
        schema = json.load(f)
    return json.dumps(schema, indent=2)

def build_system_prompt(schema_doc: str, guidance_rules: List[str]) -> str:
    """Backward compatibility function - builds single table prompt"""
    rules = "\n".join(f"- {r}" for r in guidance_rules)
    return f"""You are a SQL expert.

Schema:
{schema_doc}

Instructions:
{rules}
"""

# -----------------------------
# Volume Estimation (from original query_framework.py)
# -----------------------------

def generate_volume_estimation_query(user_input: str, query_tags: Dict) -> str:
    """Generate volume estimation query based on user input and classification"""
    
    # Extract parameters from query tags
    year = query_tags.get('year', 2024)
    stock_group = query_tags.get('stock_group', 'SP500')
    
    # Determine if query is by venue or broker
    query_by_venue = query_tags.get('mentions_venue', False)
    
    # Extract venue/broker from user input
    venue = None
    executing_bd = None
    
    # Simple venue/broker extraction (can be enhanced)
    if query_by_venue:
        # Look for venue names in the input
        venue_keywords = ['citadel', 'cboe', 'nasdaq', 'nyse', 'bats', 'iex']
        for keyword in venue_keywords:
            if keyword.lower() in user_input.lower():
                # This would need to be resolved through venue_mapping
                venue = keyword.upper()  # Simplified for now
                break
    else:
        # Look for broker names
        broker_keywords = ['robinhood', 'schwab', 'fidelity', 'etrade']
        for keyword in broker_keywords:
            if keyword.lower() in user_input.lower():
                executing_bd = keyword.upper()  # Simplified for now
                break
    
    return generate_volume_estimation_query_detailed(
        year=year,
        stock_group=stock_group,
        executing_bd=executing_bd,
        venue=venue,
        query_by_venue=query_by_venue
    )

def generate_volume_estimation_query_detailed(year: int = 2024, stock_group: str = 'SP500', executing_bd: str = None, venue: str = None, query_by_venue: bool = False) -> str:
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

# -----------------------------
# SQL Sanitization (from original query_framework.py)
# -----------------------------

def sanitize_sql_output(sql: str) -> str:
    """Clean and sanitize SQL output from LLM"""
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

# -----------------------------
# Venue Resolution (from original query_framework.py)
# -----------------------------

def resolve_venue_from_db(user_input: str) -> Optional[str]:
    """Resolve venue alias to canonical name from database"""
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", 5432),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        cursor = conn.cursor()
        
        # Split user input into words and check for matches
        words = user_input.lower().split()
        
        for word in words:
            # Clean the word (remove punctuation)
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) < 3:  # Skip very short words
                continue
                
            cursor.execute(
                "SELECT canonical_name FROM venue_mapping WHERE alias ILIKE %s LIMIT 1",
                (f"%{clean_word}%",)
            )
            result = cursor.fetchone()
            if result:
                cursor.close()
                conn.close()
                return result[0]
        
        cursor.close()
        conn.close()
        return None
        
    except Exception as e:
        print(f"Error resolving venue: {e}")
        return None

def resolve_venue(user_input: str) -> Optional[str]:
    """Resolve venue alias to canonical name"""
    return resolve_venue_from_db(user_input)

# -----------------------------
# Broker Resolution (from original query_framework.py)
# -----------------------------

def load_broker_aliases(filename: str = "executing_bd_aliases.json") -> dict:
    """Load broker aliases from JSON file"""
    try:
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def resolve_executing_bd(user_input: str, alias_map: dict) -> Optional[str]:
    """Resolve executing broker alias to canonical name"""
    text = user_input.lower()
    
    for canonical_name, aliases in alias_map.items():
        for alias in aliases:
            if alias.lower() in text:
                return canonical_name
    return None

# Default guidance rules for backward compatibility
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
    "Only generate read-only SQL queries."
]
