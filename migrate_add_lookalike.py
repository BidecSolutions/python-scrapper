"""Migration script to create lookalike tables"""
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
        
        # Check if lookalike_jobs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lookalike_jobs'")
        if cursor.fetchone():
            print("[OK] lookalike_jobs table already exists")
        else:
            print("[MIGRATING] Creating lookalike_jobs table...")
            cursor.execute("""
                CREATE TABLE lookalike_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    started_at DATETIME,
                    completed_at DATETIME,
                    workspace_id INTEGER NOT NULL,
                    organization_id INTEGER NOT NULL,
                    started_by_user_id INTEGER NOT NULL,
                    source_segment_id INTEGER,
                    source_list_id INTEGER,
                    source_campaign_id INTEGER,
                    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
                    positive_lead_count INTEGER DEFAULT 0 NOT NULL,
                    candidates_found INTEGER DEFAULT 0 NOT NULL,
                    profile_embedding TEXT,
                    meta TEXT DEFAULT '{}',
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                    FOREIGN KEY (started_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (source_segment_id) REFERENCES segments(id) ON DELETE SET NULL,
                    FOREIGN KEY (source_list_id) REFERENCES lead_lists(id) ON DELETE SET NULL
                )
            """)
            cursor.execute("CREATE INDEX idx_lookalike_job_workspace_status ON lookalike_jobs(workspace_id, status)")
            cursor.execute("CREATE INDEX idx_lookalike_job_created ON lookalike_jobs(created_at)")
            cursor.execute("CREATE INDEX idx_lookalike_job_workspace_id ON lookalike_jobs(workspace_id)")
            cursor.execute("CREATE INDEX idx_lookalike_job_source_segment_id ON lookalike_jobs(source_segment_id)")
            cursor.execute("CREATE INDEX idx_lookalike_job_source_list_id ON lookalike_jobs(source_list_id)")
            print("[OK] Created lookalike_jobs table")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lookalike_candidates'")
        if cursor.fetchone():
            print("[OK] lookalike_candidates table already exists")
        else:
            print("[MIGRATING] Creating lookalike_candidates table...")
            cursor.execute("""
                CREATE TABLE lookalike_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    job_id INTEGER NOT NULL,
                    workspace_id INTEGER NOT NULL,
                    lead_id INTEGER,
                    company_id INTEGER,
                    score REAL NOT NULL,
                    reason_vector TEXT,
                    FOREIGN KEY (job_id) REFERENCES lookalike_jobs(id) ON DELETE CASCADE,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX idx_lookalike_candidate_job_score ON lookalike_candidates(job_id, score)")
            cursor.execute("CREATE INDEX idx_lookalike_candidate_lead ON lookalike_candidates(lead_id)")
            cursor.execute("CREATE INDEX idx_lookalike_candidate_company ON lookalike_candidates(company_id)")
            cursor.execute("CREATE INDEX idx_lookalike_candidate_job_id ON lookalike_candidates(job_id)")
            print("[OK] Created lookalike_candidates table")
        
        conn.commit()
        conn.close()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate()

