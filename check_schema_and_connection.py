"""Check which database and schema we're actually connected to"""
import sys
import os
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

def check_connection_details():
    print("=" * 60)
    print("Database Connection Analysis")
    print("=" * 60)
    
    db_url = settings.DATABASE_URL
    print(f"\nConnection String: {db_url.split('@')[0]}@***")
    print(f"Full URL (hidden password): {db_url.split(':')[-1]}")
    
    # Convert async URL to sync if needed
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
    
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Check current database
        result = conn.execute(text("SELECT current_database(), current_schema();"))
        db_name, schema = result.fetchone()
        print(f"\n✅ Currently connected to:")
        print(f"   Database: {db_name}")
        print(f"   Schema: {schema}")
        
        # Check all schemas
        print(f"\n📋 Available schemas:")
        result = conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
        """))
        schemas = result.fetchall()
        for schema_row in schemas:
            print(f"   - {schema_row[0]}")
        
        # Check tables in public schema
        print(f"\n📊 Tables in 'public' schema:")
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
            LIMIT 10;
        """))
        tables = result.fetchall()
        if tables:
            for table in tables:
                print(f"   - {table[0]}")
            print(f"   ... (showing first 10)")
        else:
            print("   ❌ No tables found in 'public' schema!")
        
        # Check tables in ALL schemas
        print(f"\n📊 Tables in ALL schemas:")
        result = conn.execute(text("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY table_schema, table_name
            LIMIT 20;
        """))
        all_tables = result.fetchall()
        if all_tables:
            current_schema = None
            for schema, table in all_tables:
                if schema != current_schema:
                    print(f"\n   Schema: {schema}")
                    current_schema = schema
                print(f"      - {table}")
            if len(all_tables) == 20:
                print(f"   ... (showing first 20)")
        else:
            print("   ❌ No tables found in any schema!")
        
        # Count total tables
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast');
        """))
        total = result.scalar()
        print(f"\n📈 Total tables across all schemas: {total}")
        
        # Check if we're using connection pooler
        print(f"\n🔌 Connection details:")
        if ":6543" in settings.DATABASE_URL:
            print("   ⚠️  Using CONNECTION POOLER (port 6543)")
            print("   💡 Tip: Supabase dashboard shows the DIRECT connection database")
            print("   💡 The pooler might connect to a different database!")
        elif ":5432" in settings.DATABASE_URL:
            print("   ✅ Using DIRECT connection (port 5432)")
            print("   ✅ This should match what you see in Supabase dashboard")
        else:
            print("   ⚠️  Unknown connection type")

if __name__ == "__main__":
    try:
        check_connection_details()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

