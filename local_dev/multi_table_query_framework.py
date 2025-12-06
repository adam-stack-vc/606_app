# multi_table_query_framework.py

import os
import re
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd

# Try importing spacy, handle if missing
try:
    import spacy
except ImportError:
    spacy = None
    print("Warning: 'spacy' not found. NLP features will be disabled.")

# -----------------------------
# Global Resource Loading (NLP & Maps)
# -----------------------------

NLP_MODEL = None
DIRECTION_MAP = {}

def initialize_nlp_resources():
    """Initialize SpaCy model and direction map safely"""
    global NLP_MODEL, DIRECTION_MAP
    
    # Load SpaCy
    if spacy:
        try:
            NLP_MODEL = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: Spacy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")

    # Load Direction Map
    map_path = os.path.join(os.path.dirname(__file__), "direction_map.json")
    if os.path.exists(map_path):
        with open(map_path, "r") as f:
            DIRECTION_MAP = json.load(f)
    else:
        # Fallback/Default map if file is missing to prevent crash
        DIRECTION_MAP = {
            "venue_to_executing_bd": {
                "verbs": ["pay", "paid", "rebate", "send"],
                "subject_role": "venue",
                "object_role": "executing_bd",
                "implied_metric": "pfof"
            },
            "executing_bd_to_venue": {
                "verbs": ["route", "send", "direct"],
                "subject_role": "executing_bd",
                "object_role": "venue",
                "implied_metric": "volume"
            }
        }

# Initialize on module load
initialize_nlp_resources()

# -----------------------------
# Multi-Table Schema Management
# -----------------------------

def load_all_schemas(schemas_dir: str = "schemas") -> Dict[str, Dict]:
    """Load all table schemas from the schemas directory"""
    schemas = {}
    schemas_path = os.path.join(os.path.dirname(__file__), schemas_dir)
    
    if not os.path.exists(schemas_path):
        # Fallback if directory doesn't exist
        return {}

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
# NLP & Time Extraction Helpers
# -----------------------------

MONTHS_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}

def get_direction_for_verb(verb: str):
    """Lookup direction from verb using grouped dictionary"""
    verb = verb.lower()
    for direction, cfg in DIRECTION_MAP.items():
        if verb in cfg["verbs"]:
            return {
                "direction": direction,
                "subject_role": cfg["subject_role"],
                "object_role": cfg["object_role"],
                "implied_metric": cfg.get("implied_metric")
            }
    return None

def extract_time_period(user_input: str) -> dict:
    """Extract time period from text including relative dates"""
    text = user_input.lower()
    now = datetime.now()

    year, month, quarter = None, None, None

    # ---- Explicit year (e.g., 2024)
    year_match = re.search(r"\b(20[0-9]{2})\b", text)
    if year_match:
        year = int(year_match.group(1))

    # ---- Explicit month (e.g., January)
    for m_name, m_num in MONTHS_MAP.items():
        if m_name in text:
            month = m_num
            break

    # ---- Quarter (Q1, Q2, etc.)
    q_match = re.search(r"\bq([1-4])\b", text)
    if q_match:
        quarter = int(q_match.group(1))

    # ---- Relative time expressions
    if "last year" in text:
        year = now.year - 1
    elif "this year" in text:
        year = now.year

    if "this month" in text:
        month = now.month
        year = year or now.year

    if "last month" in text:
        if now.month == 1:
            month = 12
            year = (year or now.year) - 1
        else:
            month = now.month - 1
            year = year or now.year

    if "this quarter" in text:
        quarter = (now.month - 1) // 3 + 1
        year = year or now.year

    if "last quarter" in text:
        q = (now.month - 1) // 3 + 1
        quarter = q - 1 if q > 1 else 4
        year = now.year if q > 1 else now.year - 1

    return {"year": year, "month": month, "quarter": quarter}

