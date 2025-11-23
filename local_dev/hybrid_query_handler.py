# hybrid_query_handler.py

import os
import re
import json
from typing import List, Dict, Optional, Tuple
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
try:
    import parsedatetime as pdt
    CAL = pdt.Calendar()
except Exception:
    pdt = None
    CAL = None

# Optional LangChain NL2SQL adapter (semantic hints only)
try:
    from semantic_sql_adapter import (
        get_sql_hint as _get_sql_hint,
        build_intent_from_user_input as _build_intent,
        build_final_sql as _build_final_sql,
    )
except Exception:
    _get_sql_hint = lambda q, i: None  # type: ignore
    _build_intent = lambda q, t: type("_I", (), {"__dict__": {}})  # dummy intent
    _build_final_sql = lambda i, h=None: None
from handlers.executing_bd_606_handler import generate_top_pfof_broker_per_quarter_query
from handlers.monthly_data_handler import generate_top_exchange_share_per_quarter_query
from handlers.finra_ats_handler import generate_top_ats_shares_per_quarter_query
from planner import plan_single_sql

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Connect to the database
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT", 5432),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
conn.autocommit = True
cursor = conn.cursor()

# -----------------------------
# Two-Table Query Handlers
# -----------------------------

# Handler 1: executing_bd_606 + monthly_data (time-based volume)
# Handler 2: executing_bd_606 + finra_ats (broker-specific ATS analysis)

def generate_time_based_volume_query(user_input: str, query_tags: Dict) -> Tuple[str, str]:
    """
    Generate two-table query for time-based volume analysis.
    Returns: (main_query, context_query)
    """
    
    # Extract time parameters
    year = query_tags.get('year', 2024)
    month = query_tags.get('month')
    
    # Build WHERE conditions for main query (executing_bd_606)
    where_conditions = [
        f"year = {year}",
        "data_type = 'venue'",
        "venues IS NOT NULL",
        "venues != ''"
    ]
    
    if month:
        where_conditions.append(f"month = '{month}'")
    
    # Main query: Get venue volume from executing_bd_606
    main_query = f"""
    SELECT 
        venues,
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
    WHERE {' AND '.join(where_conditions)}
    GROUP BY venues
    ORDER BY estimated_volume DESC
    LIMIT 1;
    """
    
    # Context query: Get market data from monthly_data
    month_name = get_month_name(month) if month else None
    context_query = f"""
    WITH finra_data AS (
        SELECT 
            SUM(total_shares) as finra_total_shares
        FROM monthly_data
        WHERE EXTRACT(YEAR FROM day) = {year}
        {'AND EXTRACT(MONTH FROM day) = ' + str(month) if month else ''}
        AND market_participant LIKE '%FINRA%'
    ),
    total_market AS (
        SELECT 
            SUM(total_shares) as total_market_shares
        FROM monthly_data
        WHERE EXTRACT(YEAR FROM day) = {year}
        {'AND EXTRACT(MONTH FROM day) = ' + str(month) if month else ''}
    )
    SELECT 
        finra_data.finra_total_shares,
        total_market.total_market_shares,
        CASE 
            WHEN total_market.total_market_shares > 0 
            THEN ROUND((finra_data.finra_total_shares::numeric / total_market.total_market_shares::numeric) * 100, 2)
            ELSE 0
        END as finra_market_share_pct
    FROM finra_data, total_market;
    """
    
    return main_query.strip(), context_query.strip()

def get_month_name(month_num: int) -> str:
    """Convert month number to month name"""
    months = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }
    return months.get(month_num, "")

def execute_time_based_volume_query(user_input: str, query_tags: Dict) -> Dict:
    """Execute the two-table time-based volume query"""
    
    print("🔗 Two-table query detected - executing_bd_606 + monthly_data")
    
    # Generate queries
    main_query, context_query = generate_time_based_volume_query(user_input, query_tags)
    
    print(f"Main Query: \n{main_query}")
    print(f"Context Query: \n{context_query}")
    
    try:
        # Execute main query
        cursor.execute(main_query)
        main_results = cursor.fetchall()
        main_columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Execute context query
        cursor.execute(context_query)
        context_results = cursor.fetchall()
        context_columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Format results
        main_data = []
        if main_results:
            for row in main_results:
                main_data.append(dict(zip(main_columns, row)))
        
        context_data = []
        if context_results:
            for row in context_results:
                context_data.append(dict(zip(context_columns, row)))
        
        # Generate response
        response = generate_time_based_response(user_input, main_data, context_data, query_tags)
        
        return {
            "question": user_input,
            "query_type": "two_table_time_based",
            "main_query": main_query,
            "context_query": context_query,
            "main_results": main_data,
            "context_results": context_data,
            "response": response,
            "query_classification": query_tags
        }
        
    except Exception as e:
        return {
            "question": user_input,
            "query_type": "two_table_time_based",
            "main_query": main_query,
            "context_query": context_query,
            "error": str(e),
            "query_classification": query_tags
        }

