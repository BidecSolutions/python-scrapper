# How to Get the Direct Connection String from Supabase

## The Problem
- **Connection Pooler (port 6543)**: Connects to `Lead_scrapper` database with 75 tables ✅
- **Supabase Dashboard**: Shows the DIRECT connection database, which appears empty ❌

These are pointing to different databases!

## Solution: Use Direct Connection

### Step 1: Get Direct Connection String from Supabase

1. Go to your Supabase dashboard: https://supabase.com/dashboard/project/aashvhvwiayvniidvaqk
2. Click on **"Settings"** (gear icon) in the left sidebar
3. Click on **"Database"** in the settings menu
4. Scroll down to **"Connection string"** section
5. Look for **"URI"** or **"Connection pooling"** section
6. You'll see two options:
   - **Direct connection** (port 5432) ← Use this one!
   - **Connection pooling** (port 6543) ← This is what you're currently using

### Step 2: Copy the Direct Connection String

The direct connection string should look like:
```
postgresql://postgres.aashvhvwiayvniidvaqk:[YOUR-PASSWORD]@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
```

**OR** it might be:
```
postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

### Step 3: Update Your .env File

Replace the current `DATABASE_URL` in your `.env` file:

**Current (Pooler - port 6543):**
```
DATABASE_URL=postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper
```

**New (Direct - port 5432):**
```
DATABASE_URL=postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
```

**OR if Supabase gives you a different format:**
```
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

### Step 4: Important Notes

1. **Database Name**: The direct connection might use `postgres` as the database name, not `Lead_scrapper`
2. **Password Encoding**: Make sure to URL-encode special characters:
   - `@` becomes `%40`
   - `#` becomes `%23`
   - etc.

3. **After changing**: You may need to:
   - Create the `Lead_scrapper` database in the direct connection
   - OR migrate your tables to the `postgres` database
   - OR check if Supabase has a way to specify the database name

## Alternative: Check Supabase Project Settings

1. In Supabase dashboard, go to **Settings** → **Database**
2. Check if there's a way to:
   - Create a new database named `Lead_scrapper`
   - OR see all databases in your project
   - OR switch which database the dashboard shows

## Quick Test

After updating your `.env` file, run:
```bash
python check_schema_and_connection.py
```

This will show you which database and tables you're connected to.