def disambiguate_context(user_input: str, tags: dict, debug=False) -> dict:
    """Disambiguate direction + metric + entities + time using NLP"""
    if not NLP_MODEL:
        return tags

    text = user_input.lower()
    doc = NLP_MODEL(text)

    if debug:
        print("\n--- Dependency Parse ---")
        for tok in doc:
            print(f"{tok.text:12s} {tok.dep_:12s} -> {tok.head.text}")
        print("------------------------\n")

    # 1. Step: Direction from verb
    direction_info = None
    for token in doc:
        direction_info = get_direction_for_verb(token.lemma_)
        if direction_info:
            tags["direction"] = direction_info["direction"]
            tags["subject_role"] = direction_info["subject_role"]
            tags["object_role"] = direction_info["object_role"]
            
            if direction_info.get("implied_metric"):
                tags["metric"] = direction_info["implied_metric"]
            break

    # 2. Extract agent/recipient (passive + active)
    agent = None       # semantic sender
    recipient = None   # semantic receiver

    # Special pattern: "For X, how many Y" - X is the entity filter
    # Example: "For Robinhood, how many venues..."
    if text.startswith("for ") and ", how many" in text:
        # Find the entity after "for" and before the comma
        for tok in doc:
            if tok.head.text.lower() == "for" and tok.dep_ == "pobj":
                # This is likely the entity we're filtering by
                # Determine if it's a broker or venue based on context
                if "broker" in text or "executing" in text:
                    agent = tok.text
                elif "venue" in text:
                    # If asking "how many venues", the entity is the broker
                    agent = tok.text
                break

    for tok in doc:
        # Passive voice agent: "by Robinhood"
        if tok.dep_ == "agent":
            for child in tok.children:
                if child.dep_ == "pobj":
                    agent = child.text

        # Recipient via preposition: "to Citadel", "from Robinhood", "for Robinhood"
        if tok.dep_ == "pobj" and tok.head.text.lower() in ["to", "from", "for"]:
            recipient = tok.text

        # Direct object for "send", "pay", etc.
        if tok.dep_ in ["dobj", "pobj"] and tok.head.lemma_ in ["send", "pay"]:
            recipient = tok.text

    # 3. Assign entities based on direction mapping
    if direction_info:
        if direction_info["direction"] == "executing_bd_to_venue":
            if agent: tags["executing_bd"] = agent
            if recipient: tags["venue"] = recipient

        elif direction_info["direction"] == "venue_to_executing_bd":
            if agent: tags["venue"] = agent
            if recipient: tags["executing_bd"] = recipient

    # 4. Fallback metric inference from context
    if not tags.get("metric"):
        if "order" in text or "orders" in text:
            tags["metric"] = "volume"
        elif "pfof" in text or "payment" in text or "rebate" in text:
            tags["metric"] = "pfof"
        elif "rate" in text or "cents per" in text:
            tags["metric"] = "rate"

    # 5. Direction fallback (based on metric)
    if not tags.get("direction"):
        if tags.get("metric") == "pfof":
            tags["direction"] = "venue_to_executing_bd"
        else:
            tags["direction"] = "executing_bd_to_venue"

    # 5b. Entity assignment fallback - if entities were captured but direction wasn't set yet
    if (agent or recipient) and not tags.get("executing_bd") and not tags.get("venue"):
        if tags.get("direction") == "executing_bd_to_venue":
            if agent: tags["executing_bd"] = agent
            if recipient: tags["venue"] = recipient
        elif tags.get("direction") == "venue_to_executing_bd":
            if agent: tags["venue"] = agent
            if recipient: tags["executing_bd"] = recipient

    # 6. Time extraction
    time_info = extract_time_period(user_input)

    if time_info["year"]:
        tags["year"] = time_info["year"]
    if time_info["month"]:
        tags["month"] = time_info["month"]
    if time_info["quarter"]:
        tags["quarter"] = time_info["quarter"]

    # Update boolean flags based on extracted year/month
    if tags.get("year"): tags["mentions_year"] = True
    if tags.get("month"): tags["mentions_month"] = True
    if tags.get("quarter"): tags["mentions_quarter"] = True

    return tags

# -----------------------------
# Enhanced Query Classification
# -----------------------------

