"""Migration script to add LeadList tables"""
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
        
        # Check if lead_lists table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lead_lists'")
        if cursor.fetchone():
            print("[OK] lead_lists table already exists")
        else:
            cursor.execute("""
                CREATE TABLE lead_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    organization_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    is_campaign_ready BOOLEAN NOT NULL DEFAULT 0,
                    tags VARCHAR(500),
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX idx_lead_list_org_name ON lead_lists(organization_id, name)")
            print("[OK] Created lead_lists table")
        
        # Check if lead_list_leads table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lead_list_leads'")
        if cursor.fetchone():
            print("[OK] lead_list_leads table already exists")
        else:
            cursor.execute("""
                CREATE TABLE lead_list_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    list_id INTEGER NOT NULL,
                    lead_id INTEGER NOT NULL,
                    added_by_user_id INTEGER,
                    notes TEXT,
                    FOREIGN KEY (list_id) REFERENCES lead_lists(id) ON DELETE CASCADE,
                    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
                    FOREIGN KEY (added_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
                    UNIQUE(list_id, lead_id)
                )
            """)
            cursor.execute("CREATE INDEX idx_lead_list_lead_list ON lead_list_leads(list_id)")
            cursor.execute("CREATE INDEX idx_lead_list_lead_lead ON lead_list_leads(lead_id)")
            print("[OK] Created lead_list_leads table")
        
        conn.commit()
        conn.close()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        print("\nNote: If you're using PostgreSQL, run these SQL commands manually:")
        print("""
CREATE TABLE lead_lists (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_campaign_ready BOOLEAN NOT NULL DEFAULT FALSE,
    tags VARCHAR(500)
);

CREATE INDEX idx_lead_list_org_name ON lead_lists(organization_id, name);

CREATE TABLE lead_list_leads (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    list_id INTEGER NOT NULL REFERENCES lead_lists(id) ON DELETE CASCADE,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    added_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    UNIQUE(list_id, lead_id)
);

CREATE INDEX idx_lead_list_lead_list ON lead_list_leads(list_id);
CREATE INDEX idx_lead_list_lead_lead ON lead_list_leads(lead_id);
        """)

if __name__ == "__main__":
    migrate()

