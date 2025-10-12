import psycopg2
from aws_config import config

def get_db_connection():
    """
    Create database connection using AWS Secrets Manager or local .env
    """
    return psycopg2.connect(
        host=config.get('DB_HOST'),
        database=config.get('DB_NAME'),
        user=config.get('DB_USER'),
        password=config.get('DB_PASSWORD'),
        port=config.get('DB_PORT', 5432),
    )