def classify_query_enhanced(user_input: str) -> Dict:
    """Enhanced query classification with table routing and NLP refinement"""
    text = user_input.lower()

    # Initial keyword-based tagging
    tags = {
        "mentions_volume": any(k in text for k in [
            "volume", "number of shares", "shares traded", "number of trades"
        ]),
        "mentions_pfof": (
            "pfof" in text or
            "payment for order flow" in text or
            ("payment" in text and ("broker" in text or "brokers" in text)) or
            ("paid" in text and ("broker" in text or "brokers" in text)) or
            ("revenue" in text and ("broker" in text or "brokers" in text)) or
            ("payment received" in text)
        ),
        "mentions_order_type": "order type" in text or "stock group" in text,
        "ambiguous_paid": "who paid" in text,
        "mentions_rate": any(k in text for k in ["rate", "cents per", "per share", "cph"]),
        "mentions_cph": ("cph" in text),
        "mentions_max": any(k in text for k in ["highest", "maximum"]),
        "mentions_zero_pfof": any(k in text for k in ["not paid", "no pfof", "zero flow", "received no"]),
        "mentions_month": any(k in text for k in ["month", "monthly", "last month", "this month"]),
        "mentions_year": any(k in text for k in ["year", "annual", "this year", "last year", "yoy"]),
        "mentions_quarter": any(k in text for k in ["quarter", "q1", "q2", "q3", "q4"]),
        "mentions_broker": any(k in text for k in ["broker", "bd", "routing broker", "retail broker", "orders routed"]),
        "mentions_venue": any(k in text for k in ["venue", "exchange", "market center", "market maker","wholesaler","executing broker"]),
        "mentions_trend": (
            any(k in text for k in ["trend", "compare", "change over", "increase", "decrease"])
            or ("was that month also" in text) or ("also the largest" in text)
        ),
        "mentions_ats": any(k in text for k in ["ats", "alternative trading system", "finra","dark pool","ATS"]),
        "mentions_tape": any(k in text for k in ["tape a", "tape b", "tape c", "tape","NYSE-listed","NASDAQ-listed","AMEX-listed","ETFs","ETNs","stocks"]),
        "mentions_market_share": any(k in text for k in ["market share", "percentage share", "share of market", "percent share", "share %", "share pct", "share percentage"]),
        "mentions_entity_type": any(k in text for k in ["entity type", "exchange", "market maker", "organization"]),
        "mentions_streak": any(k in text for k in ["streak", "consecutive", "longest run", "longest streak"]),
        "mentions_longest": any(k in text for k in ["longest", "max", "record"]),
        "mentions_first": any(k in text for k in ["first", "earliest", "beginning", "start"]),
        "mentions_orders": any(k in text for k in ["order", "orders", "got the most orders", "most orders", "received the most orders"]),
        
        # Default None, filled by logic or NLP
        "year": None,
        "month": None,
        "quarter": None,
        "executing_bd": None,
        "venue": None,
        "stock_group": None,
    }

    # Detect stock_group from keywords
    text_lower = user_input.lower()
    if any(k in user_input.upper() for k in ["SP500", "S&P 500", "S&P500"]):
        tags["stock_group"] = "SP500"
    elif "option" in text_lower:
        tags["stock_group"] = "Options"
    elif "other stock" in text_lower or "otherstocks" in text_lower:
        tags["stock_group"] = "OtherStocks"

    # Basic Regex Year Extraction (Fallback if NLP fails)
    match_year = re.search(r"\b(20[0-9]{2})\b", user_input)
    if match_year:
        tags["year"] = int(match_year.group(1))

    # Basic Month Name Extraction (Fallback if NLP is unavailable)
    for m_name, m_num in MONTHS_MAP.items():
        if m_name in text:
            tags["month"] = m_num
            tags["mentions_month"] = True
            break

    # Attempt to resolve venue from DB Alias
    try:
        resolved_venue = resolve_venue(user_input)
        if resolved_venue:
            tags["venue"] = resolved_venue
    except Exception:
        pass

    # Attempt to resolve executing_bd from broker aliases
    try:
        broker_aliases = load_broker_aliases()
        if broker_aliases and "executing_bd_map" in broker_aliases:
            resolved_broker = resolve_executing_bd(user_input, broker_aliases["executing_bd_map"])
            if resolved_broker:
                tags["executing_bd"] = resolved_broker
    except Exception:
        pass

    # --- INTEGRATION POINT: Apply NLP Refinement ---
    if NLP_MODEL:
        tags = disambiguate_context(user_input, tags)

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
    
    # monthly_data-specific rules to avoid GROUP BY errors on 'day'
    if 'monthly_data' in relevant_tables:
        rules.extend([
            "For monthly_data, do not select raw 'day' unless you GROUP BY it.",
            "For month-level trends: SELECT EXTRACT(MONTH FROM day) AS month and GROUP BY EXTRACT(MONTH FROM day).",
            "For quarter-level trends: SELECT EXTRACT(QUARTER FROM day) AS quarter and GROUP BY EXTRACT(QUARTER FROM day).",
            "For year-level trends: SELECT EXTRACT(YEAR FROM day) AS year and GROUP BY EXTRACT(YEAR FROM day).",
            "Prefer COUNT(DISTINCT day) for trading day counts; avoid selecting 'day' with aggregates.",
        ])

    # Market share-specific guidance
    if query_tags.get('mentions_market_share') and 'monthly_data' in relevant_tables:
        rules.extend([
            "For market share, compute entity_shares / total_shares within the same period (month/quarter/year).",
            "Use EXTRACT(QUARTER FROM day) or EXTRACT(MONTH FROM day) to bucket time, then rank share_pct.",
            "If tapes are mentioned, use tape_a_shares + tape_b_shares + tape_c_shares; otherwise total_shares.",
            "Filter out TRF/FINRA if the question is about exchanges only.",
        ])

    # CPH-specific guidance
    if query_tags.get('mentions_cph') or query_tags.get('mentions_rate'):
        rules.extend([
            "For CPH questions, use *_cph columns (marketorderscph, marketablelimitorderscph, nonmarketablelimitorderscph, otherorderscph).",
            "When ranking by highest CPH overall, compute GREATEST(...) across the *_cph columns per broker.",
            "Group and rank within stock_group and specified time filters (year/month).",
        ])
    
    # NLP-Derived Specificity
    if query_tags.get('executing_bd'):
        rules.append(f"Filter specifically for broker: executing_bd = '{query_tags['executing_bd']}'")
    
    if query_tags.get('venue'):
        rules.append(f"Filter specifically for venue: venues = '{query_tags['venue']}'")

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
        if 'executing_bd_606' in relevant_tables and query_tags.get('mentions_pfof'):
            rules.append("Only estimate volume from executing_bd_606 when explicitly asked; otherwise use PFOF USD totals.")
            rules.append("For executing_bd_606 volume estimation: volume = (usd / cph) * 100")
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
        
        # Inject specific time filters if NLP found them
        if query_tags.get('year'):
            rules.append(f"Filter by year = {query_tags['year']}")
        if query_tags.get('month'):
            rules.append(f"Filter by month = '{query_tags['month']}'")
        if query_tags.get('quarter'):
             rules.append(f"Filter by quarter explicitly if column exists, or months {((query_tags['quarter']-1)*3)+1}-{query_tags['quarter']*3}")

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
# Volume Estimation
# -----------------------------