def generate_time_based_response(user_input: str, main_data: List[Dict], context_data: List[Dict], query_tags: Dict) -> str:
    """Generate natural language response for time-based volume query"""
    
    if not main_data:
        return "No venue data found for the specified time period."
    
    # Extract time information
    year = query_tags.get('year', 2024)
    month = query_tags.get('month')
    month_name = get_month_name(month) if month else ""
    
    # Get top venue
    top_venue = main_data[0]
    venue_name = top_venue.get('venues', 'Unknown')
    estimated_volume = top_venue.get('estimated_volume', 0)
    total_usd = top_venue.get('total_usd', 0)
    
    # Get market context
    finra_total = 0
    total_market = 0
    finra_share_pct = 0
    
    if context_data:
        context = context_data[0]
        finra_total = context.get('finra_total_shares', 0)
        total_market = context.get('total_market_shares', 0)
        finra_share_pct = context.get('finra_market_share_pct', 0)
    
    # Format numbers
    finra_total_formatted = f"{finra_total:,}" if finra_total else "0"
    total_market_formatted = f"{total_market:,}" if total_market else "0"
    total_usd_formatted = f"${total_usd:,.2f}" if total_usd else "$0"
    
    # Build response
    time_period = f"{month_name} {year}" if month_name else f"{year}"
    
    response = f"""In {time_period}, {venue_name} was the venue that received the most volume from brokers.

**Volume Analysis:**
- Estimated Volume: {estimated_volume:,.0f} shares
- Total PFOF Payments: {total_usd_formatted}

**Market Context:**
For context, off-exchange volume that month was {finra_total_formatted} shares, representing {finra_share_pct:.1f}% of all shares traded ({total_market_formatted} total shares)."""
    
    return response

# (Removed Virtu-specific handler; ATS analysis handled generically in complex path)

# -----------------------------
# Complex Multi-Table Query Handler (Separate Queries + OpenAI Synthesis)
# -----------------------------

def _is_direct_pfof_broker_venues_query(user_input: str, query_tags: Dict) -> bool:
    """
    Detect a direct, single-shot query: Broker PFOF by venue for a specific time.
    Examples:
      - 'How much did Robinhood receive in PFOF from each of its venues in Jan 2024'
    Requirements:
      - mentions_pfof true
      - executing_bd resolved
      - month and/or year present
      - phrase indicating venue breakdown (e.g., 'each of its venues', 'by venue', 'from each venue')
    """
    if not query_tags.get('mentions_pfof'):
        return False
    if not query_tags.get('executing_bd'):
        return False
    if not (query_tags.get('month') or query_tags.get('year')):
        return False
    text = (user_input or "").lower()
    venue_breakdown = any(
        p in text for p in [
            "each of its venues", "each venue", "by venue", "from each venue", "from each of its venues"
        ]
    )
    return venue_breakdown


def execute_direct_pfof_by_venue_for_broker(user_input: str, query_tags: Dict) -> Dict:
    """
    Single deterministic query answering:
      PFOF totals per venue for a specific executing_bd within a time filter (month/year).
    No extras; no synthesis. Returns only the direct answer.
    """
    broker = query_tags.get('executing_bd')
    year = query_tags.get('year')
    month = query_tags.get('month')

    where_conditions = ["data_type = 'venue'"]
    if broker:
        # Escape single quotes in broker name minimally
        safe_broker = str(broker).replace("'", "''")
        where_conditions.append(f"executing_bd = '{safe_broker}'")
    if year:
        where_conditions.append(f"year = {int(year)}")
    if month:
        where_conditions.append(f"month = '{int(month)}'")

    sql = f"""
    SELECT
        venues,
        SUM(
          COALESCE(netpmtpaidrecvmarketordersusd, 0) +
          COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
          COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
          COALESCE(netpmtpaidrecvotherordersusd, 0)
        ) AS total_pfof_usd
    FROM executing_bd_606
    WHERE {' AND '.join(where_conditions)}
    GROUP BY venues
    ORDER BY total_pfof_usd DESC;
    """.strip()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description] if cursor.description else []
        formatted = [dict(zip(cols, r)) for r in rows] if rows else []
        return {
            "question": user_input,
            "query_type": "direct_single",
            "sql": sql,
            "results": formatted,
            "row_count": len(formatted),
            "query_classification": query_tags
        }
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return {
            "question": user_input,
            "query_type": "direct_single",
            "sql": sql,
            "error": str(e),
            "query_classification": query_tags
        }


def _is_list_unique_query(user_input: str, query_tags: Dict) -> bool:
    """
    Detect simple list/unique queries that can be answered with DISTINCT on a single column.
    Examples:
      - 'list all the unique executing brokers for January 2024'
      - 'show distinct venues in 2024'
    """
    text = (user_input or "").lower()
    has_list_word = any(w in text for w in ["list", "show", "display"])
    has_unique_word = any(w in text for w in ["unique", "distinct", "all"])
    mentions_target = any(w in text for w in ["executing broker", "executing brokers", "brokers", "venues", "venue"])
    return has_list_word and has_unique_word and mentions_target


def execute_direct_list_query(user_input: str, query_tags: Dict) -> Dict:
    """
    Single deterministic DISTINCT query for one column (executing_bd or venues) on executing_bd_606.
    Applies optional time filters (year/month). No extras; no synthesis.
    """
    text = (user_input or "").lower()
    # Choose target column
    if any(w in text for w in ["executing broker", "executing brokers", "brokers"]):
        target_col = "executing_bd"
    elif any(w in text for w in ["venues", "venue"]):
        target_col = "venues"
    else:
        # Default to executing_bd if not explicit
        target_col = "executing_bd"

    year = query_tags.get('year')
    month = query_tags.get('month')

    where_conditions = ["data_type = 'venue'"]
    if year:
        where_conditions.append(f"year = {int(year)}")
    if month:
        where_conditions.append(f"month = '{int(month)}'")
    # Filter out null/empty values
    where_conditions.extend([f"{target_col} IS NOT NULL", f"{target_col} != ''"])

    sql = f"""
    SELECT DISTINCT {target_col}
    FROM executing_bd_606
    WHERE {' AND '.join(where_conditions)}
    ORDER BY {target_col};
    """.strip()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description] if cursor.description else []
        formatted = [dict(zip(cols, r)) for r in rows] if rows else []
        return {
            "question": user_input,
            "query_type": "direct_single",
            "sql": sql,
            "results": formatted,
            "row_count": len(formatted),
            "query_classification": query_tags
        }
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return {
            "question": user_input,
            "query_type": "direct_single",
            "sql": sql,
            "error": str(e),
            "query_classification": query_tags
        }


