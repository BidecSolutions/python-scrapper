"""Database migration script to add new columns"""
import sqlite3
import os
from pathlib import Path
from app.core.config import settings

def migrate_database():
    """Add missing columns to existing database"""
    db_url = settings.DATABASE_URL
    
    if db_url.startswith("sqlite"):
        # Extract database file path (handle both sync and async SQLite URLs)
        # sqlite:///path or sqlite+aiosqlite:///path
        db_path = db_url
        
        # Handle async SQLite URL first
        if db_path.startswith("sqlite+aiosqlite:///"):
            db_path = db_path.replace("sqlite+aiosqlite:///", "")
        elif db_path.startswith("sqlite+aiosqlite://"):
            db_path = db_path.replace("sqlite+aiosqlite://", "")
        elif db_path.startswith("sqlite:///"):
            db_path = db_path.replace("sqlite:///", "")
        elif db_path.startswith("sqlite://"):
            db_path = db_path.replace("sqlite://", "")
        
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
        
        print(f"Migrating SQLite database: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"Database file not found: {db_path}")
            print("Run 'python init_db.py' first to create the database.")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check and add columns to scrape_jobs table
            cursor.execute("PRAGMA table_info(scrape_jobs)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            migrations = []
            
            # scrape_jobs table migrations
            if "total_targets" not in existing_columns:
                migrations.append("ALTER TABLE scrape_jobs ADD COLUMN total_targets INTEGER")
            if "processed_targets" not in existing_columns:
                migrations.append("ALTER TABLE scrape_jobs ADD COLUMN processed_targets INTEGER NOT NULL DEFAULT 0")
            if "extract_config" not in existing_columns:
                migrations.append("ALTER TABLE scrape_jobs ADD COLUMN extract_config TEXT NOT NULL DEFAULT '{}'")
            
            # leads table migrations
            cursor.execute("PRAGMA table_info(leads)")
            existing_lead_columns = [row[1] for row in cursor.fetchall()]
            
            if "sources" not in existing_lead_columns:
                migrations.append("ALTER TABLE leads ADD COLUMN sources TEXT")
            if "smart_score" not in existing_lead_columns:
                migrations.append("ALTER TABLE leads ADD COLUMN smart_score NUMERIC(5,2)")
            if "smart_score_version" not in existing_lead_columns:
                migrations.append("ALTER TABLE leads ADD COLUMN smart_score_version INTEGER")
            if "fit_label" not in existing_lead_columns:
                migrations.append("ALTER TABLE leads ADD COLUMN fit_label VARCHAR(20)")
            if "segment_id" not in existing_lead_columns:
                migrations.append("ALTER TABLE leads ADD COLUMN segment_id INTEGER")
            if "custom_fields" not in existing_lead_columns:
                migrations.append("ALTER TABLE leads ADD COLUMN custom_fields TEXT")
            if "digital_maturity" not in existing_lead_columns:
                migrations.append("ALTER TABLE leads ADD COLUMN digital_maturity NUMERIC(5,2)")
            if "qa_status" not in existing_lead_columns:
                migrations.append("ALTER TABLE leads ADD COLUMN qa_status VARCHAR(50)")
            if "qa_reason" not in existing_lead_columns:
                migrations.append("ALTER TABLE leads ADD COLUMN qa_reason TEXT")
            if "embedding" not in existing_lead_columns:
                migrations.append("ALTER TABLE leads ADD COLUMN embedding TEXT")
            
            # Execute migrations
            if migrations:
                print(f"\nApplying {len(migrations)} migrations...")
                for migration in migrations:
                    print(f"  - {migration}")
                    try:
                        cursor.execute(migration)
                    except sqlite3.OperationalError as e:
                        if "duplicate column" in str(e).lower():
                            print(f"    (Column already exists, skipping)")
                        else:
                            raise
                
                conn.commit()
                print("\nSUCCESS: Database migration completed!")
            else:
                print("\nDatabase is up to date - no migrations needed.")
            
            # Create new tables for ML features
            print("\nCreating new tables for ML features...")
            from app.core.db import Base, engine
            # Import all ORM modules to register tables with Base.metadata
            from app.core import orm  # Import all models
            try:
                from app.core import orm_segments  # Import segments models
            except ImportError:
                pass
            try:
                from app.core import orm_lists  # Import lists models
            except ImportError:
                pass
            
            # Create only the new tables
            new_tables = [
                "lead_feedback",
                "org_models",
                "job_segments",
                "job_insights",
                "playbooks",
                "custom_fields",
                "segments",
                "lists"
            ]
            
            for table_name in new_tables:
                try:
                    # Check if table exists
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    if not cursor.fetchone():
                        # Create table using SQLAlchemy
                        table = Base.metadata.tables.get(table_name)
                        if table:
                            table.create(bind=engine, checkfirst=True)
                            print(f"  - Created table: {table_name}")
                        else:
                            print(f"  - Warning: Table {table_name} not found in Base.metadata (may not be imported)")
                    else:
                        print(f"  - Table already exists: {table_name}")
                except Exception as e:
                    print(f"  - Warning: Could not create {table_name}: {e}")
            
            # Also try to create all tables that might be missing
            try:
                Base.metadata.create_all(bind=engine, checkfirst=True)
                print("  - Created any additional missing tables")
            except Exception as e:
                print(f"  - Warning: Error creating additional tables: {e}")
            
        except Exception as e:
            conn.rollback()
            print(f"\nERROR: Migration failed: {e}")
            raise
        finally:
            conn.close()
    
    elif db_url.startswith("postgresql"):
        print("PostgreSQL migration not yet implemented.")
        print("Please run SQL manually or use Alembic migrations.")
        print("\nRequired SQL:")
        print("""
-- For scrape_jobs table:
ALTER TABLE scrape_jobs ADD COLUMN IF NOT EXISTS total_targets INTEGER;
ALTER TABLE scrape_jobs ADD COLUMN IF NOT EXISTS processed_targets INTEGER NOT NULL DEFAULT 0;
ALTER TABLE scrape_jobs ADD COLUMN IF NOT EXISTS extract_config JSONB NOT NULL DEFAULT '{}'::jsonb;

-- For leads table:
ALTER TABLE leads ADD COLUMN IF NOT EXISTS sources TEXT[];
ALTER TABLE leads ADD COLUMN IF NOT EXISTS smart_score NUMERIC(5,2);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS smart_score_version INTEGER;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS fit_label VARCHAR(20);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS segment_id INTEGER REFERENCES job_segments(id) ON DELETE SET NULL;

-- Create new tables (run init_db.py or use Alembic)
        """)
    else:
        print(f"Unsupported database URL: {db_url}")


if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        print(f"\nMigration failed: {e}")
        import traceback
        traceback.print_exc()
        raise

