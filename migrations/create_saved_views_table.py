"""
Database migration script to create the saved_views table.

Run this script to create the saved_views table in your database.

Usage:
    python migrations/create_saved_views_table.py
"""
import sqlite3
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_saved_views_table(db_path="lead_scraper.db"):
    """Create the saved_views table in SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='saved_views'
        """)
        if cursor.fetchone():
            print("Table 'saved_views' already exists. Skipping creation.")
            return

        # Create saved_views table
        cursor.execute("""
            CREATE TABLE saved_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                -- Multi-tenant
                organization_id INTEGER NOT NULL,
                user_id INTEGER,
                workspace_id INTEGER,
                
                -- View metadata
                name VARCHAR(255) NOT NULL,
                page_type VARCHAR(50) NOT NULL,
                is_pinned BOOLEAN NOT NULL DEFAULT 0,
                is_shared BOOLEAN NOT NULL DEFAULT 0,
                
                -- Filter & sort configuration
                filters TEXT NOT NULL DEFAULT '{}',  -- JSON stored as TEXT in SQLite
                sort_by VARCHAR(50),
                sort_order VARCHAR(10) DEFAULT 'desc',
                
                -- Column visibility preferences
                visible_columns TEXT,  -- JSON stored as TEXT in SQLite
                
                -- Usage tracking
                last_used_at TIMESTAMP,
                usage_count INTEGER NOT NULL DEFAULT 0,
                
                -- Foreign keys
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX idx_saved_views_org_page_pinned 
            ON saved_views(organization_id, page_type, is_pinned)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_saved_views_user_page 
            ON saved_views(user_id, page_type)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_saved_views_page_type 
            ON saved_views(page_type)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_saved_views_last_used 
            ON saved_views(last_used_at)
        """)

        conn.commit()
        print("[OK] Successfully created 'saved_views' table with indexes")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error creating table: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create saved_views table")
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
    
    print(f"Creating saved_views table in {args.db}...")
    create_saved_views_table(args.db)
    print("Migration completed successfully!")