def generate_complex_multi_table_query(user_input: str, query_tags: Dict) -> Dict:
    """Generate complex multi-table query using separate queries + OpenAI synthesis"""
    
    print("🔗 Complex multi-table query detected - using separate queries + OpenAI synthesis")
    # Enrich time tags using parsedatetime if available
    query_tags = _enrich_time_with_parsedatetime(user_input, query_tags)
    
    # Special flow: venue + orders -> top venue by orders in executing_bd_606, then ATS volume
    text = user_input.lower()
    if query_tags.get('mentions_venue') and (query_tags.get('mentions_orders') or 'order' in text or 'orders' in text):
        return execute_orders_venue_then_ats(user_input, query_tags)

    # Determine which tables to query based on classification
    queries_to_execute = []
    
    # Always query executing_bd_606 for PFOF data
    if query_tags.get('mentions_pfof') or query_tags.get('mentions_volume'):
        queries_to_execute.append({
            'name': 'pfof_data',
            'description': 'PFOF payment data from executing_bd_606',
            'query': generate_pfof_query(query_tags)
        })
    
    # Query monthly_data for market context (include quarter/year-driven cases)
    if query_tags.get('mentions_trend') or query_tags.get('mentions_month') or query_tags.get('mentions_quarter'):
        queries_to_execute.append({
            'name': 'market_data',
            'description': 'Market volume data from monthly_data',
            'query': generate_market_data_query(query_tags)
        })

    # Quarter-based PFOF top broker
    if query_tags.get('mentions_pfof') and (query_tags.get('mentions_quarter') or query_tags.get('year')):
        queries_to_execute.append({
            'name': 'pfof_by_quarter',
            'description': 'Top broker by total PFOF per quarter from executing_bd_606',
            'query': generate_top_pfof_broker_per_quarter_query(query_tags)
        })

    # Exchange with largest market share per quarter
    if query_tags.get('mentions_market_share') and (query_tags.get('mentions_quarter') or query_tags.get('year')):
        queries_to_execute.append({
            'name': 'exchange_share_by_quarter',
            'description': 'Exchange with largest market share per quarter from monthly_data',
            'query': generate_top_exchange_share_per_quarter_query(query_tags)
        })

    # ATS with highest share volume per quarter
    if query_tags.get('mentions_ats') and (query_tags.get('mentions_quarter') or query_tags.get('year')):
        queries_to_execute.append({
            'name': 'ats_top_by_quarter',
            'description': 'ATS with highest share volume per quarter from finra_ats',
            'query': generate_top_ats_shares_per_quarter_query(query_tags)
        })
    
    # Query finra_ats for ATS data
    if query_tags.get('mentions_ats'):
        queries_to_execute.append({
            'name': 'ats_data',
            'description': 'ATS trading data from finra_ats',
            'query': generate_ats_query(query_tags)
        })

    # Query for top CPH brokers per stock group (year/month aware)
    if query_tags.get('mentions_cph') or (query_tags.get('mentions_rate') and query_tags.get('mentions_broker')):
        queries_to_execute.append({
            'name': 'cph_data',
            'description': 'Top brokers by CPH per stock group from executing_bd_606',
            'query': generate_top_cph_brokers_query(query_tags)
        })

    # Query for top PFOF broker per stock group (when user mentions stock group)
    if query_tags.get('mentions_pfof') and (query_tags.get('mentions_order_type') or 'stock group' in user_input.lower()):
        queries_to_execute.append({
            'name': 'pfof_by_stock_group',
            'description': 'Top broker by total PFOF per stock group from executing_bd_606',
            'query': generate_top_pfof_broker_per_stock_group_query(query_tags)
        })

    # Query for top PFOF broker per order type (market, marketable limit, nonmarketable limit, other)
    if query_tags.get('mentions_pfof') and query_tags.get('mentions_order_type'):
        queries_to_execute.append({
            'name': 'pfof_by_order_type',
            'description': 'Top broker by total PFOF per order type from executing_bd_606',
            'query': generate_top_pfof_broker_per_order_type_query(query_tags)
        })

    # Earliest PFOF month queries
    if query_tags.get('mentions_pfof') and query_tags.get('mentions_first'):
        queries_to_execute.append({
            'name': 'earliest_pfof_month',
            'description': 'Earliest month/year with PFOF > 0',
            'query': generate_earliest_pfof_month_query()
        })
        queries_to_execute.append({
            'name': 'earliest_pfof_by_broker',
            'description': 'Earliest month/year with PFOF > 0 per broker',
            'query': generate_earliest_pfof_by_broker_query()
        })
    
    # Longest streak of routing broker→venue
    if query_tags.get('mentions_streak') and (query_tags.get('mentions_broker') or query_tags.get('mentions_venue') or True):
        queries_to_execute.append({
            'name': 'streak_data',
            'description': 'Longest consecutive month streak with PFOF > 0 per broker→venue pair',
            'query': generate_longest_broker_venue_streak_query()
        })

    # Query entity_types for venue classifications
    if query_tags.get('mentions_venue') or query_tags.get('mentions_entity_type'):
        queries_to_execute.append({
            'name': 'entity_data',
            'description': 'Venue type classifications from entity_types',
            'query': generate_entity_query(query_tags)
        })
    
    # Execute all queries
    query_results = {}
    for query_info in queries_to_execute:
        try:
            cursor.execute(query_info['query'])
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append(dict(zip(columns, row)))
            
            query_results[query_info['name']] = {
                'description': query_info['description'],
                'query': query_info['query'],
                'results': formatted_results,
                'row_count': len(formatted_results)
            }
            
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            query_results[query_info['name']] = {
                'description': query_info['description'],
                'query': query_info['query'],
                'error': str(e),
                'row_count': 0
            }
    
    # Generate OpenAI synthesis
    synthesis = generate_openai_synthesis(user_input, query_results, query_tags)

    # Attach optional semantic NL2SQL hint (readout only by default)
    try:
        show_hints = (os.getenv("SHOW_SEMANTIC_HINTS", "false").lower() == "true")
        use_hints = (os.getenv("USE_SEMANTIC_HINTS", "false").lower() == "true")
        if show_hints or use_hints:
            intent = _build_intent(user_input, dict(query_tags))
            hint_sql = _get_sql_hint(user_input, intent)
            final_hint_sql = _build_final_sql(intent, hint_sql) if hint_sql else None
            query_results["semantic_nl2sql"] = {
                "used": use_hints,
                "hint": hint_sql,
                "final_sql": final_hint_sql,
            }
    except Exception:
        pass
    
    return {
        "question": user_input,
        "query_type": "complex_multi_table",
        "query_results": query_results,
        "synthesis": synthesis,
        "query_classification": query_tags
    }

