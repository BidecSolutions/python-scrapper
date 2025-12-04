# How to View Lead_scrapper Database with pgAdmin

Since Supabase dashboard doesn't show custom databases, use pgAdmin to view your `Lead_scrapper` database.

## Step 1: Download pgAdmin

1. Go to: https://www.pgadmin.org/download/
2. Download pgAdmin 4 for Windows
3. Install it (it's free and open-source)

## Step 2: Add Supabase Server

1. Open pgAdmin
2. Right-click on "Servers" in the left panel
3. Select "Register" → "Server"

## Step 3: Configure Connection

### General Tab:
- **Name**: `Supabase Lead_scrapper` (or any name you like)

### Connection Tab:
- **Host name/address**: `aws-1-ap-northeast-2.pooler.supabase.com`
- **Port**: `5432` (direct connection) or `6543` (pooler)
- **Maintenance database**: `Lead_scrapper`
- **Username**: `postgres.aashvhvwiayvniidvaqk`
- **Password**: `Newpass@2025@`
- **Save password**: ✅ (check this box)

### Advanced Tab (Optional):
- **DB restriction**: `Lead_scrapper` (to only show this database)

## Step 4: Connect and View

1. Click "Save"
2. Expand the server in the left panel
3. Expand "Databases"
4. Expand "Lead_scrapper"
5. Expand "Schemas" → "public" → "Tables"
6. You'll see all 75 tables! 🎉

## Alternative: Use DBeaver (Easier)

1. Download DBeaver: https://dbeaver.io/download/
2. Create new connection → PostgreSQL
3. Use connection string:
   ```
   postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:5432/Lead_scrapper
   ```
4. Connect and browse all tables

## Quick Connection String

For any PostgreSQL client tool, use:

**Direct Connection (port 5432):**
```
postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:5432/Lead_scrapper
```

**Connection Pooler (port 6543):**
```
postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper
```

Both work! Use port 5432 for direct connection (matches what Supabase dashboard uses).

