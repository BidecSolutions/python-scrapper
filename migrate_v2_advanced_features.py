"""Migration script for v2 advanced AI features (Dossier, Identity Graph, Next Action)"""
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.db import Base

# Import all ORM models to register them
from app.core.orm import *  # noqa
from app.core.orm_v2 import *  # noqa

def migrate():
    """Create/update tables for advanced features"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("Creating/updating v2 advanced AI feature tables...")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    print("SUCCESS: Tables created/updated!")
    
    # Add new columns to leads table if using SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        conn = engine.connect()
        try:
            # Check existing columns
            cursor = conn.execute(text("PRAGMA table_info(leads)"))
            columns = [row[1] for row in cursor.fetchall()]
            
            migrations = []
            
            if "company_entity_id" not in columns:
                migrations.append("ALTER TABLE leads ADD COLUMN company_entity_id INTEGER")
            
            if "nb_action" not in columns:
                migrations.append("ALTER TABLE leads ADD COLUMN nb_action VARCHAR(32)")
            
            if "nb_action_score" not in columns:
                migrations.append("ALTER TABLE leads ADD COLUMN nb_action_score NUMERIC(5,2)")
            
            if "nb_action_generated_at" not in columns:
                migrations.append("ALTER TABLE leads ADD COLUMN nb_action_generated_at TIMESTAMP")
            
            if migrations:
                print("\nAdding new columns to leads table...")
                for migration in migrations:
                    try:
                        conn.execute(text(migration))
                        print(f"  - {migration}")
                    except Exception as e:
                        if "duplicate column" in str(e).lower():
                            print(f"  - Column already exists (skipping)")
                        else:
                            print(f"  - Warning: {e}")
                conn.commit()
            else:
                print("\n  - All columns already exist")
                
        except Exception as e:
            print(f"  - Warning: Could not add columns: {e}")
        finally:
            conn.close()
    
    print("\nMigration complete!")
    print("\nUpdated tables:")
    print("  - dossiers (with status tracking)")
    print("  - person_scores (decision maker scoring)")
    print("  - action_outcomes (with suggested_by_ai, outcome_at)")
    print("  - leads (added company_entity_id, nb_action fields)")

if __name__ == "__main__":
    migrate()

