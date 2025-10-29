# hybrid_query_handler.py

import os
import re
import json
from typing import List, Dict, Optional, Tuple
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI

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

# Handler 2: executing_bd_606 + finra_ats (broker-specific ATS analysis)

def generate_virtu_ats_query(user_input: str, query_tags: Dict) -> Tuple[str, str]:
    """
    Generate two-table query for Virtu ATS analysis.
    Returns: (main_query, context_query)
    """
    
    # Extract time parameters
    year = query_tags.get('year', 2024)
    quarter = None
    
    # Determine quarter from month or explicit quarter mention
    if query_tags.get('month'):
        month = query_tags['month']
        if month in [1, 2, 3]:
            quarter = 1
        elif month in [4, 5, 6]:
            quarter = 2
        elif month in [7, 8, 9]:
            quarter = 3
        elif month in [10, 11, 12]:
            quarter = 4
    elif query_tags.get('mentions_quarter'):
        # Extract quarter from query tags if available
        quarter = query_tags.get('quarter')
    
    # Build WHERE conditions for main query (executing_bd_606)
    where_conditions = [
        f"year = {year}",
        "data_type = 'venue'",
        "venues IS NOT NULL",
        "venues != ''",
        "(venues ILIKE '%VIRTU%' OR venues ILIKE '%VIRTUAL%')"
    ]
    
    if quarter:
        where_conditions.append(f"month IN ('{quarter*3-2}', '{quarter*3-1}', '{quarter*3}')")
    
    # Main query: Get Virtu PFOF data from executing_bd_606
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
    ORDER BY estimated_volume DESC;
    """
    
    # Context query: Get Virtu ATS data from finra_ats
    ats_where_conditions = [
        f"year = {year}",
        "ats_name ILIKE '%VIRTU%'"
    ]
    
    if quarter:
        ats_where_conditions.append(f"quarter = '{quarter}'")
    
    context_query = f"""
    SELECT 
        ats_name,
        tier,
        SUM(total_shares) as total_ats_shares,
        SUM(total_trades) as total_ats_trades,
        COUNT(DISTINCT quarter) as quarters_active
    FROM finra_ats
    WHERE {' AND '.join(ats_where_conditions)}
    GROUP BY ats_name, tier
    ORDER BY total_ats_shares DESC;
    """
    
    return main_query.strip(), context_query.strip()

def execute_virtu_ats_query(user_input: str, query_tags: Dict) -> Dict:
    """Execute the two-table Virtu ATS query"""
    
    print("🔗 Two-table query detected - executing_bd_606 + finra_ats (Virtu ATS)")
    
    # Generate queries
    main_query, context_query = generate_virtu_ats_query(user_input, query_tags)
    
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
        response = generate_virtu_ats_response(user_input, main_data, context_data, query_tags)
        
        return {
            "question": user_input,
            "query_type": "two_table_virtu_ats",
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
            "query_type": "two_table_virtu_ats",
            "main_query": main_query,
            "context_query": context_query,
            "error": str(e),
            "query_classification": query_tags
        }

def generate_virtu_ats_response(user_input: str, main_data: List[Dict], context_data: List[Dict], query_tags: Dict) -> str:
    """Generate natural language response for Virtu ATS query"""
    
    if not main_data and not context_data:
        return "No Virtu-related data found for the specified time period."
    
    # Extract time information
    year = query_tags.get('year', 2024)
    quarter = None
    
    if query_tags.get('month'):
        month = query_tags['month']
        if month in [1, 2, 3]:
            quarter = 1
        elif month in [4, 5, 6]:
            quarter = 2
        elif month in [7, 8, 9]:
            quarter = 3
        elif month in [10, 11, 12]:
            quarter = 4
    
    # Get PFOF data
    total_pfof_usd = 0
    total_estimated_volume = 0
    virtu_venues = []
    
    if main_data:
        for venue_data in main_data:
            total_pfof_usd += venue_data.get('total_usd', 0)
            total_estimated_volume += venue_data.get('estimated_volume', 0)
            virtu_venues.append(venue_data.get('venues', 'Unknown'))
    
    # Get ATS data
    total_ats_shares = 0
    total_ats_trades = 0
    ats_names = []
    
    if context_data:
        for ats_data in context_data:
            total_ats_shares += ats_data.get('total_ats_shares', 0)
            total_ats_trades += ats_data.get('total_ats_trades', 0)
            ats_names.append(ats_data.get('ats_name', 'Unknown'))
    
    # Format numbers
    total_pfof_formatted = f"${total_pfof_usd:,.2f}" if total_pfof_usd else "$0"
    total_ats_shares_formatted = f"{total_ats_shares:,}" if total_ats_shares else "0"
    total_ats_trades_formatted = f"{total_ats_trades:,}" if total_ats_trades else "0"
    total_estimated_volume_formatted = f"{total_estimated_volume:,.0f}" if total_estimated_volume else "0"
    
    # Build response
    time_period = f"Q{quarter} {year}" if quarter else f"{year}"
    
    response = f"""**Virtu Analysis for {time_period}**