def generate_volume_estimation_query(user_input: str, query_tags: Dict) -> str:
    """Generate volume estimation query based on user input and classification"""
    
    # Extract parameters from query tags
    year = query_tags.get('year', 2024)
    stock_group = query_tags.get('stock_group', 'SP500')
    
    # Use NLP derived entities if available, else fallbacks
    venue = query_tags.get('venue')
    executing_bd = query_tags.get('executing_bd')
    
    # Fallback logic if NLP didn't catch them but tags exist
    query_by_venue = query_tags.get('mentions_venue', False)
    
    if not venue and not executing_bd:
         # Simple venue/broker extraction (can be enhanced)
        if query_by_venue:
            # Look for venue names in the input
            venue_keywords = ['citadel', 'cboe', 'nasdaq', 'nyse', 'bats', 'iex']
            for keyword in venue_keywords:
                if keyword.lower() in user_input.lower():
                    venue = keyword.upper() 
                    break
        else:
            # Look for broker names
            broker_keywords = ['robinhood', 'schwab', 'fidelity', 'etrade']
            for keyword in broker_keywords:
                if keyword.lower() in user_input.lower():
                    executing_bd = keyword.upper()
                    break
    
    return generate_volume_estimation_query_detailed(
        year=year,
        stock_group=stock_group,
        executing_bd=executing_bd,
        venue=venue,
        query_by_venue=bool(venue) or query_by_venue
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
# SQL Sanitization
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
# Venue Resolution
# -----------------------------

def resolve_venue_from_db(user_input: str) -> Optional[str]:
    """Resolve venue alias to canonical name from database"""
    try:
        import psycopg2
        from dotenv import load_dotenv

        load_dotenv()

        # Skip if query contains generic "each venue/venues" or similar phrases
        text = user_input.lower()
        if re.search(r'\beach\s+(venue|venues|exchange|market)\b|\b(venue|venues|exchange|market)s?\s+each\b|\bper\s+(venue|venues|exchange|market)\b|\bby\s+(venue|venues|exchange|market)\b', text):
            return None

        # Skip top-per-group queries like "top venue per broker"
        if re.search(r'\btop\b.*\b(venue|venues)\b.*\bper\b', text):
            return None

        # Skip queries grouping by broker/executing (e.g., "PFOF by broker", "volume by executing bd")
        if re.search(r'\bby\s+(broker|brokers?|executing)', text):
            return None

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", 5432),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        cursor = conn.cursor()

        # Fetch all venue aliases from database
        cursor.execute(
            "SELECT canonical_name, aliases FROM venue_mapping"
        )
        venue_mappings = cursor.fetchall()

        text = user_input.lower()

        # Skip generic words that shouldn't trigger venue matching
        generic_words = {'each', 'broker', 'brokers', 'venue', 'venues', 'exchange',
                        'market', 'volume', 'pfof', 'estimated', 'options', 'option',
                        'stocks', 'stock', 'shares', 'share', 'tape', 'top', 'per',
                        'highest', 'lowest', 'most', 'least', 'compare', 'and', 'by',
                        'for', 'in', 'the', 'a', 'an', 'is', 'are', 'was', 'were',
                        'total', 'sum', 'count', 'avg', 'average'}

        # Try to match aliases using word boundaries (most specific first)
        for canonical_name, aliases_json in venue_mappings:
            try:
                import json
                aliases = json.loads(aliases_json) if aliases_json else []
            except:
                continue

            for alias in aliases:
                alias_lower = alias.lower().strip()

                # Skip single-word aliases that are generic terms
                if ' ' not in alias_lower and alias_lower in generic_words:
                    continue

                # Skip very short aliases (< 3 chars) to avoid false positives
                if len(alias_lower) < 3:
                    continue

                # Use word boundaries for precise matching
                # Match "citadel" but not "cit" in "citadel"
                # Match "israel englander" as a phrase
                pattern = r'\b' + re.escape(alias_lower) + r'\b'
                if re.search(pattern, text):
                    cursor.close()
                    conn.close()
                    return canonical_name

        cursor.close()
        conn.close()
        return None

    except Exception as e:
        # print(f"Error resolving venue: {e}")
        return None

def resolve_venue(user_input: str) -> Optional[str]:
    """Resolve venue alias to canonical name"""
    return resolve_venue_from_db(user_input)

# -----------------------------
# Broker Resolution
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
    """Resolve executing broker alias to canonical name using word boundary matching"""
    import re
    text = user_input.lower()

    # Skip if query contains generic "each broker/brokers" phrases
    if re.search(r'\beach\s+brokers?\b|\bbrokers?\s+each\b|\bper\s+brokers?\b|\bby\s+brokers?\b', text):
        return None

    # Match aliases with word boundaries to avoid partial matches
    for canonical_name, aliases in alias_map.items():
        for alias in aliases:
            # Use word boundaries for more precise matching
            # \b ensures we match whole words/phrases
            pattern = r'\b' + re.escape(alias.lower()) + r'\b'
            if re.search(pattern, text):
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