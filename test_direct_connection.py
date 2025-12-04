"""Test direct connection (port 5432) vs pooler connection (port 6543)"""
import sys
import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Your connection details
USER = "postgres.aashvhvwiayvniidvaqk"
PASSWORD = "Newpass@2025@"
HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
DB_NAME = "Lead_scrapper"

# URL encode password
encoded_password = quote_plus(PASSWORD)

print("=" * 70)
print("Testing Both Connection Types")
print("=" * 70)

# Test 1: Connection Pooler (port 6543)
print("\n1️⃣  Testing CONNECTION POOLER (port 6543):")
pooler_url = f"postgresql://{USER}:{encoded_password}@{HOST}:6543/{DB_NAME}"
print(f"   URL: postgresql://{USER}:***@{HOST}:6543/{DB_NAME}")

try:
    engine = create_engine(pooler_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database(), COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"))
        db_name, table_count = result.fetchone()
        print(f"   ✅ Connected to database: {db_name}")
        print(f"   ✅ Tables in public schema: {table_count}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Direct Connection (port 5432) - Try with 'postgres' database
print("\n2️⃣  Testing DIRECT CONNECTION (port 5432) - 'postgres' database:")
direct_url_postgres = f"postgresql://{USER}:{encoded_password}@{HOST}:5432/postgres"
print(f"   URL: postgresql://{USER}:***@{HOST}:5432/postgres")

try:
    engine = create_engine(direct_url_postgres)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database(), COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"))
        db_name, table_count = result.fetchone()
        print(f"   ✅ Connected to database: {db_name}")
        print(f"   ✅ Tables in public schema: {table_count}")
        
        # List all databases
        result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"))
        databases = result.fetchall()
        print(f"\n   📋 Available databases:")
        for db in databases:
            print(f"      - {db[0]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Direct Connection (port 5432) - Try with 'Lead_scrapper' database
print("\n3️⃣  Testing DIRECT CONNECTION (port 5432) - 'Lead_scrapper' database:")
direct_url_lead = f"postgresql://{USER}:{encoded_password}@{HOST}:5432/{DB_NAME}"
print(f"   URL: postgresql://{USER}:***@{HOST}:5432/{DB_NAME}")

try:
    engine = create_engine(direct_url_lead)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database(), COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"))
        db_name, table_count = result.fetchone()
        print(f"   ✅ Connected to database: {db_name}")
        print(f"   ✅ Tables in public schema: {table_count}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("💡 Recommendation:")
print("   Use the connection that shows your 75 tables AND matches")
print("   what you see in the Supabase dashboard.")
print("=" * 70)

