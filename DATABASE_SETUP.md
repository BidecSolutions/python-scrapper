# Database Connection Setup Guide

## PostgreSQL Connection Configuration

Your database connection details:
- **Host**: aws-1-ap-northeast-2.pooler.supabase.com
- **Port**: 6543
- **Database**: Lead_scrapper
- **Username**: postgres.aashvhvwiayvniidvaqk
- **Password**: Newpass@2025@

## Step 1: Install PostgreSQL Dependencies

Make sure you have the required PostgreSQL driver installed:

```bash
cd python-scrapper
pip install psycopg2-binary
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## Step 2: Create .env File

Create a `.env` file in the `python-scrapper` directory with the following content:

```env
# Database Configuration
# PostgreSQL connection string for Supabase
# Note: Password is URL-encoded (@ becomes %40)
DATABASE_URL=postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper

# JWT Secret Key (change in production!)
JWT_SECRET_KEY=your-secret-key-change-in-production-min-32-chars-please-use-a-secure-random-string
```

**Important**: The password `Newpass@2025@` must be URL-encoded as `Newpass%402025%40` in the connection string.

## Step 3: Test Database Connection

Test the connection:

```bash
cd python-scrapper
python test_db_connection.py
```

This will verify:
- ✅ Connection to PostgreSQL server
- ✅ Database name (Lead_scrapper)
- ✅ List of existing tables

## Step 4: Initialize Database Tables

If the connection test passes, create the database tables:

```bash
python init_db.py
```

## Step 5: Create Admin User

Create your first admin user:

```bash
python create_user.py
```

## Troubleshooting

### Connection Error: "could not connect to server"

**Possible causes:**
1. Network/firewall blocking connection
2. Incorrect host/port
3. Database server is down

**Solutions:**
- Verify you can reach the Supabase host
- Check if port 6543 is accessible
- Verify credentials in Supabase dashboard

### Connection Error: "database does not exist"

**Solution:**
- Verify the database name is `Lead_scrapper` (case-sensitive)
- Check if the database exists in your Supabase project

### Connection Error: "password authentication failed"

**Solution:**
- Verify the password is correct: `Newpass@2025@`
- Ensure password is URL-encoded in connection string: `Newpass%402025%40`
- Check for any extra spaces or characters

### Module Error: "No module named 'psycopg2'"

**Solution:**
```bash
pip install psycopg2-binary
```

### SSL Connection Error

If you encounter SSL errors, you can add SSL parameters to the connection string:

```
DATABASE_URL=postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper?sslmode=require
```

## Connection String Format

The PostgreSQL connection string format is:
```
postgresql://[username]:[password]@[host]:[port]/[database]
```

Where:
- `username`: postgres.aashvhvwiayvniidvaqk
- `password`: Newpass%402025%40 (URL-encoded)
- `host`: aws-1-ap-northeast-2.pooler.supabase.com
- `port`: 6543
- `database`: Lead_scrapper

## Next Steps

After successful connection:
1. ✅ Database connection verified
2. ✅ Tables created (run `init_db.py`)
3. ✅ Admin user created (run `create_user.py`)
4. ✅ Start the backend server: `python main.py`

