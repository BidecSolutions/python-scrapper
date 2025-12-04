"""Fix Supabase connection to match dashboard"""
import os
import sys

# Get the .env file path
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

print("=" * 70)
print("Supabase Connection Fix")
print("=" * 70)

# Read current .env
current_url = None
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                current_url = line.strip()
                break

if current_url:
    print(f"\nCurrent DATABASE_URL:")
    print(f"  {current_url[:80]}...")
    
    # Check if using pooler
    if ':6543' in current_url:
        print("\n⚠️  Currently using CONNECTION POOLER (port 6543)")
        print("   This connects to Lead_scrapper but Supabase dashboard shows 'postgres'")
        
        # Create new connection string for direct connection
        new_url = current_url.replace(':6543', ':5432')
        
        print(f"\n✅ Recommended DATABASE_URL (Direct connection):")
        print(f"   {new_url}")
        
        # Ask if user wants to update
        print("\n" + "=" * 70)
        print("OPTION 1: Update .env to use direct connection")
        print("=" * 70)
        print("This will make your app connect the same way Supabase dashboard does.")
        print("\nTo apply this fix, update your .env file:")
        print(f"\nReplace:")
        print(f"  {current_url}")
        print(f"\nWith:")
        print(f"  {new_url}")
        
    else:
        print("\n✅ Already using direct connection")
else:
    print("\n⚠️  No DATABASE_URL found in .env")

print("\n" + "=" * 70)
print("OPTION 2: Use this SQL query in Supabase SQL Editor")
print("=" * 70)
print("""
-- This query will show all databases
SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database 
WHERE datistemplate = false 
ORDER BY datname;

-- Then to see tables in Lead_scrapper, you need to:
-- 1. Check if Supabase dashboard has a database selector dropdown
-- 2. Or use the connection string that points to Lead_scrapper
""")

print("\n" + "=" * 70)
print("OPTION 3: Check Supabase Project Settings")
print("=" * 70)
print("""
1. Go to: https://supabase.com/dashboard/project/aashvhvwiayvniidvaqk/settings/database
2. Look for "Connection string" section
3. Check if there's a way to select which database to view
4. Look for "Database" or "Schema" selector in Table Editor
""")

print("\n" + "=" * 70)
print("Quick Test Query for Supabase SQL Editor")
print("=" * 70)
print("""
Run this in Supabase SQL Editor to see all databases:

SELECT datname FROM pg_database WHERE datistemplate = false;
""")

