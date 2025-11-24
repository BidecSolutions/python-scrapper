"""
Database migration script to create the duplicate detection tables.

Run this script to create the duplicate_groups and duplicate_leads tables.

Usage:
    python migrations/create_duplicates_tables.py
"""
import sqlite3
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_duplicates_tables(db_path="lead_scraper.db"):
    """Create the duplicate detection tables in SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if tables already exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='duplicate_groups'
        """)
        if cursor.fetchone():
            print("Table 'duplicate_groups' already exists. Skipping creation.")
        else:
            # Create duplicate_groups table
            cursor.execute("""
                CREATE TABLE duplicate_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Multi-tenant
                    organization_id INTEGER NOT NULL,
                    workspace_id INTEGER,
                    
                    -- Group metadata
                    confidence_score REAL NOT NULL DEFAULT 0.0,
                    match_reason VARCHAR(255),
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    
                    -- Canonical lead (the one we keep after merge)
                    canonical_lead_id INTEGER,
                    
                    -- Foreign keys
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                    FOREIGN KEY (canonical_lead_id) REFERENCES leads(id) ON DELETE SET NULL
                )
            """)

            # Create indexes for duplicate_groups
            cursor.execute("""
                CREATE INDEX idx_duplicate_groups_org_status 
                ON duplicate_groups(organization_id, status)
            """)
            
            cursor.execute("""
                CREATE INDEX idx_duplicate_groups_confidence 
                ON duplicate_groups(confidence_score)
            """)
            
            print("[OK] Successfully created 'duplicate_groups' table with indexes")

        # Check if duplicate_leads table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='duplicate_leads'
        """)
        if cursor.fetchone():
            print("Table 'duplicate_leads' already exists. Skipping creation.")
        else:
            # Create duplicate_leads table
            cursor.execute("""
                CREATE TABLE duplicate_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Foreign keys
                    duplicate_group_id INTEGER NOT NULL,
                    lead_id INTEGER NOT NULL,
                    
                    -- Match metadata
                    similarity_score REAL NOT NULL DEFAULT 0.0,
                    matched_fields TEXT NOT NULL DEFAULT '[]',  -- JSON stored as TEXT
                    
                    -- Foreign keys
                    FOREIGN KEY (duplicate_group_id) REFERENCES duplicate_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
                )
            """)

            # Create indexes for duplicate_leads
            cursor.execute("""
                CREATE INDEX idx_duplicate_leads_group 
                ON duplicate_leads(duplicate_group_id)
            """)
            
            cursor.execute("""
                CREATE INDEX idx_duplicate_leads_lead 
                ON duplicate_leads(lead_id)
            """)
            
            cursor.execute("""
                CREATE UNIQUE INDEX idx_duplicate_leads_unique 
                ON duplicate_leads(duplicate_group_id, lead_id)
            """)
            
            print("[OK] Successfully created 'duplicate_leads' table with indexes")

        conn.commit()
        print("Migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create duplicate detection tables")
    parser.add_argument(
        "--db",
        default="lead_scraper.db",
        help="Path to SQLite database file (default: lead_scraper.db)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db):
        print(f"[ERROR] Database file not found: {args.db}")
        print("  Please ensure the database file exists or specify the correct path with --db")
        sys.exit(1)
    
    print(f"Creating duplicate detection tables in {args.db}...")
    create_duplicates_tables(args.db)

