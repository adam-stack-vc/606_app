# ask606_hybrid.py

from openai import OpenAI
import psycopg2
import os
from dotenv import load_dotenv
from hybrid_query_handler import (
    route_hybrid_query,
    is_simple_two_table_query,
    is_complex_multi_table_query,
    is_virtu_ats_query
)
from multi_table_query_framework import classify_query_enhanced

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

def ask_hybrid(question: str):
    """Hybrid ask function that routes queries to appropriate handlers"""
    
    # Classify the query
    query_tags = classify_query_enhanced(question)
    
    print(f"🔍 Query Classification: {query_tags}")
    
    # Route to appropriate handler
    if is_virtu_ats_query(query_tags):
        print("🔗 Routing to Virtu ATS handler")
        result = route_hybrid_query(question, query_tags)
        
        # Format response for API
        return {
            "question": question,
            "sql": result.get("main_query", ""),
            "context_sql": result.get("context_query", ""),
            "results": result.get("main_results", []),
            "context_results": result.get("context_results", []),
            "response": result.get("response", ""),
            "query_type": "two_table_virtu_ats",
            "query_classification": query_tags,
            "row_count": len(result.get("main_results", []))
        }
        
    elif is_simple_two_table_query(query_tags):
        print("🔗 Routing to two-table handler")
        result = route_hybrid_query(question, query_tags)
        
        # Format response for API
        return {
            "question": question,
            "sql": result.get("main_query", ""),
            "context_sql": result.get("context_query", ""),
            "results": result.get("main_results", []),
            "context_results": result.get("context_results", []),
            "response": result.get("response", ""),
            "query_type": "two_table_time_based",
            "query_classification": query_tags,
            "row_count": len(result.get("main_results", []))
        }
        
    elif is_complex_multi_table_query(query_tags):
        print("🔗 Routing to complex multi-table handler")
        result = route_hybrid_query(question, query_tags)
        
        # Format response for API
        return {
            "question": question,
            "sql": "Multiple queries executed",
            "query_results": result.get("query_results", {}),
            "response": result.get("synthesis", ""),
            "query_type": "complex_multi_table",
            "query_classification": query_tags,
            "row_count": sum(r.get("row_count", 0) for r in result.get("query_results", {}).values())
        }
        
    else:
        print("🔗 Routing to single-table handler (fallback)")
        # Fallback to existing single-table logic
        from ask606 import ask
        result = ask(question)
        
        # Ensure result is a dict, not a list
        if isinstance(result, list):
            return {
                "question": question,
                "sql": "Single table query",
                "results": result,
                "response": f"Found {len(result)} results",
                "query_type": "single_table_fallback",
                "query_classification": query_tags,
                "row_count": len(result)
            }
        else:
            return result

# Backward compatibility function
def ask(question: str):
    """Backward compatibility - uses hybrid framework"""
    return ask_hybrid(question)

if __name__ == "__main__":
    # Test the hybrid framework
    test_questions = [
        "What venue received the most volume in January 2024?",  # Two-table
        "Compare all brokers' PFOF performance and market trends for 2024",  # Complex
        "What is the volume for citadel?",  # Single-table fallback
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print('='*60)
        result = ask_hybrid(question)
        print(f"Query Type: {result.get('query_type', 'N/A')}")
        print(f"Response: {result.get('response', 'N/A')}")
        if result.get('error'):
            print(f"Error: {result['error']}")
        print()
