"""Check if admin user exists and verify credentials"""
import sys
import os
import bcrypt
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

def check_admin_user():
    print("=" * 70)
    print("Checking Admin User")
    print("=" * 70)
    
    db_url = settings.DATABASE_URL
    
    # Convert async URL to sync if needed
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
    
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        email = "admin@admin.com"
        
        # Check if user exists
        result = conn.execute(
            text("SELECT id, email, password_hash, is_active, status FROM users WHERE email = :email"),
            {"email": email}
        )
        user = result.fetchone()
        
        if not user:
            print(f"\n❌ User '{email}' NOT FOUND in database!")
            print("\n💡 Solution: Create the user by running:")
            print("   python create_user_postgres.py")
            return
        
        user_id, db_email, password_hash, is_active, status = user
        
        print(f"\n✅ User found:")
        print(f"   ID: {user_id}")
        print(f"   Email: {db_email}")
        print(f"   Is Active: {is_active}")
        print(f"   Status: {status}")
        print(f"   Password Hash: {password_hash[:50]}...")
        
        # Test password
        test_password = "123123"
        print(f"\n🔐 Testing password: '{test_password}'")
        
        try:
            # Check if password matches
            if password_hash.startswith('$2b$') or password_hash.startswith('$2a$'):
                # bcrypt hash
                is_valid = bcrypt.checkpw(
                    test_password.encode('utf-8'),
                    password_hash.encode('utf-8')
                )
            else:
                print("   ⚠️  Password hash format not recognized (not bcrypt)")
                is_valid = False
            
            if is_valid:
                print("   ✅ Password is CORRECT!")
            else:
                print("   ❌ Password is INCORRECT!")
                print("\n💡 Solution: Update the password by running:")
                print("   python create_user_postgres.py")
        except Exception as e:
            print(f"   ❌ Error checking password: {e}")
            print("\n💡 Solution: Recreate the user by running:")
            print("   python create_user_postgres.py")
        
        # Check user status
        if not is_active:
            print("\n⚠️  User is NOT active!")
        if status != "active":
            print(f"\n⚠️  User status is '{status}' (should be 'active')")
        
        # Check organization
        result = conn.execute(
            text("SELECT organization_id FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        org_id = result.scalar()
        if org_id:
            result = conn.execute(
                text("SELECT name FROM organizations WHERE id = :org_id"),
                {"org_id": org_id}
            )
            org_name = result.scalar()
            print(f"\n📋 Organization:")
            print(f"   ID: {org_id}")
            print(f"   Name: {org_name or 'N/A'}")

if __name__ == "__main__":
    try:
        check_admin_user()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

