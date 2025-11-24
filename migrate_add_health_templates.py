"""Migration script to create health and template tables"""
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
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workspace_daily_metrics'")
        if cursor.fetchone():
            print("[OK] workspace_daily_metrics table already exists")
        else:
            print("[MIGRATING] Creating workspace_daily_metrics table...")
            cursor.execute("""
                CREATE TABLE workspace_daily_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    workspace_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    emails_sent INTEGER DEFAULT 0 NOT NULL,
                    emails_bounced INTEGER DEFAULT 0 NOT NULL,
                    emails_spam_complaints INTEGER DEFAULT 0 NOT NULL,
                    emails_unsubscribed INTEGER DEFAULT 0 NOT NULL,
                    emails_verified INTEGER DEFAULT 0 NOT NULL,
                    ver_valid INTEGER DEFAULT 0 NOT NULL,
                    ver_invalid INTEGER DEFAULT 0 NOT NULL,
                    ver_risky INTEGER DEFAULT 0 NOT NULL,
                    ver_unknown INTEGER DEFAULT 0 NOT NULL,
                    campaign_sends INTEGER DEFAULT 0 NOT NULL,
                    campaign_opens INTEGER DEFAULT 0 NOT NULL,
                    campaign_replies INTEGER DEFAULT 0 NOT NULL,
                    linkedin_success INTEGER DEFAULT 0 NOT NULL,
                    linkedin_failed INTEGER DEFAULT 0 NOT NULL,
                    jobs_started INTEGER DEFAULT 0 NOT NULL,
                    jobs_failed INTEGER DEFAULT 0 NOT NULL,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE UNIQUE INDEX idx_workspace_daily_metrics_workspace_date ON workspace_daily_metrics(workspace_id, date)")
            cursor.execute("CREATE INDEX idx_workspace_daily_metrics_workspace_id ON workspace_daily_metrics(workspace_id)")
            cursor.execute("CREATE INDEX idx_workspace_daily_metrics_date ON workspace_daily_metrics(date)")
            print("[OK] Created workspace_daily_metrics table")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workspace_health_snapshots'")
        if cursor.fetchone():
            print("[OK] workspace_health_snapshots table already exists")
        else:
            print("[MIGRATING] Creating workspace_health_snapshots table...")
            cursor.execute("""
                CREATE TABLE workspace_health_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    workspace_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    health_score INTEGER NOT NULL,
                    details TEXT DEFAULT '{}',
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE UNIQUE INDEX idx_workspace_health_workspace_date ON workspace_health_snapshots(workspace_id, date)")
            cursor.execute("CREATE INDEX idx_workspace_health_workspace_id ON workspace_health_snapshots(workspace_id)")
            cursor.execute("CREATE INDEX idx_workspace_health_date ON workspace_health_snapshots(date)")
            print("[OK] Created workspace_health_snapshots table")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='templates'")
        if cursor.fetchone():
            print("[OK] templates table already exists")
        else:
            print("[MIGRATING] Creating templates table...")
            cursor.execute("""
                CREATE TABLE templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    workspace_id INTEGER,
                    scope VARCHAR(50) DEFAULT 'workspace' NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    kind VARCHAR(50) DEFAULT 'email' NOT NULL,
                    subject VARCHAR(255),
                    body TEXT,
                    status VARCHAR(50) DEFAULT 'draft' NOT NULL,
                    locked BOOLEAN DEFAULT 0 NOT NULL,
                    created_by_user_id INTEGER NOT NULL,
                    approved_by_user_id INTEGER,
                    tags TEXT DEFAULT '[]',
                    meta TEXT DEFAULT '{}',
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (approved_by_user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            cursor.execute("CREATE INDEX idx_template_workspace_status ON templates(workspace_id, status)")
            cursor.execute("CREATE INDEX idx_template_created_by ON templates(created_by_user_id)")
            cursor.execute("CREATE INDEX idx_template_workspace_id ON templates(workspace_id)")
            cursor.execute("CREATE INDEX idx_template_scope ON templates(scope)")
            cursor.execute("CREATE INDEX idx_template_status ON templates(status)")
            print("[OK] Created templates table")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='template_governance'")
        if cursor.fetchone():
            print("[OK] template_governance table already exists")
        else:
            print("[MIGRATING] Creating template_governance table...")
            cursor.execute("""
                CREATE TABLE template_governance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    workspace_id INTEGER NOT NULL UNIQUE,
                    require_approval_for_new_templates BOOLEAN DEFAULT 0 NOT NULL,
                    restrict_to_approved_only BOOLEAN DEFAULT 0 NOT NULL,
                    allow_personal_templates BOOLEAN DEFAULT 1 NOT NULL,
                    require_unsubscribe BOOLEAN DEFAULT 1 NOT NULL,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE UNIQUE INDEX idx_template_governance_workspace_id ON template_governance(workspace_id)")
            print("[OK] Created template_governance table")
        
        conn.commit()
        conn.close()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate()

