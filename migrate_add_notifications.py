"""Migration script to create notifications table"""
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
        
        # Check if notifications table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'")
        if cursor.fetchone():
            print("[OK] notifications table already exists")
            conn.close()
            return
        
        print("[MIGRATING] Creating notifications table...")
        
        # Create notifications table
        cursor.execute("""
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                workspace_id INTEGER NOT NULL,
                user_id INTEGER,
                type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                body TEXT,
                target_url VARCHAR(500),
                meta TEXT DEFAULT '{}',
                is_read BOOLEAN DEFAULT 0 NOT NULL,
                is_archived BOOLEAN DEFAULT 0 NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_notification_workspace_user_read ON notifications(workspace_id, user_id, is_read)")
        cursor.execute("CREATE INDEX idx_notification_created ON notifications(created_at)")
        cursor.execute("CREATE INDEX idx_notification_workspace_id ON notifications(workspace_id)")
        cursor.execute("CREATE INDEX idx_notification_user_id ON notifications(user_id)")
        cursor.execute("CREATE INDEX idx_notification_type ON notifications(type)")
        cursor.execute("CREATE INDEX idx_notification_is_read ON notifications(is_read)")
        cursor.execute("CREATE INDEX idx_notification_is_archived ON notifications(is_archived)")
        
        conn.commit()
        conn.close()
        print("[OK] Created notifications table with indexes")
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: If you're using PostgreSQL, run these SQL commands manually:")
        print("""
-- PostgreSQL commands for reference:

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    target_url VARCHAR(500),
    meta JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    is_archived BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_workspace_user_read ON notifications(workspace_id, user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notification_created ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notification_workspace_id ON notifications(workspace_id);
CREATE INDEX IF NOT EXISTS idx_notification_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notification_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notification_is_archived ON notifications(is_archived);
        """)

if __name__ == "__main__":
    migrate()

