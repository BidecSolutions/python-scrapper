"""Migration script to add email_verifications table"""
import sqlite3
import os
from pathlib import Path

# Database path (adjust if needed)
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./lead_scraper.db").replace("sqlite:///", "")

def migrate():
    """Add email_verifications table"""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("The table will be created automatically when the app starts (SQLAlchemy will handle it)")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_verifications'")
        if cursor.fetchone():
            print("[OK] email_verifications table already exists")
            conn.close()
            return
        
        # Create table
        cursor.execute("""
            CREATE TABLE email_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                organization_id INTEGER NOT NULL,
                email VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL,
                reason VARCHAR(100),
                confidence NUMERIC(5, 2),
                mx_records JSON,
                smtp_checked BOOLEAN NOT NULL DEFAULT 0,
                checked_at DATETIME,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                UNIQUE(organization_id, email)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_email_verifications_org ON email_verifications(organization_id)")
        cursor.execute("CREATE INDEX idx_email_verifications_email ON email_verifications(email)")
        cursor.execute("CREATE INDEX idx_email_verifications_status ON email_verifications(status)")
        cursor.execute("CREATE INDEX idx_email_verification_status ON email_verifications(organization_id, status)")
        
        conn.commit()
        conn.close()
        print("[OK] Created email_verifications table with indexes")
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        print("\nNote: If you're using PostgreSQL, run this SQL manually:")
        print("""
CREATE TABLE email_verifications (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    reason VARCHAR(100),
    confidence NUMERIC(5, 2),
    mx_records TEXT[],
    smtp_checked BOOLEAN NOT NULL DEFAULT FALSE,
    checked_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, email)
);

CREATE INDEX idx_email_verifications_org ON email_verifications(organization_id);
CREATE INDEX idx_email_verifications_email ON email_verifications(email);
CREATE INDEX idx_email_verifications_status ON email_verifications(status);
CREATE INDEX idx_email_verification_status ON email_verifications(organization_id, status);
        """)

if __name__ == "__main__":
    migrate()

