# Fix: Logo Upload Error

## Issue
The error "no such column: organizations.logo_url" occurs because the backend server needs to be restarted after adding the database column.

## Solution

### Step 1: Verify Column Exists
The migration has already been run and the column exists. You can verify:
```bash
python -c "import sqlite3; conn = sqlite3.connect('lead_scraper.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(organizations)'); print([row[1] for row in cursor.fetchall()])"
```

You should see `logo_url` in the list.

### Step 2: Restart Backend Server

**Option A: If using npm scripts:**
```bash
# Stop the current server (Ctrl+C)
# Then restart:
npm run dev:backend
```

**Option B: If using PowerShell scripts:**
```bash
# Stop the current server (Ctrl+C)
# Then restart:
.\start-backend.ps1
```

**Option C: Manual restart:**
```bash
# Stop current server (Ctrl+C)
# Then:
python -m uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Test Logo Upload
1. Go to Settings page
2. Click "Upload Logo"
3. Select an image file
4. The logo should upload successfully

## Why This Happens
SQLAlchemy caches the table schema when the application starts. After adding a new column, the server needs to be restarted so SQLAlchemy can detect the new column.

## Verification
After restarting, the logo upload should work. The logo will appear in:
- Settings page (preview)
- Sidebar (replaces default "LF" logo)

