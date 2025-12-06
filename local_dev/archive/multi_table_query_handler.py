# Enhanced Multi-Table Query Handler

def detect_multi_table_query(query_tags: Dict, relevant_tables: List[str]) -> bool:
    """Detect if a query requires multiple tables with JOINs"""
    
    # Multi-table indicators
    multi_table_patterns = [
        # Cross-table comparisons
        query_tags.get('mentions_trend') and len(relevant_tables) > 2,
        # Market share analysis
        query_tags.get('mentions_volume') and query_tags.get('mentions_pfof'),
        # Time-based cross-table analysis
        query_tags.get('mentions_month') and len(relevant_tables) > 2,
        # Venue performance across tables
        query_tags.get('mentions_venue') and query_tags.get('mentions_trend'),
    ]
    
    return any(multi_table_patterns) or len(relevant_tables) > 2

def generate_multi_table_query(user_input: str, query_tags: Dict, relevant_tables: List[str]) -> str:
    """Generate SQL for queries requiring multiple tables"""
    
    # Define common JOIN patterns
    join_patterns = {
        ('executing_bd_606', 'monthly_data'): {
            'condition': 'e.year = EXTRACT(YEAR FROM m.day) AND e.month = EXTRACT(MONTH FROM m.day)::text',
            'alias_e': 'e',
            'alias_m': 'm'
        },
        ('executing_bd_606', 'venue_mapping'): {
            'condition': 'e.venues = vm.canonical_name',
            'alias_e': 'e', 
            'alias_vm': 'vm'
        },
        ('monthly_data', 'venue_mapping'): {
            'condition': 'm.market_participant = vm.canonical_name',
            'alias_m': 'm',
            'alias_vm': 'vm'
        },
        ('finra_ats', 'venue_mapping'): {
            'condition': 'f.ats_name = vm.canonical_name',
            'alias_f': 'f',
            'alias_vm': 'vm'
        }
    }
    
    # Build JOIN clauses
    joins = []
    table_aliases = {}
    
    # Start with primary table
    primary_table = relevant_tables[0] if relevant_tables else 'executing_bd_606'
    table_aliases[primary_table] = primary_table[0]  # First letter as alias
    
    # Add JOINs for other tables
    for table in relevant_tables[1:]:
        alias = table[0]  # First letter as alias
        table_aliases[table] = alias
        
        # Find appropriate JOIN pattern
        join_key = (primary_table, table) if (primary_table, table) in join_patterns else (table, primary_table)
        if join_key in join_patterns:
            pattern = join_patterns[join_key]
            joins.append(f"JOIN {table} {alias} ON {pattern['condition']}")
    
    # Build WHERE conditions based on query classification
    where_conditions = []
    
    if query_tags.get('mentions_pfof'):
        where_conditions.append("e.data_type = 'venue'")
    
    if query_tags.get('year'):
        where_conditions.append(f"e.year = {query_tags['year']}")
    
    if query_tags.get('mentions_venue'):
        # Extract venue name from user input
        venue = extract_venue_from_input(user_input)
        if venue:
            where_conditions.append(f"e.venues = '{venue}'")
    
    # Build SELECT clause based on query type
    select_clauses = []
    
    if query_tags.get('mentions_volume') and query_tags.get('mentions_pfof'):
        # Market share analysis
        select_clauses.extend([
            "e.executing_bd",
            "SUM(e.netpmtpaidrecvmarketordersusd) as total_pfof_usd",
            "m.total_shares",
            "ROUND(SUM(e.netpmtpaidrecvmarketordersusd) / NULLIF(m.total_shares, 0) * 100, 2) as market_share_pct"
        ])
    elif query_tags.get('mentions_trend'):
        # Trend analysis
        select_clauses.extend([
            "e.month",
            "e.year", 
            "SUM(e.netpmtpaidrecvmarketordersusd) as total_pfof",
            "m.total_shares as market_volume"
        ])
    else:
        # Default multi-table query
        select_clauses.extend([
            "e.executing_bd",
            "e.venues",
            "SUM(e.netpmtpaidrecvmarketordersusd) as total_pfof",
            "m.total_shares"
        ])
    
    # Build GROUP BY
    group_by_fields = []
    if query_tags.get('mentions_volume') and query_tags.get('mentions_pfof'):
        group_by_fields = ["e.executing_bd", "m.total_shares"]
    elif query_tags.get('mentions_trend'):
        group_by_fields = ["e.month", "e.year", "m.total_shares"]
    else:
        group_by_fields = ["e.executing_bd", "e.venues"]
    
    # Construct final SQL
    sql = f"""
SELECT 
    {', '.join(select_clauses)}
FROM {primary_table} {table_aliases[primary_table]}
{' '.join(joins)}
WHERE {' AND '.join(where_conditions) if where_conditions else '1=1'}
GROUP BY {', '.join(group_by_fields)}
ORDER BY total_pfof DESC
LIMIT 10;
"""
    
    return sql.strip()

def extract_venue_from_input(user_input: str) -> str:
    """Extract venue name from user input"""
    # This would use the venue resolution logic
    from multi_table_query_framework import resolve_venue_from_db
    return resolve_venue_from_db(user_input)

# Enhanced routing in ask606_multi_table.py
def ask_multi_table_enhanced(question: str):
    """Enhanced ask function with full multi-table support"""
    
    # Load all schemas
    all_schemas = load_all_schemas()
    
    # Route the query to get targeted system prompt and relevant tables
    system_prompt, relevant_tables = route_query(question, all_schemas)
    
    # Classify the query
    query_tags = classify_query_enhanced(question)
    
    print(f"🔍 Query Classification: {query_tags}")
    print(f"📊 Relevant Tables: {relevant_tables}")
    
    # Check if this requires multi-table handling
    if detect_multi_table_query(query_tags, relevant_tables):
        print("🔗 Multi-table query detected - using custom multi-table handler")
        sql = generate_multi_table_query(question, query_tags, relevant_tables)
        print(f"Generated Multi-Table SQL: \n{sql}")
    elif query_tags.get("mentions_volume"):
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
    
    # Rest of the function remains the same...
    # (execute SQL, format results, etc.)
