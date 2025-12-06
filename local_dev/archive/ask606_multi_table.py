# ask606_multi_table.py

from openai import OpenAI
import psycopg2
import os
from dotenv import load_dotenv
from multi_table_query_framework import (
    load_all_schemas,
    route_query,
    classify_query_enhanced,
    generate_market_data_query,
    generate_volume_estimation_query,
    sanitize_sql_output
)
from handlers.executing_bd_606_handler import (
    generate_top_cph_brokers_query,
    generate_top_pfof_broker_per_stock_group_query,
    generate_top_pfof_broker_per_order_type_query,
    generate_earliest_pfof_month_query,
    generate_earliest_pfof_by_broker_query,
    generate_longest_broker_venue_streak_query,
    generate_top_pfof_broker_per_quarter_query,
)
from handlers.monthly_data_handler import (
    generate_top_exchange_share_per_quarter_query,
)
from handlers.finra_ats_handler import (
    generate_top_ats_shares_per_quarter_query,
)

# Optional NL2SQL semantic hint adapter (hints only by default)
try:
    from semantic_sql_adapter import (  # type: ignore
        get_sql_hint as _get_sql_hint,
        build_intent_from_user_input as _build_intent,
        build_final_sql as _build_final_sql,
    )
    _ADAPTER_OK = True
except Exception:  # adapter or deps may be absent; fall back gracefully
    _ADAPTER_OK = False
    _get_sql_hint = lambda q, i: None  # type: ignore
    _build_intent = lambda q, t: t  # type: ignore
    _build_final_sql = lambda i, h=None: None  # type: ignore

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

