# How to See Your Database in Supabase Dashboard

## The Problem
Your Supabase dashboard is showing the **`postgres`** database (which is empty), but your tables are in the **`Lead_scrapper`** database.

## Solution: Switch Database in Supabase Dashboard

### Option 1: Use SQL Editor with Database Name

1. In Supabase dashboard, go to **SQL Editor**
2. Before running queries, make sure you're connected to the right database
3. Run this query to switch to your database:
   ```sql
   \c Lead_scrapper
   ```
   OR
   ```sql
   SET search_path TO 'Lead_scrapper';
   ```

4. Then run:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   ORDER BY table_name;
   ```

### Option 2: Check Database Selector

1. In Supabase dashboard, look for a **database selector** dropdown
2. It might be in:
   - The top navigation bar
   - SQL Editor settings
   - Table Editor settings
3. Select **`Lead_scrapper`** instead of `postgres`

### Option 3: Use Direct Connection String

Update your `.env` to use the direct connection that matches the dashboard:

**Current (Pooler):**
```
DATABASE_URL=postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper
```

**Direct Connection (matches dashboard):**
```
DATABASE_URL=postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:5432/Lead_scrapper
```

**Note:** Change port from `6543` to `5432` and keep database name as `Lead_scrapper`

## Quick Verification

After switching, you should see:
- ✅ 75 tables in Table Editor
- ✅ All your tables: `users`, `organizations`, `leads`, `jobs`, etc.

## Why This Happened

Supabase has two databases:
1. **`postgres`** - Default database (empty in your case)
2. **`Lead_scrapper`** - Your actual database with 75 tables

The dashboard defaults to showing `postgres`, but your data is in `Lead_scrapper`.

