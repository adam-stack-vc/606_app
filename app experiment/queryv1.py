import os
from dotenv import load_dotenv
from openai import OpenAI
from app.db import get_db_connection
import pandas as pd


# 🔑 Load .env file BEFORE using os.getenv
load_dotenv()

# ✅ Now this will correctly grab your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Get absolute path to prompt.txt relative to query.py
prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")

# Read the file contents into SYSTEM_PROMPT
with open(prompt_path, "r") as f:
    SYSTEM_PROMPT = f.read()

def run_query_from_nl(prompt: str):
    response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Translate this to SQL: {prompt}"}
    ]
)
    sql = response.choices[0].message.content.strip()

    
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall()

         # 🧼 Clean results using pandas
        df = pd.DataFrame(rows, columns=columns)
        df.dropna(inplace=True)                    # Remove rows with any nulls
        df.drop_duplicates(inplace=True)           # Remove exact duplicates
        df = df[df.apply(lambda row: all(str(v).strip() != '' for v in row), axis=1)]  # Remove blanks

        cleaned_results = df.to_dict(orient="records")

        return {
            "sql": sql,
            "results": cleaned_results
        }
       
    except Exception as e:
        return {"sql": sql, "error": str(e)}
    finally:
        cur.close()
        conn.close()
