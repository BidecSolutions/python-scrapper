# How to Switch Database in Supabase SQL Editor

## The Problem
- ✅ Your tables exist in `Lead_scrapper` database (75 tables)
- ❌ Supabase SQL Editor is connected to `postgres` database (0 tables)
- The "Primary Database" dropdown is the solution!

## Solution: Use the "Primary Database" Dropdown

### Step-by-Step Instructions:

1. **Look at the SQL Editor interface**
   - You should see a dropdown labeled **"Primary Database"** 
   - It's located to the right of the query editor, near the "Run" button

2. **Click on "Primary Database" dropdown**
   - It probably currently shows: `postgres` or `Primary Database`
   - Click to open the dropdown menu

3. **Select `Lead_scrapper` from the dropdown**
   - You should see both databases listed:
     - `postgres` (empty)
     - `Lead_scrapper` (your database with 75 tables)
   - Select `Lead_scrapper`

4. **Re-run your query**
   - After switching, run this query again:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   ORDER BY table_name;
   ```
   - You should now see all 75 tables!

## Alternative: If "Primary Database" Dropdown Doesn't Work

If you can't find or use the "Primary Database" dropdown, try this:

### Option 1: Check Table Editor
1. Go to **Table Editor** (icon in left sidebar)
2. Look for a **"Database"** or **"Schema"** dropdown at the top
3. Select `Lead_scrapper` from there

### Option 2: Check Project Settings
1. Go to **Settings** → **Database**
2. Look for connection settings or database selection
3. See if you can specify which database to view

### Option 3: Use Connection String
The connection string in your `.env` file is correct:
```
DATABASE_URL=postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper
```

This connects to `Lead_scrapper` - your app is working correctly!

## Quick Test After Switching

Once you switch to `Lead_scrapper`, run:

```sql
-- Verify you're in the right database
SELECT current_database();

-- Should return: Lead_scrapper

-- Count tables
SELECT COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Should return: 75

-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name
LIMIT 20;
```

## Summary

**The "Primary Database" dropdown is the key!** 
- It's visible in your screenshots (to the right of the query editor)
- Click it and select `Lead_scrapper`
- Then all your queries will show your 75 tables!