def ask_multi_table(question: str):
    """Enhanced ask function that uses multi-table query framework"""
    
    # Load all schemas
    all_schemas = load_all_schemas()
    
    # Route the query to get targeted system prompt and relevant tables
    system_prompt, relevant_tables = route_query(question, all_schemas)
    
    # Classify the query
    query_tags = classify_query_enhanced(question)
    
    print(f"🔍 Query Classification: {query_tags}")
    print(f"📊 Relevant Tables: {relevant_tables}")
    
    hint_sql = None
    final_hint_sql = None

    # Check if this is a volume query and route to custom function
    if query_tags.get("mentions_volume"):
        print("📈 Volume query detected - using custom volume estimation")
        sql = generate_volume_estimation_query(question, query_tags)
        print(f"Generated Volume SQL: \n{sql}")
    else:
        # Use OpenAI for other queries
        print("🤖 Using OpenAI for query generation")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.1
        )
        sql = response.choices[0].message.content.strip()
    
    # Sanitize the SQL from LLM output
    sql = sanitize_sql_output(sql)

    # Optionally compute and (optionally) apply semantic NL2SQL hints
    try:
        show_hints = os.getenv("SHOW_SEMANTIC_HINTS", "false").lower() == "true"
        use_hints = os.getenv("USE_SEMANTIC_HINTS", "false").lower() == "true"
        if _ADAPTER_OK and (show_hints or use_hints):
            intent = _build_intent(question, dict(query_tags))
            hint_sql = _get_sql_hint(question, intent)
            if use_hints and hint_sql:
                final_hint_sql = _build_final_sql(intent, hint_sql)
                if final_hint_sql:
                    sql = sanitize_sql_output(final_hint_sql)
    except Exception:
        # Do not block execution if adapter or deps are missing
        pass
    
    try:
        # Execute the primary query
        cursor.execute(sql)
        results = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description] if cursor.description else []
        primary_formatted = [dict(zip(column_names, row)) for row in results] if results else []

        # Build query_results with primary
        query_results = {
            'primary': {
                'description': 'Primary query result',
                'query': sql,
                'results': primary_formatted,
                'row_count': len(primary_formatted),
            }
        }

        # Attach semantic hint info for transparency if requested
        try:
            show_hints = os.getenv("SHOW_SEMANTIC_HINTS", "false").lower() == "true"
            use_hints = os.getenv("USE_SEMANTIC_HINTS", "false").lower() == "true"
            if _ADAPTER_OK and (show_hints or use_hints):
                query_results['semantic_nl2sql'] = {
                    'used': use_hints,
                    'hint': hint_sql,
                    'final_sql': final_hint_sql,
                }
        except Exception:
            pass

        # Add market_data if month/quarter mentioned
        if query_tags.get('mentions_trend') or query_tags.get('mentions_month') or query_tags.get('mentions_quarter'):
            try:
                md_sql = generate_market_data_query(query_tags)
                cursor.execute(md_sql)
                md_rows = cursor.fetchall()
                md_cols = [d[0] for d in cursor.description] if cursor.description else []
                md_fmt = [dict(zip(md_cols, r)) for r in md_rows]
                query_results['market_data'] = {
                    'description': 'Market volume data from monthly_data',
                    'query': md_sql,
                    'results': md_fmt,
                    'row_count': len(md_fmt)
                }
            except Exception as e_md:
                query_results['market_data'] = {
                    'description': 'Market volume data from monthly_data',
                    'query': md_sql,
                    'error': str(e_md),
                    'row_count': 0
                }

        # Add cph_data if asked about rate/CPH
        if query_tags.get('mentions_cph') or (query_tags.get('mentions_rate') and query_tags.get('mentions_broker')):
            try:
                cph_sql = generate_top_cph_brokers_query(query_tags)
                cursor.execute(cph_sql)
                cph_rows = cursor.fetchall()
                cph_cols = [d[0] for d in cursor.description] if cursor.description else []
                cph_fmt = [dict(zip(cph_cols, r)) for r in cph_rows]
                query_results['cph_data'] = {
                    'description': 'Top brokers by CPH per stock group from executing_bd_606',
                    'query': cph_sql,
                    'results': cph_fmt,
                    'row_count': len(cph_fmt)
                }
            except Exception as e_cph:
                query_results['cph_data'] = {
                    'description': 'Top brokers by CPH per stock group from executing_bd_606',
                    'query': cph_sql,
                    'error': str(e_cph),
                    'row_count': 0
                }

        # Add pfof_by_stock_group when asking across stock groups
        if query_tags.get('mentions_pfof') and ('stock group' in question.lower() or query_tags.get('mentions_order_type')):
            try:
                sgs_sql = generate_top_pfof_broker_per_stock_group_query(query_tags)
                cursor.execute(sgs_sql)
                sgs_rows = cursor.fetchall()
                sgs_cols = [d[0] for d in cursor.description] if cursor.description else []
                sgs_fmt = [dict(zip(sgs_cols, r)) for r in sgs_rows]
                query_results['pfof_by_stock_group'] = {
                    'description': 'Top broker by total PFOF per stock group from executing_bd_606',
                    'query': sgs_sql,
                    'results': sgs_fmt,
                    'row_count': len(sgs_fmt)
                }
            except Exception as e_sgs:
                query_results['pfof_by_stock_group'] = {
                    'description': 'Top broker by total PFOF per stock group from executing_bd_606',
                    'query': sgs_sql,
                    'error': str(e_sgs),
                    'row_count': 0
                }

        # Add pfof_by_order_type when order types mentioned
        if query_tags.get('mentions_pfof') and query_tags.get('mentions_order_type'):
            try:
                ot_sql = generate_top_pfof_broker_per_order_type_query(query_tags)
                cursor.execute(ot_sql)
                ot_rows = cursor.fetchall()
                ot_cols = [d[0] for d in cursor.description] if cursor.description else []
                ot_fmt = [dict(zip(ot_cols, r)) for r in ot_rows]
                query_results['pfof_by_order_type'] = {
                    'description': 'Top broker by total PFOF per order type from executing_bd_606',
                    'query': ot_sql,
                    'results': ot_fmt,
                    'row_count': len(ot_fmt)
                }
            except Exception as e_ot:
                query_results['pfof_by_order_type'] = {
                    'description': 'Top broker by total PFOF per order type from executing_bd_606',
                    'query': ot_sql,
                    'error': str(e_ot),
                    'row_count': 0
                }

        # Earliest PFOF month (overall and per-broker)
        if query_tags.get('mentions_pfof') and query_tags.get('mentions_first'):
            try:
                e_sql = generate_earliest_pfof_month_query()
                cursor.execute(e_sql)
                e_rows = cursor.fetchall()
                e_cols = [d[0] for d in cursor.description] if cursor.description else []
                e_fmt = [dict(zip(e_cols, r)) for r in e_rows]
                query_results['earliest_pfof_month'] = {
                    'description': 'Earliest month/year with PFOF > 0',
                    'query': e_sql,
                    'results': e_fmt,
                    'row_count': len(e_fmt)
                }
            except Exception as e_e:
                query_results['earliest_pfof_month'] = {
                    'description': 'Earliest month/year with PFOF > 0',
                    'query': e_sql,
                    'error': str(e_e),
                    'row_count': 0
                }
            try:
                eb_sql = generate_earliest_pfof_by_broker_query()
                cursor.execute(eb_sql)
                eb_rows = cursor.fetchall()
                eb_cols = [d[0] for d in cursor.description] if cursor.description else []
                eb_fmt = [dict(zip(eb_cols, r)) for r in eb_rows]
                query_results['earliest_pfof_by_broker'] = {
                    'description': 'Earliest month/year per broker with PFOF > 0',
                    'query': eb_sql,
                    'results': eb_fmt,
                    'row_count': len(eb_fmt)
                }
            except Exception as e_eb:
                query_results['earliest_pfof_by_broker'] = {
                    'description': 'Earliest month/year per broker with PFOF > 0',
                    'query': eb_sql,
                    'error': str(e_eb),
                    'row_count': 0
                }

        # Longest broker→venue streak
        if query_tags.get('mentions_streak'):
            try:
                st_sql = generate_longest_broker_venue_streak_query()
                cursor.execute(st_sql)
                st_rows = cursor.fetchall()
                st_cols = [d[0] for d in cursor.description] if cursor.description else []
                st_fmt = [dict(zip(st_cols, r)) for r in st_rows]
                query_results['streak_data'] = {
                    'description': 'Longest consecutive month streak with PFOF > 0 per broker→venue pair',
                    'query': st_sql,
                    'results': st_fmt,
                    'row_count': len(st_fmt)
                }
            except Exception as e_st:
                query_results['streak_data'] = {
                    'description': 'Longest consecutive month streak with PFOF > 0 per broker→venue pair',
                    'query': st_sql,
                    'error': str(e_st),
                    'row_count': 0
                }

        # Quarter-based PFOF top broker
        if query_tags.get('mentions_pfof') and (query_tags.get('mentions_quarter') or query_tags.get('year')):
            try:
                pq_sql = generate_top_pfof_broker_per_quarter_query(query_tags)
                cursor.execute(pq_sql)
                pq_rows = cursor.fetchall()
                pq_cols = [d[0] for d in cursor.description] if cursor.description else []
                pq_fmt = [dict(zip(pq_cols, r)) for r in pq_rows]
                query_results['pfof_by_quarter'] = {
                    'description': 'Top broker by total PFOF per quarter from executing_bd_606',
                    'query': pq_sql,
                    'results': pq_fmt,
                    'row_count': len(pq_fmt)
                }
            except Exception as e_pq:
                query_results['pfof_by_quarter'] = {
                    'description': 'Top broker by total PFOF per quarter from executing_bd_606',
                    'query': pq_sql,
                    'error': str(e_pq),
                    'row_count': 0
                }

        # Exchange with largest market share per quarter
        if query_tags.get('mentions_market_share') and (query_tags.get('mentions_quarter') or query_tags.get('year')):
            try:
                es_sql = generate_top_exchange_share_per_quarter_query(query_tags)
                cursor.execute(es_sql)
                es_rows = cursor.fetchall()
                es_cols = [d[0] for d in cursor.description] if cursor.description else []
                es_fmt = [dict(zip(es_cols, r)) for r in es_rows]
                query_results['exchange_share_by_quarter'] = {
                    'description': 'Exchange with largest market share per quarter from monthly_data',
                    'query': es_sql,
                    'results': es_fmt,
                    'row_count': len(es_fmt)
                }
            except Exception as e_es:
                query_results['exchange_share_by_quarter'] = {
                    'description': 'Exchange with largest market share per quarter from monthly_data',
                    'query': es_sql,
                    'error': str(e_es),
                    'row_count': 0
                }

        # ATS with highest share volume per quarter
        if query_tags.get('mentions_ats') and (query_tags.get('mentions_quarter') or query_tags.get('year')):
            try:
                ats_sql = generate_top_ats_shares_per_quarter_query(query_tags)
                cursor.execute(ats_sql)
                ats_rows = cursor.fetchall()
                ats_cols = [d[0] for d in cursor.description] if cursor.description else []
                ats_fmt = [dict(zip(ats_cols, r)) for r in ats_rows]
                query_results['ats_top_by_quarter'] = {
                    'description': 'ATS with highest share volume per quarter from finra_ats',
                    'query': ats_sql,
                    'results': ats_fmt,
                    'row_count': len(ats_fmt)
                }
            except Exception as e_ats:
                query_results['ats_top_by_quarter'] = {
                    'description': 'ATS with highest share volume per quarter from finra_ats',
                    'query': ats_sql,
                    'error': str(e_ats),
                    'row_count': 0
                }

        # Deterministic synthesis (subset of hybrid)
        synthesis = _multi_deterministic_synthesis(query_results, query_tags)

        return {
            'question': question,
            'query_results': query_results,
            'synthesis': synthesis,
            'query_classification': query_tags
        }
            
    except Exception as e:
        error_msg = str(e)
        try:
            conn.rollback()
        except Exception:
            pass
        
        # Fallback: If LLM SQL against monthly_data failed due to GROUP BY/day issues,
        # use a deterministic monthly_data aggregation query.
        if ("monthly_data" in sql.lower() or "monthly_data" in error_msg.lower()) and (
            "must appear in the GROUP BY clause" in error_msg.lower() or
            "column" in error_msg.lower() and "day" in error_msg.lower()
        ):
            try:
                fallback_sql = generate_market_data_query(query_tags)
                cursor.execute(fallback_sql)
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                formatted_results = [dict(zip(column_names, row)) for row in results]
                return {
                    "question": question,
                    "sql": fallback_sql,
                    "results": formatted_results,
                    "row_count": len(formatted_results),
                    "relevant_tables": relevant_tables,
                    "query_classification": query_tags,
                    "note": "Used deterministic monthly_data fallback due to GROUP BY/day aggregation error"
                }
            except Exception as e2:
                return {
                    "question": question,
                    "sql": sql,
                    "error": f"{error_msg} | Fallback error: {str(e2)}",
                    "relevant_tables": relevant_tables,
                    "query_classification": query_tags
                }
        else:
            return {
                "question": question,
                "sql": sql,
                "error": error_msg,
                "relevant_tables": relevant_tables,
                "query_classification": query_tags
            }
            
