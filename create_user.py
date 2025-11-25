"""
Create a dummy user script

Run this script to create a user:
    python create_user.py
"""
import sys
import os
import sqlite3
import bcrypt

def create_user():
    """Create a user using direct SQL"""
    db_path = "lead_scraper.db"
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found: {db_path}")
        print("  Please ensure the database file exists")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        email = "admin@admin.com"
        password = "123123"
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Check if user already exists
        cursor.execute("SELECT id, email FROM users WHERE email = ?", (email,))
        existing = cursor.fetchone()
        
        if existing:
            user_id, existing_email = existing
            print(f"User {email} already exists. Updating password and permissions...")
            cursor.execute("""
                UPDATE users 
                SET is_super_admin = 1,
                    can_use_advanced = 1,
                    status = 'active',
                    password_hash = ?,
                    is_active = 1
                WHERE id = ?
            """, (password_hash, user_id))
            conn.commit()
            print(f"[OK] Updated user {email}")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print(f"  Status: active")
            print(f"  Super Admin: True")
            return
        
        # Get or create default organization
        cursor.execute("SELECT id FROM organizations LIMIT 1")
        org = cursor.fetchone()
        
        if not org:
            cursor.execute("""
                INSERT INTO organizations (name, slug, plan_tier, credits_balance, credits_limit, settings, created_at, updated_at)
                VALUES ('Default Organization', 'default', 'free', 0, 1000, '{}', datetime('now'), datetime('now'))
            """)
            org_id = cursor.lastrowid
            print(f"[OK] Created default organization (ID: {org_id})")
        else:
            org_id = org[0]
        
        # Create user
        cursor.execute("""
            INSERT INTO users (
                email, password_hash, full_name, status, is_super_admin, 
                can_use_advanced, organization_id, role, is_active, 
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            email,
            password_hash,
            "Admin User",
            "active",
            1,  # is_super_admin
            1,  # can_use_advanced
            org_id,
            "admin",
            1,  # is_active
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        print(f"[OK] Successfully created user:")
        print(f"  ID: {user_id}")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  Status: active")
        print(f"  Super Admin: True")
        print(f"  Organization ID: {org_id}")
        
    except Exception as e:
        print(f"[ERROR] Failed to create user: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("Creating user...")
    create_user()
    print("Done!")

