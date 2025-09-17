# query.py

from fastapi import HTTPException
from openai import OpenAI
import os
import pandas as pd

from app.db import get_db_connection
from app.query_framework import (
    build_system_prompt,
    classify_query,
    clean_and_dedup,
    load_schema_from_json,
    generate_volume_estimation_query,
    sanitize_sql_output,
    DEFAULT_GUIDANCE_RULES
)

# Load schema and build prompt
SCHEMA = load_schema_from_json()
SYSTEM_PROMPT = build_system_prompt(SCHEMA, DEFAULT_GUIDANCE_RULES)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def run_query_from_nl(prompt: str):
    tags = classify_query(prompt)
    print(f"🏷️  Detected tags: {tags}")

    year = tags.get("year", 2024)
    stock_group = tags.get("stock_group", "SP500")
    executing_bd = tags.get("executing_bd")

    sql = ""
    cur = None
    conn = None

    try:
        # Custom logic router
        if tags.get("mentions_volume"):
            sql = generate_volume_estimation_query(year=year, stock_group=stock_group, executing_bd=executing_bd)
            print("🔁 Routed to: generate_volume_estimation_query")
        else:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Translate this to SQL: {prompt}"}
                ]
            )
            raw_sql = response.choices[0].message.content
            sql = sanitize_sql_output(raw_sql)
            print("🧠 Final sanitized SQL:\n", sql)

        # Execute the SQL
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

        df = pd.DataFrame(rows, columns=columns)

        # Clean
        if not df.empty:
            df = clean_and_dedup(df)

        return {"sql": sql, "results": df.to_dict(orient="records")}

    except Exception as e:
        return {"sql": sql, "error": str(e)}

    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except:
            pass