def execute_orders_venue_then_ats(user_input: str, query_tags: Dict) -> Dict:
    """Flow: find top venue by orders (estimated volume) and then its ATS total shares."""
    year = query_tags.get('year', 2024)
    month = query_tags.get('month')

    # Step 1: Top venue by orders (estimated from PFOF USD and CPH)
    where_conditions = [
        f"year = {year}",
        "data_type = 'venue'",
        "venues IS NOT NULL",
        "venues != ''"
    ]
    if month:
        where_conditions.append(f"month = '{month}'")

    top_venue_sql = f"""
    SELECT 
        venues,
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
        END as estimated_orders
    FROM executing_bd_606
    WHERE {' AND '.join(where_conditions)}
    GROUP BY venues
    ORDER BY estimated_orders DESC
    LIMIT 1;
    """

    cursor.execute(top_venue_sql)
    top_rows = cursor.fetchall()
    top_cols = [desc[0] for desc in cursor.description] if cursor.description else []
    top_results = [dict(zip(top_cols, r)) for r in top_rows]

    selected_venue = top_results[0]['venues'] if top_results else None

    # Step 2: ATS total shares for that venue (year or quarter if month given)
    ats_where = [f"year = {year}"]
    if month:
        q = 1 if month in [1,2,3] else 2 if month in [4,5,6] else 3 if month in [7,8,9] else 4
        ats_where.append(f"quarter = '{q}'")

    if selected_venue:
        patterns = _ats_patterns_for_venue(selected_venue)
        if patterns:
            like_clauses = [f"ats_name ILIKE '{p}'" for p in patterns]
            ats_where.append("(" + " OR ".join(like_clauses) + ")")

    ats_sql = f"""
    SELECT 
        SUM(total_shares) AS ats_total_shares,
        SUM(total_trades) AS ats_total_trades
    FROM finra_ats
    WHERE {' AND '.join(ats_where)};
    """

    cursor.execute(ats_sql)
    ats_rows = cursor.fetchall()
    ats_cols = [desc[0] for desc in cursor.description] if cursor.description else []
    ats_results = [dict(zip(ats_cols, r)) for r in ats_rows]

    # Compose result similar to complex path
    query_results = {
        'top_venue_orders': {
            'description': 'Top venue by estimated orders from executing_bd_606',
            'query': top_venue_sql,
            'results': top_results,
            'row_count': len(top_results),
        },
        'ats_volume': {
            'description': 'ATS totals for matched venue',
            'query': ats_sql,
            'results': ats_results,
            'row_count': len(ats_results),
        }
    }

    synthesis = generate_openai_synthesis(user_input, query_results, query_tags)

    return {
        "question": user_input,
        "query_type": "complex_multi_table",
        "query_results": query_results,
        "synthesis": synthesis,
        "query_classification": query_tags
    }

def generate_pfof_query(query_tags: Dict) -> str:
    """Generate PFOF query.
    If asking for the largest month, aggregate *_usd by month and return the top month.
    Otherwise, return top entities by total PFOF.
    """
    where_conditions = ["data_type = 'venue'"]
    
    if query_tags.get('year'):
        where_conditions.append(f"year = {query_tags['year']}")
    
    if query_tags.get('month'):
        where_conditions.append(f"month = '{query_tags['month']}'")
    
    # If the user asks about orders/volume and a max-month context, estimate orders per month
    if (query_tags.get('mentions_orders') or query_tags.get('mentions_volume')) and query_tags.get('mentions_max') and (query_tags.get('mentions_month') or query_tags.get('year')):
        return f"""
        SELECT 
            month,
            CASE 
                WHEN AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) +
                         COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) +
                         COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) +
                         COALESCE(netpmtpaidrecvotherorderscph, 0)) > 0
                THEN ROUND((
                    SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) +
                        COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
                        COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
                        COALESCE(netpmtpaidrecvotherordersusd, 0))
                    /
                    AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) +
                        COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) +
                        COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) +
                        COALESCE(netpmtpaidrecvotherorderscph, 0))
                ) * 100, 2)
                ELSE 0
            END as estimated_orders
        FROM executing_bd_606
        WHERE {' AND '.join(where_conditions)}
        GROUP BY month
        ORDER BY estimated_orders DESC
        LIMIT 1;
        """

    if query_tags.get('mentions_max') and (query_tags.get('mentions_month') or query_tags.get('year')):
        return f"""
        SELECT 
            month,
            SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) +
                COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
                COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
                COALESCE(netpmtpaidrecvotherordersusd, 0)) as total_pfof_usd
        FROM executing_bd_606
        WHERE {' AND '.join(where_conditions)}
        GROUP BY month
        ORDER BY total_pfof_usd DESC
        LIMIT 1;
        """
    
    return f"""
    SELECT 
        executing_bd,
        venues,
        SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) +
            COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
            COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
            COALESCE(netpmtpaidrecvotherordersusd, 0)) as total_pfof_usd,
        AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) +
            COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) +
            COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) +
            COALESCE(netpmtpaidrecvotherorderscph, 0)) as avg_cph
    FROM executing_bd_606
    WHERE {' AND '.join(where_conditions)}
    GROUP BY executing_bd, venues
    ORDER BY total_pfof_usd DESC
    LIMIT 10;
    """

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

