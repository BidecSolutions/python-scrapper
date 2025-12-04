# How to View Your Database in Supabase Dashboard

## Your Database Connection Details
- **Database Name**: `Lead_scrapper`
- **Host**: `aws-1-ap-northeast-2.pooler.supabase.com:6543`
- **Status**: ✅ Connected (75 tables exist)

## Steps to View Database in Supabase Dashboard

### 1. Log into Supabase Dashboard
- Go to https://supabase.com/dashboard
- Log in with your Supabase account

### 2. Select Your Project
- Look for your project (it should be associated with the connection string)
- The project name might be related to the host: `aws-1-ap-northeast-2`

### 3. Navigate to Database Section
- In the left sidebar, click on **"Database"** or **"SQL Editor"**
- You should see your database listed

### 4. View Tables
- Click on **"Tables"** in the left sidebar under Database
- You should see all 75 tables including:
  - `users`
  - `organizations`
  - `leads`
  - `jobs`
  - `duplicate_groups`
  - `duplicate_leads`
  - `saved_views`
  - And 68 more tables

### 5. Using SQL Editor
- Click on **"SQL Editor"** in the left sidebar
- You can run queries like:
  ```sql
  SELECT table_name 
  FROM information_schema.tables 
  WHERE table_schema = 'public' 
  ORDER BY table_name;
  ```

## If You Still Can't See the Database

### Option 1: Check Project Selection
- Make sure you're in the correct Supabase project
- The connection string shows: `postgres.aashvhvwiayvniidvaqk`
- This is your project reference ID

### Option 2: Check Database Connection Pooler
- Your connection uses port **6543** (connection pooler)
- In Supabase dashboard, go to **Settings** → **Database**
- Check the connection pooler settings

### Option 3: Direct Database Connection
- In Supabase dashboard, go to **Settings** → **Database**
- Look for **"Connection string"** or **"Connection pooling"**
- You should see your connection details there

### Option 4: Use Table Editor
- Click on **"Table Editor"** in the left sidebar
- This shows all tables in a visual interface
- You should see your 75 tables listed

## Verify Database is Working

Your database is confirmed working! The test shows:
- ✅ Connection successful
- ✅ 75 tables exist
- ✅ Database name: `Lead_scrapper`

## Common Issues

1. **Wrong Project**: Make sure you're logged into the correct Supabase account/project
2. **Permissions**: Ensure your account has access to view databases
3. **Region**: Your database is in `ap-northeast-2` (Asia Pacific - Seoul)
4. **Connection Type**: You're using the connection pooler (port 6543), not direct connection (port 5432)

## Quick Test Query

You can test if you can see the database by running this in SQL Editor:

```sql
-- List all tables
SELECT 
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

This should return 75 rows.

