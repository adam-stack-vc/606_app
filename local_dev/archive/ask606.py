from openai import OpenAI
import psycopg2
import os
from dotenv import load_dotenv
from query_framework import (
    load_schema_from_json, 
    build_system_prompt, 
    DEFAULT_GUIDANCE_RULES,
    classify_query,
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

# Function to ask question
def ask(question):
    # Load schema and build system prompt
    schema_doc = load_schema_from_json()
    system_prompt = build_system_prompt(schema_doc, DEFAULT_GUIDANCE_RULES)
    
    # Classify the query to detect volume-related queries
    query_tags = classify_query(question)
    
    # Check if this is a volume query and route to custom function
    if query_tags.get("mentions_volume", False):
        # Extract parameters from query tags
        year = query_tags.get("year", 2024)
        stock_group = query_tags.get("stock_group", "SP500")
        executing_bd = query_tags.get("executing_bd")
        venue = query_tags.get("venue")
        
        # Determine if query is asking about venues or executing_bd
        # If a venue was resolved from aliases, query by venue
        # Otherwise check if "venue" or "venues" appears in the question
        query_by_venue = venue is not None or "venue" in question.lower() or "venues" in question.lower()
        
        # Generate custom volume estimation query
        sql = generate_volume_estimation_query(
            year=year,
            stock_group=stock_group,
            executing_bd=executing_bd,
            venue=venue,
            query_by_venue=query_by_venue
        )
        print("Generated Volume SQL:", sql)
    else:
        # Use standard OpenAI query generation
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Translate this to SQL: {question}"}
            ]
        )
        sql = response.choices[0].message.content.strip()
        print("Generated SQL:", sql)
    
    # Sanitize the SQL output
    sql = sanitize_sql_output(sql)

    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        return results
    except Exception as e:
        return f"❌ Error running query: {e}"

# Example usage
if __name__ == "__main__":
    question = "Give me a list of all of the unique venue names"
    print(ask(question))
