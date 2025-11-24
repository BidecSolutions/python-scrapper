"""Migration: Add emails table and email_verification_items table"""
import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./lead_scraper.db").replace("sqlite:///", "")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("The tables will be created automatically when the app starts (SQLAlchemy will handle it)")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if emails table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    organization_id INTEGER NOT NULL,
                    lead_id INTEGER,
                    email VARCHAR(255) NOT NULL,
                    label VARCHAR(50),
                    verify_status VARCHAR(20),
                    verify_reason TEXT,
                    verify_confidence DECIMAL(3,2),
                    verified_at DATETIME,
                    found_via VARCHAR(20),
                    finder_job_id INTEGER,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
                    FOREIGN KEY (finder_job_id) REFERENCES email_finder_jobs(id) ON DELETE SET NULL
                )
            """)
            cursor.execute("CREATE INDEX idx_emails_org_lead ON emails(organization_id, lead_id)")
            cursor.execute("CREATE INDEX idx_emails_email ON emails(email)")
            cursor.execute("CREATE INDEX idx_emails_verify_status ON emails(organization_id, verify_status)")
            print("[OK] Created emails table")
        
        # Check if email_verification_items table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_verification_items'")
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE email_verification_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    organization_id INTEGER NOT NULL,
                    job_id INTEGER NOT NULL,
                    email_id INTEGER,
                    raw_email VARCHAR(255) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    verify_status VARCHAR(20),
                    verify_reason TEXT,
                    verify_confidence DECIMAL(3,2),
                    error TEXT,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                    FOREIGN KEY (job_id) REFERENCES email_verification_jobs(id) ON DELETE CASCADE,
                    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE SET NULL
                )
            """)
            cursor.execute("CREATE INDEX idx_email_ver_items_job ON email_verification_items(job_id)")
            cursor.execute("CREATE INDEX idx_email_ver_items_status ON email_verification_items(job_id, status)")
            print("[OK] Created email_verification_items table")
        
        # Update email_verification_jobs table to add source_type and source_description
        cursor.execute("PRAGMA table_info(email_verification_jobs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "source_type" not in columns:
            cursor.execute("ALTER TABLE email_verification_jobs ADD COLUMN source_type VARCHAR(20) DEFAULT 'leads'")
            print("[OK] Added source_type column to email_verification_jobs table")
        
        if "source_description" not in columns:
            cursor.execute("ALTER TABLE email_verification_jobs ADD COLUMN source_description TEXT")
            print("[OK] Added source_description column to email_verification_jobs table")
        
        if "syntax_error_count" not in columns:
            cursor.execute("ALTER TABLE email_verification_jobs ADD COLUMN syntax_error_count INTEGER DEFAULT 0")
            print("[OK] Added syntax_error_count column to email_verification_jobs table")
        
        conn.commit()
        conn.close()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate()

