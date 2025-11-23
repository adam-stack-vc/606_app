from openai import OpenAI
import psycopg2
import os
from dotenv import load_dotenv

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
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": """You are a helpful assistant that translates natural language questions into valid PostgreSQL SQL queries.

Requirements:
- Use only valid PostgreSQL syntax.
- Never use MySQL-style functions like `NOW() - INTERVAL 7 DAY`. Instead, use `NOW() - INTERVAL '7 days'`.
- Do not modify or delete data; read-only queries only.
- Output just the SQL query, no explanations.
- The PostGres schema is one table (executing_bd_606) and columns:
    table_name    |                column_name                |          data_type          
------------------+-------------------------------------------+-----------------------------
 executing_bd_606 | executing_bd                              | character varying
 executing_bd_606 | venues                                    | character varying
 executing_bd_606 | stock_group                               | character varying
 executing_bd_606 | marketablelimitpct                        | numeric
 executing_bd_606 | nonmarketablelimitpct                     | numeric
 executing_bd_606 | otherpct                                  | numeric
 executing_bd_606 | netpmtpaidrecvmarketordersusd             | numeric
 executing_bd_606 | netpmtpaidrecvmarketorderscph             | numeric
 executing_bd_606 | netpmtpaidrecvmarketablelimitordersusd    | numeric
 executing_bd_606 | netpmtpaidrecvmarketablelimitorderscph    | numeric
 executing_bd_606 | netpmtpaidrecvnonmarketablelimitordersusd | numeric
 executing_bd_606 | netpmtpaidrecvnonmarketablelimitorderscph | numeric
 executing_bd_606 | netpmtpaidrecvotherordersusd              | numeric
 executing_bd_606 | netpmtpaidrecvotherorderscph              | numeric
 executing_bd_606 | materialaspects                           | text
 executing_bd_606 | month                                     | numeric
 executing_bd_606 | year                                      | integer
 executing_bd_606 | created_at                                | timestamp without time zone
 executing_bd_606 | ndopct                                    | numeric
 executing_bd_606 | ndomarketpct                              | numeric
 executing_bd_606 | ndomarketablelimitpct                     | numeric
 executing_bd_606 | ndononmarketablelimitpct                  | numeric
 executing_bd_606 | ndootherpct                               | numeric
 executing_bd_606 | orderpct                                  | numeric
 executing_bd_606 | marketpct                                 | numeric
 executing_bd_606 | data_type                                 | character varying
"""
            },
            {
                "role": "user",
                "content": f"Translate this to SQL: {question}"
            }
        ]
    )

    sql = response.choices[0].message.content.strip()
    print("Generated SQL:", sql)

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
