# 🔧 Replit Deployment Troubleshooting Guide

## 📋 Common Errors and Solutions

### Error 1: "ModuleNotFoundError" or Missing Dependencies

**Symptoms:**
```
ModuleNotFoundError: No module named 'X'
ImportError: cannot import name 'X' from 'Y'
```

**Solution:**
1. **Check if all dependencies are in `requirements.txt`**
   ```bash
   # In Replit Shell, run:
   pip install -r requirements.txt
   ```

2. **If a specific module is missing, add it:**
   ```bash
   pip install <module-name>
   ```

3. **Common missing modules:**
   - `uvicorn` - Already in requirements.txt
   - `fastapi` - Already in requirements.txt
   - `sqlalchemy` - Already in requirements.txt
   - `bcrypt` - Already in requirements.txt
   - If still missing: Check if Replit's packager installed everything

### Error 2: Database Connection Error

**Symptoms:**
```
sqlalchemy.exc.OperationalError: unable to open database file
sqlite3.OperationalError: database is locked
```

**Solution:**
1. **Set DATABASE_URL in Secrets:**
   - Go to: **Secrets** (lock icon in left sidebar)
   - Add: `DATABASE_URL=sqlite:///./lead_scraper.db`
   - Click **Add secret**

2. **Or use Replit's built-in database:**
   - Click **Database** icon (left sidebar)
   - Create database
   - Copy connection string
   - Add to Secrets: `DATABASE_URL=<connection-string>`

3. **If using SQLite:**
   ```bash
   # Ensure database file exists
   touch lead_scraper.db
   ```

### Error 3: Port Already in Use

**Symptoms:**
```
OSError: [Errno 48] Address already in use
Port 8000 is already in use
```

**Solution:**
1. **Use Replit's PORT environment variable** (already configured in `.replit`)
   - The `.replit` file should use `$PORT` (not hardcoded 8000)
   - Replit automatically provides PORT variable

2. **Check if another process is running:**
   ```bash
   # In Shell, kill existing process
   pkill -f uvicorn
   # Then click Run again
   ```

### Error 4: JWT_SECRET_KEY Missing

**Symptoms:**
```
KeyError: 'JWT_SECRET_KEY'
pydantic_core._pydantic_core.ValidationError
```

**Solution:**
1. **Generate a secret key:**
   ```bash
   # In Shell, run:
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Add to Secrets:**
   - Go to: **Secrets**
   - Key: `JWT_SECRET_KEY`
   - Value: (paste the generated key)
   - Click **Add secret**

### Error 5: Import Errors (Circular or Missing)

**Symptoms:**
```
ImportError: cannot import name 'X' from 'Y'
ModuleNotFoundError: No module named 'app'
```

**Solution:**
1. **Check PYTHONPATH:**
   - Already set in `.replit`: `PYTHONPATH=.`
   - Verify it's in Secrets if needed

2. **If app structure issues:**
   ```bash
   # In Shell, verify structure:
   ls -la app/
   ls -la app/api/
   ```

3. **Reinstall in development mode:**
   ```bash
   pip install -e .
   ```

### Error 6: "Could not build wheels" (Building Failed)

**Symptoms:**
```
ERROR: Could not build wheels for X
Failed building wheel for X
```

**Solution:**
1. **Install build dependencies:**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

2. **For specific packages:**
   ```bash
   # If numpy fails:
   pip install numpy --no-cache-dir
   
   # If cryptography fails:
   pip install cryptography --no-cache-dir
   ```

### Error 7: "Application startup failed"

**Symptoms:**
```
Application startup failed.
Error during application initialization
```

**Solution:**
1. **Check logs in Console:**
   - Look for the specific error message
   - Check if it's a database, import, or configuration issue

2. **Test database connection:**
   ```bash
   # In Shell:
   python -c "from app.core.db import engine; print(engine.url)"
   ```

3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

### Error 8: Nix Environment Build Failed

**Symptoms:**
```
couldn't get nix env building nix env: exit status 1
attribute 'X' missing
```

**Solution:**
1. **Simplified `replit.nix` is already in place** ✅
   - Uses standard packages available in Replit
   - Removed `prybar` dependencies

2. **If still failing:**
   ```nix
   { pkgs }: {
     deps = [
       pkgs.python312
       pkgs.python312Packages.pip
     ];
   }
   ```

3. **Or try minimal config:**
   ```nix
   { pkgs }: {
     deps = [ pkgs.python312 ];
   }
   ```

### Error 9: "Application Not Responding"

**Symptoms:**
- Application starts but returns errors
- 500 Internal Server Error
- Timeout errors

**Solution:**
1. **Check application logs:**
   - Look in Console for Python errors
   - Check for unhandled exceptions

2. **Test health endpoint:**
   ```
   https://your-repl.repl.co/health
   ```

3. **Check CORS settings:**
   - Already configured to allow all origins (`allow_origins=["*"]`)

### Error 10: File Permissions or Read-Only Filesystem

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied
OSError: [Errno 30] Read-only file system
```

**Solution:**
1. **For uploads directory:**
   - Already handled in code (try-except blocks)
   - Uploads may not work on Replit (use cloud storage)

2. **For database:**
   ```bash
   # Ensure write permissions:
   chmod 644 lead_scraper.db
   ```

## 🔍 Step-by-Step Debugging

### Step 1: Check Console Logs
1. Open **Console** (bottom panel)
2. Look for error messages
3. Note the first error (usually the root cause)

### Step 2: Verify Configuration
1. **Check `.replit` file exists:**
   ```bash
   cat .replit
   ```

2. **Check `main.py` exists:**
   ```bash
   cat main.py
   ```

3. **Check `replit.nix` exists:**
   ```bash
   cat replit.nix
   ```

### Step 3: Verify Secrets
1. Go to **Secrets** (lock icon)
2. Verify these are set:
   - `DATABASE_URL` (optional, defaults to SQLite)
   - `JWT_SECRET_KEY` (required)

### Step 4: Test Dependencies
```bash
# In Shell, test imports:
python -c "import fastapi; print('FastAPI OK')"
python -c "import uvicorn; print('Uvicorn OK')"
python -c "import sqlalchemy; print('SQLAlchemy OK')"
```

### Step 5: Test Application Startup
```bash
# In Shell, test main entry point:
python main.py
```

### Step 6: Check Database
```bash
# Test database connection:
python -c "from app.core.db import engine; engine.connect(); print('DB OK')"
```

## 🚀 Quick Fix Checklist

- [ ] All files pushed to GitHub (`.replit`, `main.py`, `replit.nix`)
- [ ] Repository imported to Replit
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `JWT_SECRET_KEY` set in Secrets
- [ ] `DATABASE_URL` set in Secrets (optional)
- [ ] Clicked **Run** button
- [ ] Checked Console for errors
- [ ] Tested `/health` endpoint

## 📞 Still Having Issues?

### Share These Details:
1. **Full error message** from Console
2. **What step failed** (building, starting, running)
3. **Console output** (last 20-30 lines)
4. **Secrets configured** (which ones are set)

### Quick Reset:
1. **Stop** the Repl (click Stop)
2. **Clear cache** (Tools → Clear cache)
3. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```
4. **Start again** (click Run)

---

**Most common fix:** Ensure `JWT_SECRET_KEY` is set in Secrets! 🔑

