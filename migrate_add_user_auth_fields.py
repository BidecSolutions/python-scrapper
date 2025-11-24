"""Migration script to add authentication fields to users table"""
import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./lead_scraper.db").replace("sqlite:///", "")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("The columns will be created automatically when the app starts (SQLAlchemy will handle it)")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        columns_to_add = {
            "status": ("VARCHAR(20)", "idx_user_status", "'pending'"),
            "is_super_admin": ("BOOLEAN", "idx_user_super_admin", "0"),
            "can_use_advanced": ("BOOLEAN", "idx_user_advanced", "0"),
        }
        
        for col_name, (col_type, index_name, default_value) in columns_to_add.items():
            if col_name not in existing_columns:
                print(f"[MIGRATING] Adding {col_name} column to users table...")
                cursor.execute(f"""
                    ALTER TABLE users 
                    ADD COLUMN {col_name} {col_type} DEFAULT {default_value}
                """)
                if index_name:
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON users({col_name})
                    """)
                print(f"[OK] Added {col_name} column to users table")
            else:
                print(f"[OK] users.{col_name} column already exists")
        
        # Make organization_id nullable if it's not already
        # SQLite doesn't support ALTER COLUMN, so we'll just note it
        print("[NOTE] If organization_id should be nullable, you may need to recreate the table or use a more advanced migration tool")
        
        conn.commit()
        conn.close()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: If you're using PostgreSQL, run these SQL commands manually:")
        print("""
-- PostgreSQL commands for reference:

ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending' NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_super_admin BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS can_use_advanced BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE users ALTER COLUMN organization_id DROP NOT NULL; -- Make nullable

CREATE INDEX IF NOT EXISTS idx_user_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_user_super_admin ON users(is_super_admin);
CREATE INDEX IF NOT EXISTS idx_user_advanced ON users(can_use_advanced);
        """)

if __name__ == "__main__":
    migrate()

