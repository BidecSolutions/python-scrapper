"""Migration script to create deals table"""
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
        
        # Check if deals table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deals'")
        if cursor.fetchone():
            print("[OK] deals table already exists")
            conn.close()
            return
        
        print("[MIGRATING] Creating deals table...")
        
        # Create deals table
        cursor.execute("""
            CREATE TABLE deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                workspace_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                company_id INTEGER,
                primary_lead_id INTEGER,
                owner_user_id INTEGER,
                stage VARCHAR(50) NOT NULL DEFAULT 'new',
                value NUMERIC(12, 2),
                currency VARCHAR(10) DEFAULT 'USD' NOT NULL,
                expected_close_date DATETIME,
                source_campaign_id INTEGER,
                source_segment_id INTEGER,
                lost_reason TEXT,
                lost_at DATETIME,
                won_at DATETIME,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
                FOREIGN KEY (primary_lead_id) REFERENCES leads(id) ON DELETE SET NULL,
                FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (source_segment_id) REFERENCES segments(id) ON DELETE SET NULL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_deal_workspace_stage ON deals(workspace_id, stage)")
        cursor.execute("CREATE INDEX idx_deal_owner_stage ON deals(owner_user_id, stage)")
        cursor.execute("CREATE INDEX idx_deal_expected_close ON deals(expected_close_date)")
        cursor.execute("CREATE INDEX idx_deal_workspace_id ON deals(workspace_id)")
        cursor.execute("CREATE INDEX idx_deal_organization_id ON deals(organization_id)")
        cursor.execute("CREATE INDEX idx_deal_company_id ON deals(company_id)")
        cursor.execute("CREATE INDEX idx_deal_primary_lead_id ON deals(primary_lead_id)")
        cursor.execute("CREATE INDEX idx_deal_owner_user_id ON deals(owner_user_id)")
        cursor.execute("CREATE INDEX idx_deal_stage ON deals(stage)")
        cursor.execute("CREATE INDEX idx_deal_created_at ON deals(created_at)")
        
        # Add deal_id to activities table if it exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(activities)")
            activity_columns = [col[1] for col in cursor.fetchall()]
            if "deal_id" not in activity_columns:
                print("[MIGRATING] Adding deal_id column to activities table...")
                cursor.execute("ALTER TABLE activities ADD COLUMN deal_id INTEGER")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_deal_id ON activities(deal_id)")
                print("[OK] Added deal_id column to activities table")
            else:
                print("[OK] activities.deal_id column already exists")
        else:
            print("[NOTE] activities table does not exist yet - will be created by SQLAlchemy")
        
        # Add deal_id to lead_tasks and lead_notes if they don't exist
        cursor.execute("PRAGMA table_info(lead_tasks)")
        task_columns = [col[1] for col in cursor.fetchall()]
        if "deal_id" not in task_columns:
            print("[MIGRATING] Adding deal_id column to lead_tasks table...")
            cursor.execute("ALTER TABLE lead_tasks ADD COLUMN deal_id INTEGER")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lead_task_deal_id ON lead_tasks(deal_id)")
            # Make lead_id nullable (for deal-only tasks)
            print("[NOTE] lead_tasks.lead_id should be nullable for deal-only tasks")
            print("[OK] Added deal_id column to lead_tasks table")
        else:
            print("[OK] lead_tasks.deal_id column already exists")
        
        cursor.execute("PRAGMA table_info(lead_notes)")
        note_columns = [col[1] for col in cursor.fetchall()]
        if "deal_id" not in note_columns:
            print("[MIGRATING] Adding deal_id column to lead_notes table...")
            cursor.execute("ALTER TABLE lead_notes ADD COLUMN deal_id INTEGER")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lead_note_deal_id ON lead_notes(deal_id)")
            # Make lead_id nullable (for deal-only notes)
            print("[NOTE] lead_notes.lead_id should be nullable for deal-only notes")
            print("[OK] Added deal_id column to lead_notes table")
        else:
            print("[OK] lead_notes.deal_id column already exists")
        
        conn.commit()
        conn.close()
        print("[OK] Created deals table with indexes")
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: If you're using PostgreSQL, run these SQL commands manually:")
        print("""
-- PostgreSQL commands for reference:

CREATE TABLE IF NOT EXISTS deals (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    primary_lead_id INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    stage VARCHAR(50) NOT NULL DEFAULT 'new',
    value NUMERIC(12, 2),
    currency VARCHAR(10) DEFAULT 'USD' NOT NULL,
    expected_close_date TIMESTAMP WITH TIME ZONE,
    source_campaign_id INTEGER,
    source_segment_id INTEGER REFERENCES segments(id) ON DELETE SET NULL,
    lost_reason TEXT,
    lost_at TIMESTAMP WITH TIME ZONE,
    won_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_deal_workspace_stage ON deals(workspace_id, stage);
CREATE INDEX IF NOT EXISTS idx_deal_owner_stage ON deals(owner_user_id, stage);
CREATE INDEX IF NOT EXISTS idx_deal_expected_close ON deals(expected_close_date);
CREATE INDEX IF NOT EXISTS idx_deal_workspace_id ON deals(workspace_id);
CREATE INDEX IF NOT EXISTS idx_deal_organization_id ON deals(organization_id);
CREATE INDEX IF NOT EXISTS idx_deal_company_id ON deals(company_id);
CREATE INDEX IF NOT EXISTS idx_deal_primary_lead_id ON deals(primary_lead_id);
CREATE INDEX IF NOT EXISTS idx_deal_owner_user_id ON deals(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_deal_stage ON deals(stage);
CREATE INDEX IF NOT EXISTS idx_deal_created_at ON deals(created_at);

-- Add deal_id to activities
ALTER TABLE activities ADD COLUMN IF NOT EXISTS deal_id INTEGER REFERENCES deals(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_activity_deal_id ON activities(deal_id);

-- Add deal_id to lead_tasks and make lead_id nullable
ALTER TABLE lead_tasks ADD COLUMN IF NOT EXISTS deal_id INTEGER REFERENCES deals(id) ON DELETE CASCADE;
ALTER TABLE lead_tasks ALTER COLUMN lead_id DROP NOT NULL; -- PostgreSQL syntax
CREATE INDEX IF NOT EXISTS idx_lead_task_deal_id ON lead_tasks(deal_id);

-- Add deal_id to lead_notes and make lead_id nullable
ALTER TABLE lead_notes ADD COLUMN IF NOT EXISTS deal_id INTEGER REFERENCES deals(id) ON DELETE CASCADE;
ALTER TABLE lead_notes ALTER COLUMN lead_id DROP NOT NULL; -- PostgreSQL syntax
CREATE INDEX IF NOT EXISTS idx_lead_note_deal_id ON lead_notes(deal_id);
        """)

if __name__ == "__main__":
    migrate()

