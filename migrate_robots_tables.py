"""Migration script to create robots tables"""
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.db import Base

# Import all ORM models to register them
from app.core.orm import *  # noqa
from app.core.orm_robots import *  # noqa

def migrate():
    """Create robots tables"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("Creating robots tables...")
    
    # Create tables
    Base.metadata.create_all(engine)
    
    print("SUCCESS: Robots tables created!")
    print("\nCreated tables:")
    print("  - robots")
    print("  - robot_runs")
    print("  - robot_run_urls")
    print("  - robot_run_rows")
    
    # Add source_robot_run_id column to leads if it doesn't exist
    if settings.DATABASE_URL.startswith("sqlite"):
        conn = engine.connect()
        try:
            # Check if column exists
            cursor = conn.execute(text("PRAGMA table_info(leads)"))
            columns = [row[1] for row in cursor.fetchall()]
            
            if "source_robot_run_id" not in columns:
                print("\nAdding source_robot_run_id column to leads table...")
                conn.execute(text("ALTER TABLE leads ADD COLUMN source_robot_run_id INTEGER"))
                conn.commit()
                print("  - Added source_robot_run_id column")
            else:
                print("\n  - source_robot_run_id column already exists")
        except Exception as e:
            print(f"  - Warning: Could not add column: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    migrate()

