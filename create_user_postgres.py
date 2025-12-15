"""
Create a user script for PostgreSQL

Run this script to create a user:
    python create_user_postgres.py
"""
import os
from datetime import datetime

import bcrypt
from sqlalchemy import text

from app.core.db import engine

DEFAULT_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "founder@scraper.app")
DEFAULT_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "LeadFlow@2025!")
DEFAULT_WORKSPACE_SLUG = os.getenv("DEFAULT_WORKSPACE_SLUG", "default-workspace")


def _ensure_workspace(conn, org_id: int, user_id: int) -> int:
    """Ensure the organization has at least one workspace and membership for the admin."""
    workspace_result = conn.execute(
        text("SELECT id FROM workspaces WHERE organization_id = :org_id LIMIT 1"),
        {"org_id": org_id},
    ).fetchone()

    if workspace_result:
        workspace_id = workspace_result[0]
    else:
        workspace_row = conn.execute(
            text(
                """
                INSERT INTO workspaces (name, slug, description, organization_id, created_at, updated_at)
                VALUES (:name, :slug, :description, :organization_id, :created_at, :updated_at)
                RETURNING id
                """
            ),
            {
                "name": "Default Workspace",
                "slug": DEFAULT_WORKSPACE_SLUG,
                "description": "Auto-created for the default admin user",
                "organization_id": org_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        ).fetchone()
        workspace_id = workspace_row[0]
        print(f"[OK] Created default workspace (ID: {workspace_id})")

    membership = conn.execute(
        text(
            """
            SELECT id FROM workspace_members
            WHERE workspace_id = :workspace_id AND user_id = :user_id
            """
        ),
        {"workspace_id": workspace_id, "user_id": user_id},
    ).fetchone()

    if not membership:
        conn.execute(
            text(
                """
                INSERT INTO workspace_members (
                    workspace_id, user_id, role, accepted_at, created_at, updated_at
                ) VALUES (
                    :workspace_id, :user_id, 'owner', :accepted_at, :created_at, :updated_at
                )
                """
            ),
            {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "accepted_at": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        )
        print(f"[OK] Added user {user_id} to workspace {workspace_id} as owner")

    conn.execute(
        text(
            """
            UPDATE users
            SET current_workspace_id = :workspace_id, updated_at = :updated_at
            WHERE id = :user_id
            """
        ),
        {"workspace_id": workspace_id, "updated_at": datetime.utcnow(), "user_id": user_id},
    )

    return workspace_id


def create_user():
    """Create a user using raw SQL (works with PostgreSQL)"""

    email = DEFAULT_EMAIL
    password = DEFAULT_PASSWORD
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    with engine.connect() as conn:
        try:
            # Start transaction
            trans = conn.begin()
            
            # Check if user already exists
            result = conn.execute(text("SELECT id, email FROM users WHERE email = :email"), {"email": email})
            existing = result.fetchone()
            
            if existing:
                user_id, _ = existing
                print(f"User {email} already exists. Updating password and permissions...")
                conn.execute(
                    text(
                        """
                        UPDATE users
                        SET is_super_admin = true,
                            can_use_advanced = true,
                            status = 'active',
                            password_hash = :password_hash,
                            is_active = true,
                            updated_at = :updated_at
                        WHERE id = :user_id
                        """
                    ),
                    {
                        "password_hash": password_hash,
                        "user_id": user_id,
                        "updated_at": datetime.utcnow(),
                    },
                )
                org_id = conn.execute(
                    text("SELECT organization_id FROM users WHERE id = :user_id"),
                    {"user_id": user_id},
                ).scalar()
                workspace_id = _ensure_workspace(conn, org_id, user_id)
                trans.commit()
                print(f"[OK] Updated user {email}")
                print(f"  Email: {email}")
                print(f"  Password: {password}")
                print(f"  Status: active")
                print(f"  Super Admin: True")
                print(f"  Workspace ID: {workspace_id}")
                return
            
            # Get or create default organization
            org_result = conn.execute(text("SELECT id FROM organizations LIMIT 1"))
            org = org_result.fetchone()
            
            if not org:
                conn.execute(text("""
                    INSERT INTO organizations (name, slug, plan_tier, credits_balance, credits_limit, settings, created_at, updated_at)
                    VALUES ('Default Organization', 'default', 'free', 0, 1000, '{}', :created_at, :updated_at)
                    RETURNING id
                """), {
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                org_result = conn.execute(text("SELECT id FROM organizations WHERE slug = 'default'"))
                org = org_result.fetchone()
                org_id = org[0]
                print(f"[OK] Created default organization (ID: {org_id})")
            else:
                org_id = org[0]
            
            # Create user
            conn.execute(text("""
                INSERT INTO users (
                    email, password_hash, full_name, status, is_super_admin, 
                    can_use_advanced, organization_id, role, is_active, 
                    created_at, updated_at
                )
                VALUES (
                    :email, :password_hash, :full_name, :status, :is_super_admin,
                    :can_use_advanced, :organization_id, :role, :is_active,
                    :created_at, :updated_at
                )
            """), {
                "email": email,
                "password_hash": password_hash,
                "full_name": "Admin User",
                "status": "active",
                "is_super_admin": True,
                "can_use_advanced": True,
                "organization_id": org_id,
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            # Get the created user ID
            user_result = conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
            user = user_result.fetchone()
            user_id = user[0]
            
            workspace_id = _ensure_workspace(conn, org_id, user_id)

            trans.commit()
            
            print(f"[OK] Successfully created user:")
            print(f"  ID: {user_id}")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print(f"  Status: active")
            print(f"  Super Admin: True")
            print(f"  Organization ID: {org_id}")
            print(f"  Workspace ID: {workspace_id}")
            
        except Exception as e:
            trans.rollback()
            print(f"[ERROR] Failed to create user: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    print("Creating user...")
    create_user()
    print("\n" + "="*60)
    print("Login Credentials:")
    print("="*60)
    print(f"Email: {DEFAULT_EMAIL}")
    print(f"Password: {DEFAULT_PASSWORD}")
    print("="*60)
    print("Done!")
