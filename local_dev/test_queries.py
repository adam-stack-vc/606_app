#!/usr/bin/env python3
"""
Test script to validate prompt and query generation
"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
import re

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Read the prompt
with open("prompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

def sanitize_sql_output(sql: str) -> str:
    """Remove markdown, explanations, and extract just the SQL query"""
    if "```" in sql:
        parts = sql.split("```")
        sql_candidates = [s for s in parts if "select" in s.lower()]
        if sql_candidates:
            sql = sql_candidates[0]
    
    if sql.lower().startswith("sql\n"):
        sql = sql[4:]
    
    if "select" in sql.lower():
        sql = sql[sql.lower().find("select"):]
    
    sql = re.sub(r'^.*?(?=SELECT)', '', sql, flags=re.IGNORECASE | re.DOTALL)
    
    return sql.strip()

def test_question(question: str):
    """Test a single question and return the generated SQL"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Translate this to SQL: {question}"}
        ]
    )
    raw_sql = response.choices[0].message.content.strip()
    clean_sql = sanitize_sql_output(raw_sql)
    return clean_sql

# Test questions covering different scenarios
TEST_QUESTIONS = [
    # PFOF-related queries
    {
        "category": "PFOF - Single Broker",
        "question": "What month did Robinhood receive the most PFOF in 2024?",
        "expected": "data_type = 'venue'"
    },
    {
        "category": "PFOF - All Brokers",
        "question": "Which broker received the most PFOF in 2024?",
        "expected": "data_type = 'venue'"
    },
    {
        "category": "PFOF - Specific Month",
        "question": "How much PFOF did Robinhood receive in January 2024?",
        "expected": "data_type = 'venue' AND month = '1'"
    },
    
    # Venue queries
    {
        "category": "Venues - List",
        "question": "What venues did Robinhood use in 2024?",
        "expected": "data_type = 'executing_bd'"
    },
    {
        "category": "Venues - Volume",
        "question": "Which venue got the most orders from Robinhood in 2024?",
        "expected": "data_type = 'executing_bd' AND executing_bd = 'Robinhood'"
    },
    
    # Stock group queries
    {
        "category": "Stock Groups",
        "question": "How much PFOF did Robinhood receive for S&P 500 stocks in 2024?",
        "expected": "stock_group = 'SP500' OR stock_group IN ('SP500', 'OtherStocks')"
    },
    {
        "category": "Options",
        "question": "How much PFOF did Robinhood receive for options in 2024?",
        "expected": "stock_group = 'Options'"
    },
    
    # Order type queries
    {
        "category": "Order Types",
        "question": "What percentage of Robinhood's orders were marketable limit orders in 2024?",
        "expected": "marketablelimitpct"
    },
    
    # Broker listing
    {
        "category": "Broker List",
        "question": "Give me a list of all brokers",
        "expected": "SELECT DISTINCT executing_bd"
    },
    
    # Complex queries
    {
        "category": "Complex - Comparison",
        "question": "Which broker had the highest payment rate (cents per hundred) in 2024?",
        "expected": "data_type = 'venue'"
    },
]

def check_sql_quality(sql: str, expected: str) -> dict:
    """Check if SQL meets quality criteria"""
    issues = []
    warnings = []
    
    sql_lower = sql.lower()
    
    # Check for data_type when querying PFOF
    if any(col in sql_lower for col in ['netpmtpaidrecv', 'pfof']):
        if "data_type = 'venue'" not in sql:
            issues.append("❌ Missing data_type = 'venue' for PFOF query")
    
    # Check for month as string
    if 'month =' in sql_lower:
        # Check if month is compared as number (bad)
        if re.search(r"month\s*=\s*\d+(?!')", sql):
            issues.append("❌ Month should be compared as string (month = '1' not month = 1)")
    
    # Check for NULL handling
    if 'where' in sql_lower and 'is not null' not in sql_lower:
        warnings.append("⚠️  Consider adding IS NOT NULL checks")
    
    # More flexible pattern matching - check if all parts of expected are present
    if expected:
        expected_parts = expected.lower().split(' and ')
        for part in expected_parts:
            part = part.strip()
            if part and part not in sql_lower:
                # Only flag as issue if it's a critical pattern
                if 'data_type' in part or 'month' in part:
                    issues.append(f"❌ Expected pattern not found: {part}")
    
    return {
        "issues": issues,
        "warnings": warnings,
        "has_issues": len(issues) > 0
    }

def main():
    print("=" * 80)
    print("Testing Query Generation with Current Prompt")
    print("=" * 80)
    print()
    
    results = []
    
    for i, test in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{i}. [{test['category']}]")
        print(f"   Question: {test['question']}")
        print()
        
        try:
            sql = test_question(test['question'])
            print(f"   Generated SQL:")
            print(f"   {sql}")
            print()
            
            # Check quality
            quality = check_sql_quality(sql, test['expected'])
            
            if quality['has_issues']:
                for issue in quality['issues']:
                    print(f"   {issue}")
                results.append({"test": test, "sql": sql, "passed": False, "issues": quality['issues']})
            else:
                print("   ✅ Query looks good!")
                results.append({"test": test, "sql": sql, "passed": True, "issues": []})
            
            if quality['warnings']:
                for warning in quality['warnings']:
                    print(f"   {warning}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({"test": test, "sql": None, "passed": False, "issues": [str(e)]})
        
        print("-" * 80)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if total - passed > 0:
        print("\n❌ Failed Tests:")
        for r in results:
            if not r['passed']:
                print(f"\n  • {r['test']['question']}")
                for issue in r['issues']:
                    print(f"    {issue}")
    
    print()

if __name__ == "__main__":
    main()

