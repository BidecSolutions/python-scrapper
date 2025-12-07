"""Add AI-related columns to scrape_jobs table"""
import sys
from sqlalchemy import text
from app.core.db import engine

# Columns to add
columns_to_add = [
    ("ai_status", "VARCHAR(50) NOT NULL DEFAULT 'idle'"),
    ("ai_summary", "TEXT"),
    ("ai_segments", "JSONB"),
    ("ai_error", "TEXT"),
    ("meta", "JSONB NOT NULL DEFAULT '{}'"),
]

print("Adding AI columns to scrape_jobs table...")

with engine.connect() as conn:
    try:
        # Check which columns already exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'scrape_jobs'
        """))
        existing_columns = {row[0] for row in result}
        
        # Add missing columns
        for column_name, column_def in columns_to_add:
            if column_name not in existing_columns:
                print(f"  Adding column: {column_name}")
                try:
                    conn.execute(text(f"ALTER TABLE scrape_jobs ADD COLUMN {column_name} {column_def}"))
                    conn.commit()
                    print(f"    ✓ Added {column_name}")
                except Exception as e:
                    print(f"    ✗ Failed to add {column_name}: {e}")
                    # Try without NOT NULL constraint if it fails
                    if "NOT NULL" in column_def:
                        try:
                            column_def_alt = column_def.replace(" NOT NULL", "")
                            conn.execute(text(f"ALTER TABLE scrape_jobs ADD COLUMN {column_name} {column_def_alt}"))
                            conn.execute(text(f"UPDATE scrape_jobs SET {column_name} = {column_def.split()[-1]} WHERE {column_name} IS NULL"))
                            conn.execute(text(f"ALTER TABLE scrape_jobs ALTER COLUMN {column_name} SET NOT NULL"))
                            conn.commit()
                            print(f"    ✓ Added {column_name} (with default)")
                        except Exception as e2:
                            print(f"    ✗ Failed to add {column_name} even without NOT NULL: {e2}")
            else:
                print(f"  Column {column_name} already exists, skipping")
        
        # Create index on ai_status if it doesn't exist
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_scrape_jobs_ai_status ON scrape_jobs(ai_status)"))
            conn.commit()
            print("  ✓ Created index on ai_status")
        except Exception as e:
            print(f"  ⚠ Could not create index on ai_status: {e}")
        
        print("\nSUCCESS: All AI columns added to scrape_jobs table!")
        
    except Exception as e:
        print(f"\nERROR: Failed to add columns: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)

