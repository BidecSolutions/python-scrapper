"""
Database migration script to create the activities table.

Run this script to create the activities table in your database.

Usage:
    python migrations/create_activities_table.py
"""
import sqlite3
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_activities_table(db_path="lead_scraper.db"):
    """Create the activities table in SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='activities'
        """)
        if cursor.fetchone():
            print("Table 'activities' already exists. Skipping creation.")
            return

        # Create activities table
        # Note: SQLite doesn't support ENUM, so we use TEXT for type
        cursor.execute("""
            CREATE TABLE activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                -- Multi-tenant
                workspace_id INTEGER,
                organization_id INTEGER NOT NULL,
                
                -- Event type (stored as TEXT since SQLite doesn't support ENUM)
                type VARCHAR(50) NOT NULL,
                
                -- Actor (who did it, optional for system events)
                actor_user_id INTEGER,
                
                -- Related objects (nullable, depending on event type)
                lead_id INTEGER,
                list_id INTEGER,
                campaign_id INTEGER,
                task_id INTEGER,
                job_id INTEGER,
                note_id INTEGER,
                deal_id INTEGER,
                
                -- Flexible JSON payload for extra info
                meta TEXT NOT NULL DEFAULT '{}',  -- JSON stored as TEXT in SQLite
                
                -- Foreign keys
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
                FOREIGN KEY (list_id) REFERENCES lead_lists(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES lead_tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (job_id) REFERENCES scrape_jobs(id) ON DELETE CASCADE,
                FOREIGN KEY (note_id) REFERENCES lead_notes(id) ON DELETE CASCADE,
                FOREIGN KEY (deal_id) REFERENCES deals(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX idx_activities_id ON activities(id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_created_at ON activities(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_workspace_id ON activities(workspace_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_organization_id ON activities(organization_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_type ON activities(type)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_actor_user_id ON activities(actor_user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_lead_id ON activities(lead_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_list_id ON activities(list_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_campaign_id ON activities(campaign_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_task_id ON activities(task_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_job_id ON activities(job_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_note_id ON activities(note_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activities_deal_id ON activities(deal_id)
        """)
        
        # Create composite indexes as defined in the model
        cursor.execute("""
            CREATE INDEX idx_activity_workspace_created 
            ON activities(workspace_id, created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activity_lead_created 
            ON activities(lead_id, created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_activity_type_created 
            ON activities(type, created_at)
        """)

        conn.commit()
        print("[OK] Successfully created 'activities' table with indexes")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error creating table: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create activities table")
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
    
    print(f"Creating activities table in {args.db}...")
    create_activities_table(args.db)
    print("Migration completed successfully!")