def generate_market_data_query(query_tags: Dict) -> str:
    """Generate market data query.
    Quarter-aware when requested; otherwise months or top participants.
    """
    where_conditions = []
    
    if query_tags.get('year'):
        where_conditions.append(f"EXTRACT(YEAR FROM day) = {query_tags['year']}")
    
    if query_tags.get('month'):
        where_conditions.append(f"EXTRACT(MONTH FROM day) = {query_tags['month']}")
    
    if query_tags.get('quarter'):
        where_conditions.append(f"EXTRACT(QUARTER FROM day) = {query_tags['quarter']}")
    
    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
    
    # Quarter-based aggregations
    if query_tags.get('mentions_quarter') or query_tags.get('quarter'):
        if query_tags.get('quarter'):
            # Return total market volume for the specific quarter
            return f"""
            SELECT 
                SUM(total_shares) AS total_market_shares,
                SUM(total_notional) AS total_market_notional,
                SUM(total_trade_count) AS total_trades
            FROM monthly_data
            {where_clause};
            """
        else:
            # Aggregate by quarter if quarter not explicitly parsed
            return f"""
            SELECT 
                EXTRACT(QUARTER FROM day) AS quarter,
                SUM(total_shares) AS total_shares,
                SUM(total_notional) AS total_notional,
                SUM(total_trade_count) AS total_trades
            FROM monthly_data
            {where_clause}
            GROUP BY EXTRACT(QUARTER FROM day)
            ORDER BY quarter;
            """
    
    # Largest month in a period
    if query_tags.get('mentions_max') and (query_tags.get('mentions_month') or query_tags.get('year')):
        return f"""
        SELECT 
            EXTRACT(MONTH FROM day) AS month,
            SUM(total_shares) AS total_shares
        FROM monthly_data
        {where_clause}
        GROUP BY EXTRACT(MONTH FROM day)
        ORDER BY total_shares DESC
        LIMIT 1;
        """
    
    # Default: top market participants
    return f"""
    SELECT 
        market_participant,
        SUM(total_shares) as total_shares,
        SUM(total_notional) as total_notional,
        SUM(total_trade_count) as total_trades,
        COUNT(DISTINCT day) as trading_days
    FROM monthly_data
    {where_clause}
    GROUP BY market_participant
    ORDER BY total_shares DESC
    LIMIT 10;
    """

def generate_ats_query(query_tags: Dict) -> str:
    """Generate ATS query"""
    where_conditions = []
    
    if query_tags.get('year'):
        where_conditions.append(f"year = {query_tags['year']}")
    
    if query_tags.get('mentions_quarter'):
        # Extract quarter from query tags if available
        pass
    
    # If a specific venue was resolved, constrain ats_name with generic patterns
    venue = query_tags.get('venue')
    if venue:
        patterns = _ats_patterns_for_venue(venue)
        if patterns:
            like_clauses = [f"ats_name ILIKE '{p}'" for p in patterns]
            where_conditions.append("(" + " OR ".join(like_clauses) + ")")

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
    
    return f"""
    SELECT 
        ats_name,
        tier,
        SUM(total_trades) as total_trades,
        SUM(total_shares) as total_shares,
        COUNT(DISTINCT quarter) as quarters_active
    FROM finra_ats
    {where_clause}
    GROUP BY ats_name, tier
    ORDER BY total_shares DESC
    LIMIT 10;
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
    """Generate query to find the earliest month/year (executing_bd_606) with PFOF > 0."""
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
SELECT year, month, total_pfof_usd
FROM by_month
WHERE total_pfof_usd > 0
ORDER BY year ASC, (NULLIF(month, '')::int) ASC
LIMIT 1;
"""

def generate_earliest_pfof_by_broker_query() -> str:
    """Generate query to find the earliest month/year per broker (executing_bd_606) with PFOF > 0."""
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
    """Generate query to find the longest consecutive month streak with PFOF > 0 per broker→venue pair."""
    return """
    WITH broker_venue_streaks AS (
        SELECT
            executing_bd,
            venues,
            EXTRACT(MONTH FROM day) AS month,
            EXTRACT(YEAR FROM day) AS year,
            SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) +
                COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
                COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
                COALESCE(netpmtpaidrecvotherordersusd, 0)) AS total_pfof_usd
        FROM executing_bd_606
        WHERE data_type = 'venue'
        GROUP BY executing_bd, venues, month, year
        HAVING SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) +
                   COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +
                   COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +
                   COALESCE(netpmtpaidrecvotherordersusd, 0)) > 0
    ),
    consecutive_months AS (
        SELECT
            executing_bd,
            venues,
            month,
            year,
            total_pfof_usd,
            ROW_NUMBER() OVER (PARTITION BY executing_bd, venues ORDER BY year, month) AS streak_start_index
        FROM broker_venue_streaks
    ),
    streak_lengths AS (
        SELECT
            executing_bd,
            venues,
            month,
            year,
            total_pfof_usd,
            streak_start_index,
            COUNT(*) OVER (PARTITION BY executing_bd, venues, streak_start_index) AS streak_length
        FROM consecutive_months
    )
    SELECT
        executing_bd,
        venues,
        streak_length,
        MIN(year) OVER (PARTITION BY executing_bd, venues, streak_length) AS start_year,
        MIN(month) OVER (PARTITION BY executing_bd, venues, streak_length) AS start_month,
        MAX(year) OVER (PARTITION BY executing_bd, venues, streak_length) AS end_year,
        MAX(month) OVER (PARTITION BY executing_bd, venues, streak_length) AS end_month
    FROM streak_lengths
    ORDER BY streak_length DESC, executing_bd, venues, start_year, start_month;
    """

