"""Migration script to add workspace_id columns to scrape_jobs and leads tables"""
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
        
        # Check if workspaces table exists first (required for foreign key)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workspaces'")
        if not cursor.fetchone():
            print("[WARNING] workspaces table does not exist. Creating it first...")
            # Create workspaces table (minimal structure)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workspaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    organization_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workspace_org ON workspaces(organization_id)")
            print("[OK] Created workspaces table")
        
        # Check if scrape_jobs.workspace_id exists
        cursor.execute("PRAGMA table_info(scrape_jobs)")
        scrape_jobs_columns = [col[1] for col in cursor.fetchall()]
        
        if "workspace_id" not in scrape_jobs_columns:
            print("[MIGRATING] Adding workspace_id column to scrape_jobs table...")
            # SQLite doesn't support adding foreign keys directly, so we add the column first
            # then create the index
            cursor.execute("""
                ALTER TABLE scrape_jobs 
                ADD COLUMN workspace_id INTEGER
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_scrape_jobs_workspace 
                ON scrape_jobs(workspace_id)
            """)
            print("[OK] Added workspace_id column to scrape_jobs table")
        else:
            print("[OK] scrape_jobs.workspace_id column already exists")
        
        # Check if leads.workspace_id exists and other missing columns
        cursor.execute("PRAGMA table_info(leads)")
        leads_columns = [col[1] for col in cursor.fetchall()]
        
        columns_to_add = {
            "workspace_id": ("INTEGER", "idx_leads_workspace"),
            "company_id": ("INTEGER", "idx_leads_company"),
            "owner_user_id": ("INTEGER", "idx_leads_owner"),
            "health_score": ("NUMERIC(5, 2)", "idx_leads_health_score"),
            "health_score_last_calculated_at": ("DATETIME", None),
            "next_action": ("VARCHAR(50)", "idx_leads_next_action"),
            "next_action_reason": ("TEXT", None),
            "next_action_last_calculated_at": ("DATETIME", None),
        }
        
        for col_name, (col_type, index_name) in columns_to_add.items():
            if col_name not in leads_columns:
                print(f"[MIGRATING] Adding {col_name} column to leads table...")
                cursor.execute(f"""
                    ALTER TABLE leads 
                    ADD COLUMN {col_name} {col_type}
                """)
                if index_name:
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON leads({col_name})
                    """)
                print(f"[OK] Added {col_name} column to leads table")
            else:
                print(f"[OK] leads.{col_name} column already exists")
        
        # Check if api_keys table exists and add missing columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_keys'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(api_keys)")
            api_keys_columns = [col[1] for col in cursor.fetchall()]
            
            # List of columns that need to be added to api_keys table
            api_keys_columns_to_add = {
                "workspace_id": ("INTEGER", "idx_api_key_workspace"),
                "scopes": ("TEXT DEFAULT ''", None),
                "rate_limit_per_hour": ("INTEGER", None),
                "rate_limit_per_day": ("INTEGER", None),
                "active": ("BOOLEAN DEFAULT 1", "idx_api_key_active"),
                "expires_at": ("DATETIME", None),
                "last_used_ip": ("VARCHAR(45)", None),
                "total_requests": ("INTEGER DEFAULT 0", None),
                "description": ("TEXT", None),
                "created_by_user_id": ("INTEGER", None),
            }
            
            for col_name, (col_type, index_name) in api_keys_columns_to_add.items():
                if col_name not in api_keys_columns:
                    print(f"[MIGRATING] Adding {col_name} column to api_keys table...")
                    cursor.execute(f"""
                        ALTER TABLE api_keys 
                        ADD COLUMN {col_name} {col_type}
                    """)
                    if index_name:
                        # Extract column name from col_type (remove DEFAULT etc.)
                        col_name_clean = col_type.split()[0] if 'DEFAULT' in col_type else col_name
                        if col_name_clean != col_name:
                            col_name_clean = col_name
                        cursor.execute(f"""
                            CREATE INDEX IF NOT EXISTS {index_name} 
                            ON api_keys({col_name_clean})
                        """)
                    print(f"[OK] Added {col_name} column to api_keys table")
                else:
                    print(f"[OK] api_keys.{col_name} column already exists")
            
            # Handle old "status" column - migrate data if status exists
            # Refresh column list after adding columns
            cursor.execute("PRAGMA table_info(api_keys)")
            api_keys_columns_after = [col[1] for col in cursor.fetchall()]
            
            if "status" in api_keys_columns_after and "active" in api_keys_columns_after:
                print("[MIGRATING] Migrating data from 'status' to 'active' column...")
                cursor.execute("""
                    UPDATE api_keys 
                    SET active = CASE WHEN status = 'active' THEN 1 ELSE 0 END
                    WHERE active IS NULL OR active = 1
                """)
                print("[OK] Migrated status data to active column")
        
        conn.commit()
        conn.close()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: If you're using PostgreSQL, run these SQL commands manually:")
        print("""
-- First, ensure workspaces table exists
CREATE TABLE IF NOT EXISTS workspaces (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_workspace_org ON workspaces(organization_id);

-- Add workspace_id to scrape_jobs
ALTER TABLE scrape_jobs 
ADD COLUMN IF NOT EXISTS workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_scrape_jobs_workspace ON scrape_jobs(workspace_id);

-- Add workspace_id to leads
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_leads_workspace ON leads(workspace_id);

-- Add workspace_id to api_keys
ALTER TABLE api_keys 
ADD COLUMN IF NOT EXISTS workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_api_key_workspace ON api_keys(workspace_id);
        """)

if __name__ == "__main__":
    migrate()

