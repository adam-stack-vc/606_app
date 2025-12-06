import os
import re
import json
from openai import OpenAI
from db import get_db_connection
from aws_config import config
import pandas as pd
from cross_table_enrichment import enrich_with_monthly_data

# Initialize OpenAI client with AWS Secrets Manager or local .env
client = OpenAI(api_key=config.get('OPENAI_API_KEY'))

# Get absolute path to prompt.txt relative to query.py
prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")

# Read the file contents into SYSTEM_PROMPT
with open(prompt_path, "r") as f:
    SYSTEM_PROMPT = f.read()

# Load broker aliases
broker_aliases_path = os.path.join(os.path.dirname(__file__), "executing_bd_aliases.json")
with open(broker_aliases_path, "r") as f:
    broker_aliases = json.load(f).get("executing_bd_map", {})

# Load venue aliases
venue_aliases_path = os.path.join(os.path.dirname(__file__), "venue_aliases.json")
with open(venue_aliases_path, "r") as f:
    venue_aliases = json.load(f).get("venue_map", {})

def sanitize_sql_output(sql: str) -> str:
    """Remove markdown, explanations, and extract just the SQL query"""
    # Remove markdown code fences and get the SQL
    if "```" in sql:
        parts = sql.split("```")
        sql_candidates = [s for s in parts if "select" in s.lower()]
        if sql_candidates:
            sql = sql_candidates[0]
    
    # Remove leading "sql" language identifier
    if sql.lower().startswith("sql\n"):
        sql = sql[4:]
    
    # Extract everything from SELECT onwards
    if "select" in sql.lower():
        sql = sql[sql.lower().find("select"):]
    
    # Remove any leading explanatory text before SELECT
    sql = re.sub(r'^.*?(?=SELECT)', '', sql, flags=re.IGNORECASE | re.DOTALL)
    
    return sql.strip()

def resolve_aliases_in_sql(sql: str) -> str:
    """Replace broker and venue aliases with canonical names in SQL"""
    
    # Replace broker aliases: executing_bd = 'something'
    broker_pattern = r"executing_bd\s*=\s*'([^']+)'"
    
    def replace_broker(match):
        broker_name = match.group(1)
        broker_lower = broker_name.lower()
        
        # Check if it's an alias
        for canonical, aliases in broker_aliases.items():
            if broker_lower in [a.lower() for a in aliases]:
                return f"executing_bd = '{canonical}'"
        
        # Not an alias, return as-is
        return match.group(0)
    
    sql = re.sub(broker_pattern, replace_broker, sql, flags=re.IGNORECASE)
    
    # Replace venue aliases: venues = 'something'
    venue_pattern = r"venues\s*=\s*'([^']+)'"
    
    def replace_venue(match):
        venue_name = match.group(1)
        venue_lower = venue_name.lower()
        
        # Check if it's an alias
        for canonical, aliases in venue_aliases.items():
            if venue_lower in [a.lower() for a in aliases]:
                return f"venues = '{canonical}'"
        
        # Not an alias, return as-is
        return match.group(0)
    
    sql = re.sub(venue_pattern, replace_venue, sql, flags=re.IGNORECASE)
    
    return sql

def run_query_from_nl(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Translate this to SQL: {prompt}"}
        ]
    )
    raw_sql = response.choices[0].message.content.strip()
    
    # Clean the SQL to remove markdown, explanations, etc.
    sql = sanitize_sql_output(raw_sql)
    
    # Resolve broker and venue aliases
    sql = resolve_aliases_in_sql(sql)
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        # Clean results using pandas
        df = pd.DataFrame(rows, columns=columns)
        df.dropna(inplace=True)
        df.drop_duplicates(inplace=True)
        df = df[df.apply(lambda row: all(str(v).strip() != '' for v in row), axis=1)]

        cleaned_results = df.to_dict(orient="records")

        # Enrich with monthly_data context (non-blocking)
        # Set debug=True to see enrichment errors, False to hide them
        enrichment_result = None
        insights = []
        
        try:
            enriched = enrich_with_monthly_data(sql, cleaned_results, debug=True)
            
            # Only include enrichment if it succeeded and has data
            if enriched.get("has_enrichment"):
                enrichment_result = enriched
                insights = enriched.get("insights", [])
            
            # In debug mode, include enrichment errors even if primary query succeeded
            elif enriched.get("enrichment_failed"):
                enrichment_result = {
                    "debug_info": "Enrichment failed but primary query succeeded",
                    "error": enriched.get("enrichment_error")
                }
        except Exception as e:
            # Double safety: if enrichment module itself fails, catch it here
            enrichment_result = {
                "debug_info": "Enrichment module exception",
                "error": str(e)
            }
        
        return {
            "sql": sql,
            "results": cleaned_results,
            "enrichment": enrichment_result,
            "insights": insights
        }
       
    except Exception as e:
        return {"sql": sql, "raw_sql": raw_sql, "error": str(e)}
    finally:
        cur.close()
        conn.close()