def _multi_deterministic_synthesis(query_results: dict, query_tags: dict) -> str:
    # CPH summary
    try:
        if 'cph_data' in query_results and 'results' in query_results['cph_data'] and query_results['cph_data']['results']:
            rows = query_results['cph_data']['results']
            seen = set()
            grouped = {}
            for r in rows:
                key = (r.get('executing_bd'), r.get('stock_group'), float(r.get('cph_max') or 0))
                if key in seen:
                    continue
                seen.add(key)
                sg = r.get('stock_group') or 'Unknown'
                grouped.setdefault(sg, []).append((r.get('executing_bd'), r.get('cph_max')))
            lines = []
            period = []
            if query_tags.get('month'):
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
                    f"Top brokers by PFOF rate (CPH) in {period_str}, per stock group:\n" + "\n".join(f"- {ln}" for ln in lines)
                )
    except Exception:
        pass

    # PFOF by stock group
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
                return f"Top broker by PFOF in {period_str}, per stock group:\n" + "\n".join(f"- {ln}" for ln in lines)
    except Exception:
        pass

    # PFOF by order type
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
            for key, label in mapping.items():
                if key in results_map:
                    name, usd = results_map[key]
                    if name is not None and usd is not None:
                        lines.append(f"{label}: {name} (${usd:,.2f})")
            if lines:
                return f"Top broker by PFOF in {period_str}, per order type:\n" + "\n".join(f"- {ln}" for ln in lines)
    except Exception:
        pass

    # Earliest PFOF month
    try:
        if 'earliest_pfof_month' in query_results and 'results' in query_results['earliest_pfof_month'] and query_results['earliest_pfof_month']['results']:
            r = query_results['earliest_pfof_month']['results'][0]
            y = r.get('year')
            m = r.get('month')
            total = r.get('total_pfof_usd')
            return f"Earliest PFOF observed: {m}/{y} (total ${total:,.2f})."
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

    # Fallback: no deterministic synthesis
    return ""

# Backward compatibility function
def ask(question: str):
    """Backward compatibility - uses multi-table framework"""
    return ask_multi_table(question)

if __name__ == "__main__":
    # Test the multi-table framework
    test_questions = [
        "What is the volume for citadel?",
        "Show me monthly trends for 2024",
        "What ATS venues are available?",
        "Compare brokers by PFOF payments",
        "What are the top venues by volume?"
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print('='*60)
        result = ask_multi_table(question)
        print(f"SQL: {result.get('sql', 'N/A')}")
        print(f"Results: {result.get('row_count', 0)} rows")
        if result.get('error'):
            print(f"Error: {result['error']}")
        print()
