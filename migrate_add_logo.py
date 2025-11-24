"""Simple migration script to add logo_url column to organizations table"""
import sqlite3
import os
from pathlib import Path

# Database path (adjust if needed)
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./lead_scraper.db").replace("sqlite:///", "")

def migrate():
    """Add logo_url column to organizations table"""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("The column will be added automatically when the app starts (SQLAlchemy will handle it)")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(organizations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add logo_url column
        if "logo_url" in columns:
            print("[OK] logo_url column already exists")
        else:
            cursor.execute("ALTER TABLE organizations ADD COLUMN logo_url VARCHAR(512)")
            conn.commit()
            print("[OK] Added logo_url column to organizations table")
        
        # Add brand_name column
        if "brand_name" in columns:
            print("[OK] brand_name column already exists")
        else:
            cursor.execute("ALTER TABLE organizations ADD COLUMN brand_name VARCHAR(255)")
            conn.commit()
            print("[OK] Added brand_name column to organizations table")
        
        # Add tagline column
        if "tagline" in columns:
            print("[OK] tagline column already exists")
        else:
            cursor.execute("ALTER TABLE organizations ADD COLUMN tagline VARCHAR(255)")
            conn.commit()
            print("[OK] Added tagline column to organizations table")
        
        # Create uploads directory
        uploads_dir = Path("uploads/logos")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created uploads directory: {uploads_dir}")
        
        conn.close()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        print("\nNote: If you're using PostgreSQL, run this SQL manually:")
        print("ALTER TABLE organizations ADD COLUMN logo_url VARCHAR(512);")

if __name__ == "__main__":
    migrate()

