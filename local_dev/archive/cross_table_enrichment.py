"""
Cross-table enrichment module

Automatically enriches executing_bd query results with context from monthly_data.
When a query returns results for a specific time period, this module:
1. Extracts the time period from the query/results
2. Aggregates monthly_data for that period
3. Compares with other periods to add context
4. Returns enriched insights
"""

import re
import pandas as pd
import warnings
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from db import get_db_connection

# Suppress pandas SQLAlchemy warnings
warnings.filterwarnings('ignore', message='pandas only supports SQLAlchemy')


def extract_time_period(sql: str, results: List[Dict]) -> Optional[Tuple[int, Optional[int]]]:
    """
    Extract year and optionally month from SQL query or results
    
    Returns: (year, month) or (year, None) or None
    """
    # Try to extract from SQL WHERE clause
    # Pattern: year = 2024, month = 5, etc.
    year_match = re.search(r'year\s*=\s*(\d{4})', sql, re.IGNORECASE)
    month_match = re.search(r'month\s*=\s*(\d{1,2})', sql, re.IGNORECASE)
    
    if year_match:
        year = int(year_match.group(1))
        month = int(month_match.group(1)) if month_match else None
        return (year, month)
    
    # Try to extract from results if they contain date columns
    if results and isinstance(results, list) and len(results) > 0:
        first_result = results[0]
        
        # Look for year/month columns (handle string months too)
        if 'year' in first_result:
            year = first_result['year']
            month = first_result.get('month')
            if month:
                month = int(str(month))  # Handle both int and string months
            return (int(year), month if month else None)
        
        # If only month is in results, try to get year from SQL
        if 'month' in first_result and year_match:
            year = int(year_match.group(1))
            month = int(str(first_result['month']))
            return (year, month)
        
        # Look for date columns
        for key in ['date', 'month', 'day', 'period']:
            if key in first_result:
                try:
                    date_val = first_result[key]
                    if isinstance(date_val, str):
                        date_obj = datetime.strptime(date_val, '%Y-%m-%d')
                        return (date_obj.year, date_obj.month)
                except:
                    continue
    
    return None


def get_monthly_volume_stats(year: int, month: Optional[int] = None) -> Dict:
    """
    Get aggregated trading volume statistics from monthly_data for a given period
    
    Args:
        year: Year to analyze
        month: Optional specific month (1-12)
    
    Returns:
        Dictionary with volume statistics
    """
    conn = get_db_connection()
    
    try:
        # Build date filter
        if month:
            date_filter = f"EXTRACT(YEAR FROM day) = {year} AND EXTRACT(MONTH FROM day) = {month}"
            period_label = f"{year}-{month:02d}"
        else:
            date_filter = f"EXTRACT(YEAR FROM day) = {year}"
            period_label = str(year)
        
        # Get aggregate stats for the period
        query = f"""
        SELECT 
            '{period_label}' as period,
            SUM(total_shares) as total_shares,
            SUM(total_notional) as total_notional,
            SUM(total_trade_count) as total_trade_count,
            SUM(tape_a_shares) as tape_a_shares,
            SUM(tape_b_shares) as tape_b_shares,
            SUM(tape_c_shares) as tape_c_shares
        FROM monthly_data
        WHERE {date_filter}
        """
        
        df = pd.read_sql(query, conn)
        
        if df.empty:
            return None
        
        result = df.iloc[0].to_dict()
        
        # Get ranking compared to other periods
        if month:
            # Compare with other months in the same year
            comparison_query = f"""
            SELECT 
                EXTRACT(MONTH FROM day) as month,
                SUM(total_shares) as total_shares,
                SUM(total_notional) as total_notional,
                SUM(total_trade_count) as total_trade_count
            FROM monthly_data
            WHERE EXTRACT(YEAR FROM day) = {year}
            GROUP BY EXTRACT(MONTH FROM day)
            ORDER BY total_shares DESC
            """
        else:
            # Compare with other years
            comparison_query = """
            SELECT 
                EXTRACT(YEAR FROM day) as year,
                SUM(total_shares) as total_shares,
                SUM(total_notional) as total_notional,
                SUM(total_trade_count) as total_trade_count
            FROM monthly_data
            GROUP BY EXTRACT(YEAR FROM day)
            ORDER BY total_shares DESC
            """
        
        comparison_df = pd.read_sql(comparison_query, conn)
        
        # Calculate rankings
        if month:
            result['month_rank_by_shares'] = int(comparison_df[comparison_df['month'] == month].index[0] + 1)
            result['total_months'] = len(comparison_df)
        else:
            result['year_rank_by_shares'] = int(comparison_df[comparison_df['year'] == year].index[0] + 1)
            result['total_years'] = len(comparison_df)
        
        # Add comparison insights
        result['is_highest_volume'] = result.get('month_rank_by_shares', result.get('year_rank_by_shares', 999)) == 1
        result['is_top_3'] = result.get('month_rank_by_shares', result.get('year_rank_by_shares', 999)) <= 3
        
        return result
        
    finally:
        conn.close()


