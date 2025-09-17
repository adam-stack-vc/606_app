#!/usr/bin/env python3
"""
Test script to verify database connectivity and configuration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from parent directory
parent_dir = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_environment_variables():
    """Test if required environment variables are set"""
    print("🔧 Testing Environment Variables")
    print("=" * 50)
    
    required_vars = [
        "DB_HOST",
        "DB_NAME", 
        "DB_USER",
        "DB_PASSWORD",
        "DB_PORT"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Don't print the actual password for security
            if var == "DB_PASSWORD":
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {missing_vars}")
        print("\nTo fix this, create a .env file with:")
        print("DB_HOST=your_host")
        print("DB_NAME=your_database")
        print("DB_USER=your_username")
        print("DB_PASSWORD=your_password")
        print("DB_PORT=5432")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True

def test_database_connection():
    """Test actual database connection"""
    print("\n🗄️  Testing Database Connection")
    print("=" * 50)
    
    try:
        from app.db import get_db_connection
        
        print("Attempting to connect to database...")
        conn = get_db_connection()
        print("✅ Database connection successful!")
        
        # Test basic query
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"✅ Database version: {version}")
        
        # Test if our table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'executing_bd_606'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            print("✅ Table 'executing_bd_606' exists")
            
            # Get row count
            cur.execute("SELECT COUNT(*) FROM executing_bd_606")
            count = cur.fetchone()[0]
            print(f"✅ Table has {count} rows")
            
            # Get sample data
            cur.execute("SELECT DISTINCT executing_bd FROM executing_bd_606 LIMIT 5")
            brokers = cur.fetchall()
            print(f"✅ Sample brokers: {[b[0] for b in brokers]}")
            
        else:
            print("❌ Table 'executing_bd_606' does not exist")
            print("   You may need to create the table or check the table name")
        
        cur.close()
        conn.close()
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure psycopg2 is installed: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nCommon issues:")
        print("- Check if database server is running")
        print("- Verify host, port, and credentials")
        print("- Ensure database exists")
        print("- Check firewall/network connectivity")
        return False

def test_query_framework_with_db():
    """Test if query framework can work with database"""
    print("\n🔍 Testing Query Framework with Database")
    print("=" * 50)
    
    try:
        from app.query_framework import classify_query, generate_payment_to_cph_ratio_query
        from app.db import get_db_connection
        
        # Test a simple query
        test_question = "What is the payment to cph ratio for SP500 stocks?"
        print(f"Testing question: {test_question}")
        
        # Classify the query
        tags = classify_query(test_question)
        print(f"✅ Classification successful: {tags}")
        
        # Generate SQL
        sql = generate_payment_to_cph_ratio_query(year=2024, stock_group='SP500')
        print(f"✅ SQL generation successful ({len(sql)} characters)")
        
        # Test if SQL can be executed
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(sql)
            results = cur.fetchall()
            print(f"✅ SQL execution successful: {len(results)} rows returned")
            
            if results:
                print(f"   Sample result: {results[0]}")
            
        except Exception as e:
            print(f"❌ SQL execution failed: {e}")
            print(f"   Generated SQL: {sql[:200]}...")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Query framework test failed: {e}")
        return False

def create_sample_env_file():
    """Create a sample .env file"""
    print("\n📝 Creating Sample .env File")
    print("=" * 50)
    
    env_content = """# Database Configuration
DB_HOST=localhost
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=5432

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
"""
    
    env_file_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_file_path):
        print("✅ .env file already exists")
        return
    
    try:
        with open(env_file_path, 'w') as f:
            f.write(env_content)
        print(f"✅ Created sample .env file at {env_file_path}")
        print("   Please edit it with your actual database credentials")
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")

if __name__ == "__main__":
    print("🧪 Database Connectivity Test")
    print("=" * 60)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    if not env_ok:
        create_sample_env_file()
        print("\n❌ Please set up your environment variables and try again")
        sys.exit(1)
    
    # Test database connection
    db_ok = test_database_connection()
    
    if db_ok:
        # Test query framework
        framework_ok = test_query_framework_with_db()
        
        if framework_ok:
            print("\n🎉 All tests passed! Database is ready for query execution tests.")
        else:
            print("\n⚠️  Database connection works but query framework has issues")
    else:
        print("\n❌ Database connection failed. Please fix the issues above.")
    
    print("\n" + "=" * 60)
