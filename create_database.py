"""Create the Lead_scrapper database if it doesn't exist"""
import os
import sys
from urllib.parse import urlparse, urlunparse

# First, connect to the default 'postgres' database to create our database
# Connection string to default postgres database
default_db_url = "postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres"
os.environ["DATABASE_URL"] = default_db_url

try:
    from app.core.db import engine, SessionLocal
    from sqlalchemy import text
    
    print("=" * 60)
    print("Creating Database: Lead_scrapper")
    print("=" * 60)
    
    # Connect to default postgres database
    with engine.connect() as conn:
        # Check if database exists
        result = conn.execute(text("""
            SELECT 1 FROM pg_database WHERE datname = 'Lead_scrapper'
        """))
        exists = result.fetchone() is not None
        
        if exists:
            print("✅ Database 'Lead_scrapper' already exists!")
        else:
            # Set autocommit mode to create database
            conn.execute(text("COMMIT"))
            try:
                conn.execute(text("CREATE DATABASE \"Lead_scrapper\""))
                conn.execute(text("COMMIT"))
                print("✅ Database 'Lead_scrapper' created successfully!")
            except Exception as e:
                print(f"❌ Error creating database: {e}")
                print("\nNote: You may need to create the database manually in Supabase dashboard.")
                sys.exit(1)
    
    # Now test connection to the new database
    print("\n" + "=" * 60)
    print("Testing connection to Lead_scrapper database")
    print("=" * 60)
    
    # Update to use Lead_scrapper database
    target_db_url = "postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper"
    os.environ["DATABASE_URL"] = target_db_url
    
    # Recreate engine with new database
    from sqlalchemy import create_engine
    new_engine = create_engine(target_db_url, pool_pre_ping=True)
    
    with new_engine.connect() as conn:
        result = conn.execute(text("SELECT current_database();"))
        db_name = result.fetchone()[0]
        print(f"✅ Successfully connected to database: {db_name}")
    
    print("\n" + "=" * 60)
    print("✅ Database setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Your .env file is already configured")
    print("2. Initialize tables: python init_db.py")
    print("3. Create admin user: python create_user.py")
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ Error setting up database")
    print("=" * 60)
    print(f"Error: {str(e)}")
    print("\nAlternative: Create the database manually in Supabase dashboard:")
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Run: CREATE DATABASE \"Lead_scrapper\";")
    print("   (Note: In Supabase, you may need to create it via the dashboard UI)")
    sys.exit(1)

