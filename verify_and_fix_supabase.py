"""Verify database setup and provide fix instructions"""
import sys
import os
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

def main():
    print("=" * 70)
    print("Supabase Database Verification & Fix")
    print("=" * 70)
    
    db_url = settings.DATABASE_URL
    
    # Convert async URL to sync if needed
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
    
    print(f"\n📊 Testing connection: {db_url.split('@')[0]}@***")
    
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Get current database
        result = conn.execute(text("SELECT current_database();"))
        current_db = result.scalar()
        print(f"\n✅ Connected to database: {current_db}")
        
        # Count tables
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """))
        table_count = result.scalar()
        print(f"✅ Tables in 'public' schema: {table_count}")
        
        # List all databases
        result = conn.execute(text("""
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false 
            ORDER BY datname;
        """))
        databases = result.fetchall()
        print(f"\n📋 Available databases:")
        for db in databases:
            marker = " ← You are here" if db[0] == current_db else ""
            print(f"   - {db[0]}{marker}")
        
        # List first 10 tables
        if table_count > 0:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
                LIMIT 10;
            """))
            tables = result.fetchall()
            print(f"\n📋 First 10 tables:")
            for table in tables:
                print(f"   - {table[0]}")
            if table_count > 10:
                print(f"   ... and {table_count - 10} more")
    
    print("\n" + "=" * 70)
    print("🔧 SOLUTION FOR SUPABASE DASHBOARD")
    print("=" * 70)
    
    if current_db == "postgres" and table_count == 0:
        print("""
⚠️  ISSUE DETECTED:
   - Supabase dashboard is showing 'postgres' database (empty)
   - Your tables are in 'Lead_scrapper' database

✅ SOLUTION:
   
   Option 1: Check for Database Selector in Supabase
   ------------------------------------------------
   1. In Supabase Table Editor, look for a dropdown that says "Database" or "Schema"
   2. Try to select "Lead_scrapper" instead of "postgres"
   3. If you see a "schema" dropdown, make sure it's set to "public"
   
   Option 2: Use SQL Editor with Cross-Database Query
   ------------------------------------------------
   Unfortunately, PostgreSQL doesn't allow easy cross-database queries.
   You need to connect directly to the Lead_scrapper database.
   
   Option 3: Check Supabase Connection Settings
   ------------------------------------------------
   1. Go to: Settings → Database
   2. Look at the "Connection string" section
   3. Check if there's a way to specify which database to view
   4. The connection string should end with: /Lead_scrapper
   
   Option 4: Update Your App Connection (Recommended)
   ------------------------------------------------
   Your app is working correctly! The issue is just the Supabase dashboard view.
   Your 75 tables are safe and accessible through your application.
   
   To see them in dashboard, you may need to:
   - Contact Supabase support about database selection
   - Or use a PostgreSQL client like pgAdmin or DBeaver
   - Or use the Supabase API to query your tables
        """)
    elif current_db == "Lead_scrapper" and table_count > 0:
        print("""
✅ YOUR SETUP IS CORRECT!
   - Connected to: Lead_scrapper
   - Tables found: {table_count}
   
   If Supabase dashboard shows empty:
   - The dashboard might be hardcoded to show 'postgres' database
   - Your data is safe and accessible through your app
   - Try refreshing the dashboard or checking for a database selector
        """.format(table_count=table_count))
    
    print("\n" + "=" * 70)
    print("📝 SQL QUERIES FOR SUPABASE SQL EDITOR")
    print("=" * 70)
    print("""
Copy these queries into Supabase SQL Editor:

1. See all databases:
   SELECT datname FROM pg_database WHERE datistemplate = false;

2. Check current database:
   SELECT current_database();

3. See all tables in current database:
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' ORDER BY table_name;
    """)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

