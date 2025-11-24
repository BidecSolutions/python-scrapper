"""Migration script to create playbook_jobs table"""
import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./lead_scraper.db").replace("sqlite:///", "")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("The table will be created automatically when the app starts (SQLAlchemy will handle it)")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if playbook_jobs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='playbook_jobs'")
        if cursor.fetchone():
            print("[OK] playbook_jobs table already exists")
            conn.close()
            return
        
        print("[MIGRATING] Creating playbook_jobs table...")
        
        # Create playbook_jobs table
        cursor.execute("""
            CREATE TABLE playbook_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                started_at DATETIME,
                finished_at DATETIME,
                organization_id INTEGER NOT NULL,
                workspace_id INTEGER,
                type VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'queued',
                error_message TEXT,
                params TEXT DEFAULT '{}',
                meta TEXT DEFAULT '{}',
                output_list_id INTEGER,
                estimated_credits INTEGER,
                credits_used INTEGER DEFAULT 0 NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                FOREIGN KEY (output_list_id) REFERENCES lead_lists(id) ON DELETE SET NULL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_playbook_job_org_status ON playbook_jobs(organization_id, status)")
        cursor.execute("CREATE INDEX idx_playbook_job_created ON playbook_jobs(created_at)")
        cursor.execute("CREATE INDEX idx_playbook_job_org_id ON playbook_jobs(organization_id)")
        cursor.execute("CREATE INDEX idx_playbook_job_workspace_id ON playbook_jobs(workspace_id)")
        cursor.execute("CREATE INDEX idx_playbook_job_type ON playbook_jobs(type)")
        cursor.execute("CREATE INDEX idx_playbook_job_status ON playbook_jobs(status)")
        cursor.execute("CREATE INDEX idx_playbook_job_output_list_id ON playbook_jobs(output_list_id)")
        
        conn.commit()
        conn.close()
        print("[OK] Created playbook_jobs table with indexes")
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: If you're using PostgreSQL, run these SQL commands manually:")
        print("""
-- PostgreSQL commands for reference:

CREATE TABLE IF NOT EXISTS playbook_jobs (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    error_message TEXT,
    params JSONB DEFAULT '{}'::jsonb NOT NULL,
    meta JSONB DEFAULT '{}'::jsonb NOT NULL,
    output_list_id INTEGER REFERENCES lead_lists(id) ON DELETE SET NULL,
    estimated_credits INTEGER,
    credits_used INTEGER DEFAULT 0 NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_playbook_job_org_status ON playbook_jobs(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_playbook_job_created ON playbook_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_playbook_job_org_id ON playbook_jobs(organization_id);
CREATE INDEX IF NOT EXISTS idx_playbook_job_workspace_id ON playbook_jobs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_playbook_job_type ON playbook_jobs(type);
CREATE INDEX IF NOT EXISTS idx_playbook_job_status ON playbook_jobs(status);
CREATE INDEX IF NOT EXISTS idx_playbook_job_output_list_id ON playbook_jobs(output_list_id);
        """)

if __name__ == "__main__":
    migrate()

