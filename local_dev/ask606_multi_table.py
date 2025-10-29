# ask606_multi_table.py

from openai import OpenAI
import psycopg2
import os
from dotenv import load_dotenv
from multi_table_query_framework import (
    load_all_schemas,
    route_query,
    classify_query_enhanced,
    generate_volume_estimation_query,
    sanitize_sql_output
)

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
    
    # Sanitize the SQL
    sql = sanitize_sql_output(sql)
    
    try:
        # Execute the query
        cursor.execute(sql)
        results = cursor.fetchall()
        
        # Get column names
        column_names = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Format results
        if results:
            formatted_results = []
            for row in results:
                formatted_results.append(dict(zip(column_names, row)))
            
            return {
                "question": question,
                "sql": sql,
                "results": formatted_results,
                "row_count": len(formatted_results),
                "relevant_tables": relevant_tables,
                "query_classification": query_tags
            }
        else:
            return {
                "question": question,
                "sql": sql,
                "results": [],
                "row_count": 0,
                "message": "No results found",
                "relevant_tables": relevant_tables,
                "query_classification": query_tags
            }
            
    except Exception as e:
        return {
            "question": question,
            "sql": sql,
            "error": str(e),
            "relevant_tables": relevant_tables,
            "query_classification": query_tags
        }

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
