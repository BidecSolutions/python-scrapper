"""Initialize database tables (SYNC version)"""
import os
from app.core.db import engine, Base
from app.core import orm  # Import models to register them


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("SUCCESS: Database tables created successfully!")
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        
        # Check if it's a connection error
        if "connection" in error_msg.lower() or "refused" in error_msg.lower():
            print("\n" + "="*60)
            print("Database connection error.")
            print("\nOPTION 1: Use SQLite (Quick Start)")
            print("  Create a .env file with:")
            print("  DATABASE_URL=sqlite:///./lead_scraper.db")
            print("\nOPTION 2: Setup PostgreSQL")
            print("  1. Install PostgreSQL")
            print("  2. Create database: createdb lead_scraper")
            print("  3. Create .env file with:")
            print("     DATABASE_URL=postgresql://user:password@localhost:5432/lead_scraper")
            print("="*60)
        raise


if __name__ == "__main__":
    try:
        create_tables()
    except Exception as e:
        print(f"\nFailed to create tables. Error: {e}")
        raise

