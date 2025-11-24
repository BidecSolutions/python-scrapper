"""Migration script to add missing columns to dossiers table"""
import sqlite3
import os
from pathlib import Path

# Database path (adjust if needed)
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./lead_scraper.db").replace("sqlite:///", "")

def migrate():
    """Add missing columns to dossiers table"""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("The columns will be added automatically when the app starts (SQLAlchemy will handle it)")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if table exists and get current columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dossiers'")
        if not cursor.fetchone():
            print("[OK] dossiers table does not exist - it will be created automatically when the app starts")
            conn.close()
            return
        
        cursor.execute("PRAGMA table_info(dossiers)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        # Add status column (stored as VARCHAR, SQLAlchemy will handle enum conversion)
        if "status" not in columns:
            cursor.execute("ALTER TABLE dossiers ADD COLUMN status VARCHAR(20) DEFAULT 'pending'")
            conn.commit()
            print("[OK] Added status column to dossiers table")
        else:
            print("[OK] status column already exists")
        
        # Add error column
        if "error" not in columns:
            cursor.execute("ALTER TABLE dossiers ADD COLUMN error TEXT")
            conn.commit()
            print("[OK] Added error column to dossiers table")
        else:
            print("[OK] error column already exists")
        
        # Add started_at column
        if "started_at" not in columns:
            cursor.execute("ALTER TABLE dossiers ADD COLUMN started_at DATETIME")
            conn.commit()
            print("[OK] Added started_at column to dossiers table")
        else:
            print("[OK] started_at column already exists")
        
        # Add completed_at column
        if "completed_at" not in columns:
            cursor.execute("ALTER TABLE dossiers ADD COLUMN completed_at DATETIME")
            conn.commit()
            print("[OK] Added completed_at column to dossiers table")
        else:
            print("[OK] completed_at column already exists")
        
        # Add sections column (JSON)
        if "sections" not in columns:
            cursor.execute("ALTER TABLE dossiers ADD COLUMN sections JSON")
            conn.commit()
            print("[OK] Added sections column to dossiers table")
        else:
            print("[OK] sections column already exists")
        
        conn.close()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        print("\nNote: If you're using PostgreSQL, run this SQL manually:")
        print("ALTER TABLE dossiers ADD COLUMN status VARCHAR(20) DEFAULT 'pending';")
        print("ALTER TABLE dossiers ADD COLUMN error TEXT;")
        print("ALTER TABLE dossiers ADD COLUMN started_at TIMESTAMP WITH TIME ZONE;")
        print("ALTER TABLE dossiers ADD COLUMN completed_at TIMESTAMP WITH TIME ZONE;")
        print("ALTER TABLE dossiers ADD COLUMN sections JSONB;")

if __name__ == "__main__":
    migrate()