def generate_context_insights(monthly_stats: Dict, month: Optional[int] = None) -> List[str]:
    """
    Generate human-readable insights from monthly_data statistics
    
    Args:
        monthly_stats: Dictionary of statistics from get_monthly_volume_stats
        month: Optional month number
    
    Returns:
        List of insight strings to add to the response
    """
    insights = []
    
    if not monthly_stats:
        return insights
    
    period = monthly_stats.get('period', 'this period')
    
    # Volume insights
    if monthly_stats.get('is_highest_volume'):
        if month:
            insights.append(f"📊 {period} had the **highest equity trading volume** of the year")
        else:
            insights.append(f"📊 {period} had the **highest equity trading volume** across all years in the database")
    elif monthly_stats.get('is_top_3'):
        rank = monthly_stats.get('month_rank_by_shares', monthly_stats.get('year_rank_by_shares'))
        if month:
            insights.append(f"📊 {period} ranked **#{rank}** in equity trading volume for the year")
        else:
            insights.append(f"📊 {period} ranked **#{rank}** in equity trading volume across all years")
    
    # Format large numbers
    total_shares = monthly_stats.get('total_shares')
    if total_shares:
        shares_billions = float(total_shares) / 1_000_000_000
        insights.append(f"📈 Total market volume: **{shares_billions:.2f}B shares** traded")
    
    total_notional = monthly_stats.get('total_notional')
    if total_notional:
        notional_trillions = float(total_notional) / 1_000_000_000_000
        insights.append(f"💰 Total notional value: **${notional_trillions:.2f}T**")
    
    # Tape breakdown
    tape_a = monthly_stats.get('tape_a_shares')
    tape_b = monthly_stats.get('tape_b_shares')
    tape_c = monthly_stats.get('tape_c_shares')
    
    if tape_a and tape_b and tape_c and total_shares:
        tape_a_pct = (float(tape_a) / float(total_shares)) * 100
        tape_c_pct = (float(tape_c) / float(total_shares)) * 100
        insights.append(f"📊 Tape breakdown: NYSE {tape_a_pct:.1f}% | NASDAQ {tape_c_pct:.1f}%")
    
    return insights


def enrich_with_monthly_data(sql: str, results: List[Dict], debug: bool = True) -> Dict:
    """
    Main enrichment function: adds monthly_data context to query results
    
    This function is NON-BLOCKING - if it fails, it returns safely without affecting
    the primary query results.
    
    Args:
        sql: The executed SQL query
        results: Query results
        debug: If True, include error details in response
    
    Returns:
        Dictionary with:
        - original_results: The original query results
        - monthly_context: Statistics from monthly_data
        - insights: Human-readable insights
        - has_enrichment: Boolean indicating if enrichment was added
        - error: Error message if enrichment failed (only if debug=True)
    """
    try:
        # Extract time period from query
        time_period = extract_time_period(sql, results)
        
        if not time_period:
            return {
                "original_results": results,
                "monthly_context": None,
                "insights": [],
                "has_enrichment": False
            }
        
        year, month = time_period
        
        # Get monthly data statistics
        monthly_stats = get_monthly_volume_stats(year, month)
        
        # Generate insights
        insights = generate_context_insights(monthly_stats, month) if monthly_stats else []
        
        return {
            "original_results": results,
            "monthly_context": monthly_stats,
            "insights": insights,
            "has_enrichment": bool(monthly_stats),
            "time_period": {"year": year, "month": month}
        }
    
    except Exception as e:
        # Non-blocking: return safely even if enrichment fails
        error_response = {
            "original_results": results,
            "monthly_context": None,
            "insights": [],
            "has_enrichment": False
        }
        
        # Include error details in debug mode
        if debug:
            error_response["enrichment_error"] = str(e)
            error_response["enrichment_failed"] = True
        
        return error_response


def format_enriched_response(enriched_data: Dict) -> str:
    """
    Format enriched data into a user-friendly response
    
    Args:
        enriched_data: Output from enrich_with_monthly_data
    
    Returns:
        Formatted string for display
    """
    parts = []
    
    # Original results summary
    results = enriched_data.get("original_results", [])
    if results:
        parts.append(f"**Query Results:** {len(results)} record(s) found")
    
    # Add insights
    insights = enriched_data.get("insights", [])
    if insights:
        parts.append("\n**Market Context:**")
        for insight in insights:
            parts.append(f"  {insight}")
    
    return "\n".join(parts)

