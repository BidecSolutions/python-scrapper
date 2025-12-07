"""Add job_completed and job_failed to notificationtype enum"""
import sys
from sqlalchemy import text
from app.core.db import engine

print("Adding job_completed and job_failed to notificationtype enum...")

with engine.connect() as conn:
    try:
        # Check if the enum values already exist
        result = conn.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid FROM pg_type WHERE typname = 'notificationtype'
            )
        """))
        existing_values = {row[0] for row in result}
        
        # Add missing enum values
        values_to_add = ['job_completed', 'job_failed']
        
        for enum_value in values_to_add:
            if enum_value not in existing_values:
                print(f"  Adding enum value: {enum_value}")
                try:
                    conn.execute(text(f"ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS '{enum_value}'"))
                    conn.commit()
                    print(f"    ✓ Added {enum_value}")
                except Exception as e:
                    # IF NOT EXISTS might not be supported in all PostgreSQL versions
                    # Try without it
                    try:
                        conn.execute(text(f"ALTER TYPE notificationtype ADD VALUE '{enum_value}'"))
                        conn.commit()
                        print(f"    ✓ Added {enum_value}")
                    except Exception as e2:
                        if "already exists" in str(e2).lower() or "duplicate" in str(e2).lower():
                            print(f"    ⚠ {enum_value} already exists, skipping")
                        else:
                            print(f"    ✗ Failed to add {enum_value}: {e2}")
            else:
                print(f"  Enum value {enum_value} already exists, skipping")
        
        print("\nSUCCESS: All notification enum values added!")
        
    except Exception as e:
        print(f"\nERROR: Failed to add enum values: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)

