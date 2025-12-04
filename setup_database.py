"""Interactive script to set up database connection"""
import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with database configuration"""
    env_path = Path(__file__).parent / ".env"
    
    # Check if .env already exists
    if env_path.exists():
        response = input(f".env file already exists. Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping .env file creation.")
            return False
    
    # Database connection details
    db_url = "postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper"
    
    # JWT Secret Key
    jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-min-32-chars-please-use-a-secure-random-string")
    
    env_content = f"""# Database Configuration
# PostgreSQL connection string for Supabase
# Password is URL-encoded: @ becomes %40
DATABASE_URL={db_url}

# JWT Secret Key (change in production!)
JWT_SECRET_KEY={jwt_secret}
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ Created .env file at: {env_path}")
        print("\nDatabase configuration:")
        print(f"  Database: Lead_scrapper")
        print(f"  Host: aws-1-ap-northeast-2.pooler.supabase.com:6543")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def main():
    print("=" * 60)
    print("Database Setup Script")
    print("=" * 60)
    print("\nThis script will create a .env file with your PostgreSQL connection.")
    print("\nDatabase details:")
    print("  - Database: Lead_scrapper")
    print("  - Host: aws-1-ap-northeast-2.pooler.supabase.com:6543")
    print("  - Username: postgres.aashvhvwiayvniidvaqk")
    print()
    
    if create_env_file():
        print("\n" + "=" * 60)
        print("Next steps:")
        print("=" * 60)
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Test connection: python test_db_connection.py")
        print("3. Initialize tables: python init_db.py")
        print("4. Create admin user: python create_user.py")
        print()
    else:
        print("\nYou can manually create the .env file. See DATABASE_SETUP.md for details.")

if __name__ == "__main__":
    main()