def _ats_patterns_for_venue(canonical_venue: str) -> List[str]:
    """Return ILIKE patterns to match ATS names related to a venue.
    1) First, try to map from venue_mapping to real ATS names (preferred)
    2) If nothing found, fall back to simple string heuristics
    """
    base = (canonical_venue or "").strip()
    if not base:
        return []

    # Try DB-backed mapping from venue_mapping
    try:
        local_cur = conn.cursor()
        like = f"%{base}%"
        local_cur.execute(
            """
            SELECT DISTINCT ats_name
            FROM venue_mapping
            WHERE ats_name IS NOT NULL AND ats_name != ''
              AND entity_type ILIKE 'ATS'
              AND (
                    ats_name ILIKE %s
                 OR canonical_name ILIKE %s
              )
            """,
            (like, like)
        )
        rows = local_cur.fetchall()
        local_cur.close()

        mapping_patterns: set[str] = set()
        for row in rows:
            ats = (row[0] or "").strip()
            if not ats:
                continue
            mapping_patterns.add(f"%{ats}%")
            upper = ats.upper()
            for suffix in [" ATS", " LLC", " INC", ", LLC", ", INC.", " LP", ", LP"]:
                if upper.endswith(suffix):
                    short = upper.replace(suffix, "").strip()
                    if short:
                        mapping_patterns.add(f"%{short}%")
        if mapping_patterns:
            return list(mapping_patterns)
    except Exception:
        # Ignore mapping errors and fall back to heuristics
        pass

    # Heuristic fallback if mapping did not yield patterns
    patterns: set[str] = set()
    patterns.add(f"%{base}%")
    if not base.upper().endswith(" ATS"):
        patterns.add(f"%{base}%ATS%")
    upper = base.upper()
    for suffix in [" LLC", " INC", ", LLC", ", INC.", " LP", ", LP"]:
        if suffix in upper:
            short = upper.replace(suffix, "").strip()
            if short:
                patterns.add(f"%{short}%")
                patterns.add(f"%{short}%ATS%")
    return list(patterns)

def generate_entity_query(query_tags: Dict) -> str:
    """Generate entity types query"""
    return """
    SELECT 
        venue_name,
        entity_type,
        parent_organization,
        description
    FROM entity_types
    ORDER BY venue_name
    LIMIT 20;
    """

