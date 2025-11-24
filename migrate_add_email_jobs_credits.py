"""Migration: Add email finder/verifier jobs and credits system"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./lead_scraper.db").replace("sqlite:///", "")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("The tables will be created automatically when the app starts (SQLAlchemy will handle it)")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(organizations)")
        org_columns = [col[1] for col in cursor.fetchall()]
        
        # Add credits columns to organizations
        if "credits_balance" not in org_columns:
            cursor.execute("ALTER TABLE organizations ADD COLUMN credits_balance INTEGER DEFAULT 0")
            print("[OK] Added credits_balance column to organizations table")
        
        if "credits_limit" not in org_columns:
            cursor.execute("ALTER TABLE organizations ADD COLUMN credits_limit INTEGER DEFAULT 1000")
            print("[OK] Added credits_limit column to organizations table")
        
        if "credits_reset_at" not in org_columns:
            cursor.execute("ALTER TABLE organizations ADD COLUMN credits_reset_at DATETIME")
            print("[OK] Added credits_reset_at column to organizations table")
        
        # Initialize credits for existing organizations
        cursor.execute("UPDATE organizations SET credits_balance = 1000, credits_limit = 1000 WHERE credits_balance IS NULL")
        cursor.execute("UPDATE organizations SET credits_reset_at = ? WHERE credits_reset_at IS NULL", 
                      ((datetime.utcnow() + timedelta(days=30)).isoformat(),))
        print("[OK] Initialized credits for existing organizations")
        
        # Check if email_finder_jobs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_finder_jobs'")
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE email_finder_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    organization_id INTEGER NOT NULL,
                    created_by_user_id INTEGER,
                    name VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'pending',
                    error_message TEXT,
                    input_data TEXT DEFAULT '[]',
                    total_inputs INTEGER DEFAULT 0,
                    processed_count INTEGER DEFAULT 0,
                    found_count INTEGER DEFAULT 0,
                    not_found_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    skip_smtp BOOLEAN DEFAULT 0,
                    min_confidence DECIMAL(3,2) DEFAULT 0.3,
                    auto_save_to_leads BOOLEAN DEFAULT 0,
                    target_list_id INTEGER,
                    results TEXT,
                    credits_used INTEGER DEFAULT 0,
                    started_at DATETIME,
                    completed_at DATETIME,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX idx_email_finder_jobs_org ON email_finder_jobs(organization_id)")
            cursor.execute("CREATE INDEX idx_email_finder_jobs_status ON email_finder_jobs(status)")
            cursor.execute("CREATE INDEX idx_email_finder_jobs_created ON email_finder_jobs(created_at)")
            print("[OK] Created email_finder_jobs table")
        
        # Check if email_verification_jobs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_verification_jobs'")
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE email_verification_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    organization_id INTEGER NOT NULL,
                    created_by_user_id INTEGER,
                    name VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'pending',
                    error_message TEXT,
                    input_emails TEXT DEFAULT '[]',
                    total_emails INTEGER DEFAULT 0,
                    processed_count INTEGER DEFAULT 0,
                    valid_count INTEGER DEFAULT 0,
                    invalid_count INTEGER DEFAULT 0,
                    risky_count INTEGER DEFAULT 0,
                    unknown_count INTEGER DEFAULT 0,
                    disposable_count INTEGER DEFAULT 0,
                    gibberish_count INTEGER DEFAULT 0,
                    skip_smtp BOOLEAN DEFAULT 0,
                    results TEXT,
                    credits_used INTEGER DEFAULT 0,
                    started_at DATETIME,
                    completed_at DATETIME,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX idx_email_verification_jobs_org ON email_verification_jobs(organization_id)")
            cursor.execute("CREATE INDEX idx_email_verification_jobs_status ON email_verification_jobs(status)")
            print("[OK] Created email_verification_jobs table")
        
        # Check if email_finder_results table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_finder_results'")
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE email_finder_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    organization_id INTEGER NOT NULL,
                    job_id INTEGER,
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    company VARCHAR(255),
                    domain VARCHAR(255),
                    found_email VARCHAR(255),
                    status VARCHAR(50),
                    confidence DECIMAL(3,2),
                    verification_status VARCHAR(50),
                    verification_reason VARCHAR(100),
                    candidates_checked INTEGER DEFAULT 0,
                    error_message TEXT,
                    lead_id INTEGER,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                    FOREIGN KEY (job_id) REFERENCES email_finder_jobs(id) ON DELETE CASCADE,
                    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL
                )
            """)
            cursor.execute("CREATE INDEX idx_email_finder_results_org ON email_finder_results(organization_id)")
            cursor.execute("CREATE INDEX idx_email_finder_results_job ON email_finder_results(job_id)")
            cursor.execute("CREATE INDEX idx_email_finder_results_domain ON email_finder_results(domain)")
            print("[OK] Created email_finder_results table")
        
        # Check if credit_transactions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credit_transactions'")
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE credit_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    organization_id INTEGER NOT NULL,
                    transaction_type VARCHAR(50) NOT NULL,
                    amount INTEGER NOT NULL,
                    balance_after INTEGER NOT NULL,
                    feature VARCHAR(50),
                    reference_id INTEGER,
                    reference_type VARCHAR(50),
                    description TEXT,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX idx_credit_transactions_org ON credit_transactions(organization_id)")
            cursor.execute("CREATE INDEX idx_credit_transactions_created ON credit_transactions(created_at)")
            print("[OK] Created credit_transactions table")
        
        conn.commit()
        conn.close()
        print("\n[SUCCESS] Migration completed successfully!")
        print("\nNote: If you're using PostgreSQL, run these SQL commands manually:")
        print("See EMAIL_FINDER_VERIFIER_DESIGN.md for full schema")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate()

