import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Load DB credentials from .env
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Connect and inspect schemas + tables
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()

    print("📌 Connected to:", DB_HOST)
    print("📦 Database:", DB_NAME)

    # List all schemas
    print("\n📚 Available schemas:")
    cur.execute("SELECT schema_name FROM information_schema.schemata;")
    for row in cur.fetchall():
        print("-", row[0])

    # List all tables in all schemas (filtering to yours)
    print("\n📄 Tables matching 'executing_bd_606':")
    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name ILIKE '%executing_bd_606%'
        ORDER BY table_schema;
    """)
    rows = cur.fetchall()
    if not rows:
        print("⚠️  No matching tables found.")
    else:
        for schema, table in rows:
            print(f"✅ {schema}.{table}")

    cur.close()
    conn.close()

except Exception as e:
    print("❌ Failed to connect or query the database:", e)