**PFOF Data (executing_bd_606):**
- Total PFOF Payments: {total_pfof_formatted}
- Estimated Volume: {total_estimated_volume_formatted} shares
- Virtu Venues: {', '.join(virtu_venues) if virtu_venues else 'None found'}

**ATS Data (finra_ats):**
- Total ATS Shares: {total_ats_shares_formatted}
- Total ATS Trades: {total_ats_trades_formatted}
- Virtu ATS Names: {', '.join(ats_names) if ats_names else 'None found'}

**Summary:**
In {time_period}, Virtu-operated ATS executed {total_ats_shares_formatted} shares across {len(ats_names)} ATS platforms."""
    
    return response

# -----------------------------
# Complex Multi-Table Query Handler (Separate Queries + OpenAI Synthesis)
# -----------------------------

def generate_complex_multi_table_query(user_input: str, query_tags: Dict) -> Dict:
    """Generate complex multi-table query using separate queries + OpenAI synthesis"""
    
    print("🔗 Complex multi-table query detected - using separate queries + OpenAI synthesis")
    
    # Determine which tables to query based on classification
    queries_to_execute = []
    
    # Always query executing_bd_606 for PFOF data
    if query_tags.get('mentions_pfof') or query_tags.get('mentions_volume'):
        queries_to_execute.append({
            'name': 'pfof_data',
            'description': 'PFOF payment data from executing_bd_606',
            'query': generate_pfof_query(query_tags)
        })
    
    # Query monthly_data for market context
    if query_tags.get('mentions_trend') or query_tags.get('mentions_month'):
        queries_to_execute.append({
            'name': 'market_data',
            'description': 'Market volume data from monthly_data',
            'query': generate_market_data_query(query_tags)
        })
    
    # Query finra_ats for ATS data
    if query_tags.get('mentions_ats'):
        queries_to_execute.append({
            'name': 'ats_data',
            'description': 'ATS trading data from finra_ats',
            'query': generate_ats_query(query_tags)
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
            query_results[query_info['name']] = {
                'description': query_info['description'],
                'query': query_info['query'],
                'error': str(e),
                'row_count': 0
            }
    
    # Generate OpenAI synthesis
    synthesis = generate_openai_synthesis(user_input, query_results, query_tags)
    
    return {
        "question": user_input,
        "query_type": "complex_multi_table",
        "query_results": query_results,
        "synthesis": synthesis,
        "query_classification": query_tags
    }

def generate_pfof_query(query_tags: Dict) -> str:
    """Generate PFOF query"""
    where_conditions = ["data_type = 'venue'"]
    
    if query_tags.get('year'):
        where_conditions.append(f"year = {query_tags['year']}")
    
    if query_tags.get('month'):
        where_conditions.append(f"month = '{query_tags['month']}'")
    
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

def generate_market_data_query(query_tags: Dict) -> str:
    """Generate market data query"""
    where_conditions = []
    
    if query_tags.get('year'):
        where_conditions.append(f"EXTRACT(YEAR FROM day) = {query_tags['year']}")
    
    if query_tags.get('month'):
        where_conditions.append(f"EXTRACT(MONTH FROM day) = {query_tags['month']}")
    
    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
    
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

    User Question: "{user_input}"

    Query Results:
    {json.dumps(data_summary, indent=2)}

    Please provide:
    1. A direct answer to the user's question
    2. Key insights from the data
    3. Context and analysis
    4. Any relevant trends or patterns

    Be specific with numbers and provide actionable insights.
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

def is_virtu_ats_query(query_tags: Dict) -> bool:
    """Determine if this is a Virtu ATS query (executing_bd_606 + finra_ats)"""
    
    # Check if query mentions Virtu
    mentions_virtu = query_tags.get('mentions_virtu', False)
    
    # Check for time context
    has_time = query_tags.get('mentions_month') or query_tags.get('mentions_year') or query_tags.get('mentions_quarter') or query_tags.get('year') or query_tags.get('month')
    
    # Virtu ATS pattern: mentions Virtu + time context
    return mentions_virtu and has_time

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
    
    if is_virtu_ats_query(query_tags):
        print("🔗 Routing to Virtu ATS handler")
        return execute_virtu_ats_query(user_input, query_tags)
    elif is_simple_two_table_query(query_tags):
        print("🔗 Routing to two-table handler")
        return execute_time_based_volume_query(user_input, query_tags)
    elif is_complex_multi_table_query(query_tags):
        print("🔗 Routing to complex multi-table handler")
        return generate_complex_multi_table_query(user_input, query_tags)
    else:
        print("🔗 Routing to single-table handler (fallback)")
        # Fallback to existing single-table logic
        return {"error": "Single-table queries not implemented in this handler"}

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
