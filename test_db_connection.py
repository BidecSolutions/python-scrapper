"""Test database connection to PostgreSQL"""
import os
import sys
from urllib.parse import quote_plus

# Set the database URL before importing config
# Password needs to be URL-encoded: @ becomes %40
DATABASE_URL = "postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper"
os.environ["DATABASE_URL"] = DATABASE_URL

try:
    from app.core.db import engine
    from sqlalchemy import text
    
    print("=" * 60)
    print("Testing PostgreSQL Database Connection")
    print("=" * 60)
    print(f"Database: Lead_scrapper")
    print(f"Host: aws-1-ap-northeast-2.pooler.supabase.com:6543")
    print("=" * 60)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ Connection successful!")
        print(f"PostgreSQL version: {version}")
        
        # Test database name
        result = conn.execute(text("SELECT current_database();"))
        db_name = result.fetchone()[0]
        print(f"Current database: {db_name}")
        
        # List tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"\nTables in database: {len(tables)}")
        if tables:
            print("Existing tables:")
            for table in tables[:10]:  # Show first 10
                print(f"  - {table}")
            if len(tables) > 10:
                print(f"  ... and {len(tables) - 10} more")
        else:
            print("No tables found. Run 'python init_db.py' to create tables.")
    
    print("\n" + "=" * 60)
    print("✅ Database connection test PASSED!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Create a .env file in the python-scrapper directory with:")
    print("   DATABASE_URL=postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper")
    print("2. Run 'python init_db.py' to create database tables")
    print("3. Run 'python create_user.py' to create admin user")
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ Database connection test FAILED!")
    print("=" * 60)
    print(f"Error: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Check if psycopg2-binary is installed: pip install psycopg2-binary")
    print("2. Verify database credentials are correct")
    print("3. Check if database 'Lead_scrapper' exists")
    print("4. Verify network connectivity to Supabase")
    sys.exit(1)

