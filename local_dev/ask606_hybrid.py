# ask606_hybrid.py

from openai import OpenAI
import psycopg2
import os
from dotenv import load_dotenv
from hybrid_query_handler import (
    route_hybrid_query
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
conn.autocommit = True
cursor = conn.cursor()

def ask_hybrid(question: str):
    """Hybrid ask that always delegates to the router (complex multi-table)."""
    # Classify first for logging/debug
    query_tags = classify_query_enhanced(question)
    print(f"🔍 Query Classification: {query_tags}")

    # Always use router (which now always returns complex multi-table results)
    result = route_hybrid_query(question, query_tags)

    # If router produced multi-table results
    if isinstance(result, dict) and result.get("query_results") is not None:
        return {
            "question": question,
            "sql": "Multiple queries executed",
            "query_results": result.get("query_results", {}),
            "response": result.get("synthesis", ""),
            "query_type": "complex_multi_table",
            "query_classification": query_tags,
            "row_count": sum(r.get("row_count", 0) for r in result.get("query_results", {}).values())
        }

    # If router returned a two-table style dict
    if isinstance(result, dict) and (result.get("main_query") is not None or result.get("main_results") is not None):
        return {
            "question": question,
            "sql": result.get("main_query", ""),
            "context_sql": result.get("context_query", ""),
            "results": result.get("main_results", []),
            "context_results": result.get("context_results", []),
            "response": result.get("response", ""),
            "query_type": result.get("query_type", "two_table"),
            "query_classification": query_tags,
            "row_count": len(result.get("main_results", []))
        }

    # Final fallback: return whatever the router returned
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