def generate_openai_synthesis(user_input: str, query_results: Dict, query_tags: Dict) -> str:
    """Generate OpenAI synthesis of multiple query results"""
    # Global toggle: disable narrative entirely
    try:
        if os.getenv("DISABLE_NARRATIVE", "false").lower() == "true":
            return ""
    except Exception:
        pass
    # 0) Strict priority: if user asked for "first/earliest" per broker and we have it, return that directly
    try:
        if (query_tags.get('mentions_first')
            and 'earliest_pfof_by_broker' in query_results
            and 'results' in query_results['earliest_pfof_by_broker']
            and query_results['earliest_pfof_by_broker']['results']):
            rows = query_results['earliest_pfof_by_broker']['results']
            lines = []
            for r in rows:
                bd = r.get('executing_bd')
                y = r.get('year')
                m = r.get('month')
                val = r.get('total_pfof_usd')
                if bd is not None and y is not None and m is not None:
                    if val is not None:
                        lines.append(f"{bd}: {m}/{y} (${val:,.2f})")
                    else:
                        lines.append(f"{bd}: {m}/{y}")
            if lines:
                return "Earliest PFOF month per broker:\n" + "\n".join(f"- {ln}" for ln in lines)
    except Exception:
        pass

    # If we have explicit CPH results, build a deterministic answer
    try:
        if 'cph_data' in query_results and 'results' in query_results['cph_data'] and query_results['cph_data']['results']:
            rows = query_results['cph_data']['results']
            # Deduplicate defensively
            seen = set()
            grouped = {}
            for r in rows:
                key = (r.get('executing_bd'), r.get('stock_group'), float(r.get('cph_max') or 0))
                if key in seen:
                    continue
                seen.add(key)
                sg = r.get('stock_group') or 'Unknown'
                grouped.setdefault(sg, []).append((r.get('executing_bd'), r.get('cph_max')))
            # Build lines per stock group
            lines = []
            period = []
            if query_tags.get('month'):
                # Convert month number to name if given as int
                month_map = {1:'January',2:'February',3:'March',4:'April',5:'May',6:'June',7:'July',8:'August',9:'September',10:'October',11:'November',12:'December'}
                m = query_tags['month']
                month_name = month_map.get(m, str(m)) if isinstance(m, int) else str(m)
                period.append(month_name)
            if query_tags.get('year'):
                period.append(str(query_tags['year']))
            period_str = ' '.join(period) if period else 'the requested period'

            for sg in sorted(grouped.keys()):
                top = grouped[sg][:3]
                parts = [f"{name} ({cph:.2f} cph)" for name, cph in top if name is not None and cph is not None]
                if parts:
                    lines.append(f"{sg}: " + ", ".join(parts))

            if lines:
                return (
                    f"Top brokers by PFOF rate (CPH) in {period_str}, per stock group:\n"
                    + "\n".join(f"- {ln}" for ln in lines)
                )
    except Exception:
        # Fall back to OpenAI synthesis path below on any formatting error
        pass

    # If we have top PFOF per stock group, produce segmented deterministic answer
    try:
        if 'pfof_by_stock_group' in query_results and 'results' in query_results['pfof_by_stock_group'] and query_results['pfof_by_stock_group']['results']:
            rows = query_results['pfof_by_stock_group']['results']
            grouped = {}
            for r in rows:
                sg = r.get('stock_group') or 'Unknown'
                grouped[sg] = (r.get('executing_bd'), r.get('total_pfof_usd'))

            period = []
            if query_tags.get('month'):
                month_map = {1:'January',2:'February',3:'March',4:'April',5:'May',6:'June',7:'July',8:'August',9:'September',10:'October',11:'November',12:'December'}
                m = query_tags['month']
                month_name = month_map.get(m, str(m)) if isinstance(m, int) else str(m)
                period.append(month_name)
            if query_tags.get('year'):
                period.append(str(query_tags['year']))
            period_str = ' '.join(period) if period else 'the requested period'

            lines = []
            for sg in sorted(grouped.keys()):
                name, usd = grouped[sg]
                if name is not None and usd is not None:
                    lines.append(f"{sg}: {name} (${usd:,.2f})")
            if lines:
                return (
                    f"Top broker by PFOF in {period_str}, per stock group:\n"
                    + "\n".join(f"- {ln}" for ln in lines)
                )
    except Exception:
        pass

    # If we have top PFOF per order type, produce segmented deterministic answer
    try:
        if 'pfof_by_order_type' in query_results and 'results' in query_results['pfof_by_order_type'] and query_results['pfof_by_order_type']['results']:
            rows = query_results['pfof_by_order_type']['results']
            mapping = {
                'market': 'Market Orders',
                'marketable_limit': 'Marketable Limit Orders',
                'nonmarketable_limit': 'Nonmarketable Limit Orders',
                'other': 'Other Orders'
            }
            results_map = {}
            for r in rows:
                ot = r.get('order_type')
                results_map[ot] = (r.get('executing_bd'), r.get('total_pfof_usd'))

            period = []
            if query_tags.get('month'):
                month_map = {1:'January',2:'February',3:'March',4:'April',5:'May',6:'June',7:'July',8:'August',9:'September',10:'October',11:'November',12:'December'}
                m = query_tags['month']
                month_name = month_map.get(m, str(m)) if isinstance(m, int) else str(m)
                period.append(month_name)
            if query_tags.get('year'):
                period.append(str(query_tags['year']))
            period_str = ' '.join(period) if period else 'the requested period'

            lines = []
            for key in ['market','marketable_limit','nonmarketable_limit','other']:
                if key in results_map:
                    name, usd = results_map[key]
                    if name is not None and usd is not None:
                        lines.append(f"{mapping[key]}: {name} (${usd:,.2f})")
            if lines:
                return (
                    f"Top broker by PFOF in {period_str}, per order type:\n"
                    + "\n".join(f"- {ln}" for ln in lines)
                )
    except Exception:
        pass

    # Earliest PFOF month
    try:
        if 'earliest_pfof_month' in query_results and 'results' in query_results['earliest_pfof_month'] and query_results['earliest_pfof_month']['results']:
            r = query_results['earliest_pfof_month']['results'][0]
            y = r.get('year')
            m = r.get('month')
            total = r.get('total_pfof_usd')
            line = f"Earliest PFOF observed: {m}/{y} (total ${total:,.2f})."
            # If per-broker earliest also present, provide first 3 examples
            if 'earliest_pfof_by_broker' in query_results and 'results' in query_results['earliest_pfof_by_broker'] and query_results['earliest_pfof_by_broker']['results']:
                examples = []
                for br in query_results['earliest_pfof_by_broker']['results'][:3]:
                    examples.append(f"{br.get('executing_bd')} ({br.get('month')}/{br.get('year')})")
                if examples:
                    line += " Examples: " + ", ".join(examples)
            return line
    except Exception:
        pass

    # Longest streak summary
    try:
        if 'streak_data' in query_results and 'results' in query_results['streak_data'] and query_results['streak_data']['results']:
            r = query_results['streak_data']['results'][0]
            ed = r.get('executing_bd')
            vn = r.get('venues')
            sl = r.get('streak_length')
            sy = r.get('start_year')
            sm = r.get('start_month')
            ey = r.get('end_year')
            em = r.get('end_month')
            return f"Longest broker→venue streak: {ed} → {vn}, {sl} months ({sm}/{sy} to {em}/{ey})."
    except Exception:
        pass

    # Prepare data for OpenAI
    data_summary = {}
    for query_name, result in query_results.items():
        if 'error' not in result:
            # Convert Decimal types to float for JSON serialization
            sample_data = []
            for row in result['results'][:3]:  # First 3 rows
                converted_row = {}
                for key, value in row.items():
                    if hasattr(value, '__class__') and 'Decimal' in str(value.__class__):
                        converted_row[key] = float(value)
                    else:
                        converted_row[key] = value
                sample_data.append(converted_row)
            
            data_summary[query_name] = {
                'description': result['description'],
                'row_count': result['row_count'],
                'sample_data': sample_data
            }
        else:
            data_summary[query_name] = {
                'description': result['description'],
                'error': result['error']
            }
    
    # Create synthesis prompt
    synthesis_prompt = f"""
    You are a financial data analyst. Analyze the following query results and provide a comprehensive response to the user's question.
    Do not make any suggestions or hypothesis about the causes of the data. 

    User Question: "{user_input}"

    Query Results:
    {json.dumps(data_summary, indent=2)}

    Please provide:
    1. A direct answer to the user's question
    2. Key insights from the data
    3. Context and analysis
    4. Any relevant trends or patterns

    Be specific with numbers and provide actionable insights.
    If there is an error, include the phrase "Error: {{error}}".
    If there is a warning, include the phrase "Warning: {{warning}}".
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial data analyst specializing in market structure and PFOF analysis."},
                {"role": "user", "content": synthesis_prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error generating synthesis: {str(e)}"

def _enrich_time_with_parsedatetime(user_input: str, tags: Dict) -> Dict:
    """Fill missing year/month/quarter using parsedatetime; keep existing tags authoritative."""
    if not CAL:
        return tags
    try:
        dt, status = CAL.parseDT(user_input, datetime.now())
        # status >= 1 implies date components parsed
        if status and dt:
            if not tags.get('year'):
                tags['year'] = dt.year
                tags['mentions_year'] = True
            if not tags.get('month'):
                tags['month'] = dt.month
                tags['mentions_month'] = True
        # Quarter from explicit Qn or derive from month
        if not tags.get('quarter'):
            m = re.search(r"\bq([1-4])\b", user_input.lower())
            if m:
                tags['quarter'] = int(m.group(1))
                tags['mentions_quarter'] = True
            elif tags.get('month'):
                tags['quarter'] = ((int(tags['month']) - 1) // 3) + 1
                tags['mentions_quarter'] = True
    except Exception:
        return tags
    return tags

# -----------------------------
# Hybrid Routing Logic
# -----------------------------

def is_simple_two_table_query(query_tags: Dict) -> bool:
    """Determine if this is a simple two-table query (executing_bd_606 + monthly_data)"""
    
    # Time-based volume queries
    has_time = query_tags.get('mentions_month') or query_tags.get('mentions_year') or query_tags.get('mentions_quarter') or query_tags.get('year') or query_tags.get('month')
    has_volume = query_tags.get('mentions_volume')
    has_pfof = query_tags.get('mentions_pfof')
    
    # Simple two-table pattern: time + (volume OR pfof)
    return has_time and (has_volume or has_pfof)

# (Removed Virtu-specific routing predicate)

def is_complex_multi_table_query(query_tags: Dict) -> bool:
    """Determine if this is a complex multi-table query requiring synthesis"""
    
    # Count relevant query patterns
    pattern_count = sum([
        query_tags.get('mentions_pfof', False),
        query_tags.get('mentions_volume', False),
        query_tags.get('mentions_trend', False),
        query_tags.get('mentions_ats', False),
        query_tags.get('mentions_venue', False),
        query_tags.get('mentions_entity_type', False)
    ])
    
    # Complex if multiple patterns or specific complex patterns
    return pattern_count >= 3 or query_tags.get('mentions_trend')

def route_hybrid_query(user_input: str, query_tags: Dict) -> Dict:
    """Route query to appropriate handler based on complexity"""
    
    print(f"🔍 Query Classification: {query_tags}")
    # 0) Planner single-shot path (default). Returns first if deterministically plannable.
    try:
        planned_sql = plan_single_sql(user_input, dict(query_tags))
        if planned_sql:
            print("🧭 Planner produced single-shot SQL")
            try:
                cursor.execute(planned_sql)
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description] if cursor.description else []
                formatted = [dict(zip(cols, r)) for r in rows] if rows else []
                return {
                    "question": user_input,
                    "query_type": "direct_single",
                    "sql": planned_sql,
                    "results": formatted,
                    "row_count": len(formatted),
                    "query_classification": query_tags
                }
            except Exception as e_pl:
                try:
                    conn.rollback()
                except Exception:
                    pass
                print(f"Planner SQL failed: {e_pl} — falling through to other handlers")
    except Exception as e_plan:
        print(f"Planner routing error: {e_plan}")
    # 1) Direct list/unique (legacy simple path)
    if _is_list_unique_query(user_input, query_tags):
        print("🎯 Routing to direct single-shot: DISTINCT list query")
        return execute_direct_list_query(user_input, query_tags)

    # 2) Direct single-shot: PFOF by venue for broker (legacy specific)
    if _is_direct_pfof_broker_venues_query(user_input, query_tags):
        print("🎯 Routing to direct single-shot: PFOF by venue for broker")
        return execute_direct_pfof_by_venue_for_broker(user_input, query_tags)

    # 3) Fallback: complex multi-table handler
    print("🔗 Routing to complex multi-table handler")
    return generate_complex_multi_table_query(user_input, query_tags)

# -----------------------------
# Test Functions
# -----------------------------

def test_two_table_query():
    """Test the two-table query handler"""
    test_query = "What venue received the most volume in January 2024?"
    query_tags = {
        'mentions_volume': True,
        'mentions_month': True,
        'year': 2024,
        'month': 1
    }
    
    result = execute_time_based_volume_query(test_query, query_tags)
    print("Two-Table Query Test:")
    print(f"Question: {test_query}")
    print(f"Response: {result.get('response', 'Error')}")
    return result

def test_complex_query():
    """Test the complex multi-table query handler"""
    test_query = "Compare all brokers' PFOF performance and market trends for 2024"
    query_tags = {
        'mentions_pfof': True,
        'mentions_trend': True,
        'mentions_broker': True,
        'year': 2024
    }
    
    result = generate_complex_multi_table_query(test_query, query_tags)
    print("Complex Multi-Table Query Test:")
    print(f"Question: {test_query}")
    print(f"Synthesis: {result.get('synthesis', 'Error')}")
    return result

def test_virtu_ats_query():
    """Test the Virtu ATS query handler"""
    test_query = "What was Virtu's ATS performance in January 2024?"
    query_tags = {
        'mentions_virtu': True,
        'mentions_month': True,
        'year': 2024,
        'month': 1
    }
    
    result = execute_virtu_ats_query(test_query, query_tags)
    print("Virtu ATS Query Test:")
    print(f"Question: {test_query}")
    print(f"Response: {result.get('response', 'Error')}")
    return result

if __name__ == "__main__":
    print("Testing Hybrid Query Handler...")
    print("=" * 60)
    
    # Test two-table query
    test_two_table_query()
    
    print("\n" + "=" * 60)
    
    # Test Virtu ATS query
    test_virtu_ats_query()
    
    print("\n" + "=" * 60)
    
    # Test complex query
    test_complex_query()
