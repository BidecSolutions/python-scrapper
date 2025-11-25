# 🚀 Deploy to Replit - Step by Step

## ✅ Files Ready

I've created:
- ✅ `.replit` - Replit configuration
- ✅ `main.py` - Entry point for Replit
- ✅ `replit.nix` - Nix package configuration
- ✅ `REPLIT_DEPLOYMENT.md` - Complete guide
- ✅ `REPLIT_QUICK_START.md` - Quick reference

## 🎯 Quick Deployment (4 Steps)

### Step 1: Push to GitHub

```bash
git add .replit main.py replit.nix
git commit -m "Add Replit deployment configuration"
git push origin main
```

### Step 2: Import to Replit

1. **Go to**: https://replit.com
2. **Sign up/Login** (free account works)
3. **Click**: "Create Repl" (or "+ Create")
4. **Select**: "Import from GitHub"
5. **Paste**: Your repository URL
   - Example: `https://github.com/BidecSolutions/python-scrapper`
6. **Click**: "Import from GitHub"

### Step 3: Configure

After import:

1. **Set Environment Variables** (Secrets):
   - Click **Secrets** (lock icon in left sidebar)
   - Or: Tools → Secrets
   - **Add**:
     ```
     DATABASE_URL=sqlite:///./lead_scraper.db
     JWT_SECRET_KEY=<generate random 32+ chars>
     ```
     - Generate key: https://randomkeygen.com/
     - Or: `openssl rand -hex 32`

2. **Click "Run"** button
   - Replit will auto-install dependencies
   - Server will start automatically

### Step 4: Test

After running:

1. **Check Console** - Should show:
   ```
   Application startup complete.
   Uvicorn running on http://0.0.0.0:8000
   ```

2. **Get Your URL** - Top of console shows:
   - `https://your-repl.repl.co`

3. **Test Endpoints**:
   - Health: `https://your-repl.repl.co/health`
   - Docs: `https://your-repl.repl.co/docs`

## ✅ After Deployment

### Run Database Migrations

**Via Shell** (bottom panel):

```bash
alembic upgrade head
```

### Create Admin User

```bash
python create_user.py
```

### Update Frontend

Set environment variable:
```
NEXT_PUBLIC_API_URL=https://your-repl.repl.co
```

### Update CORS

In `app/api/server.py`, add Replit URL:
```python
allow_origins=[
    "https://your-frontend.vercel.app",
    "https://your-repl.repl.co",  # Add this
    "http://localhost:3000",
]
```

## 🎉 Replit Features

✅ **Easy import** - Just import from GitHub  
✅ **Auto-install** - Installs from `requirements.txt`  
✅ **Built-in DB** - Optional Replit database  
✅ **Live URL** - Automatic `your-repl.repl.co`  
✅ **Free tier** - Good for development  

## 📋 Checklist

- [ ] Push `.replit`, `main.py`, `replit.nix` to GitHub
- [ ] Import repository to Replit
- [ ] Set `JWT_SECRET_KEY` in Secrets
- [ ] Set `DATABASE_URL` in Secrets (or use default SQLite)
- [ ] Click "Run" button
- [ ] Test `/health` endpoint
- [ ] Run database migrations (in Shell)
- [ ] Create admin user (in Shell)
- [ ] Update frontend `NEXT_PUBLIC_API_URL`
- [ ] Update CORS settings
- [ ] Test all endpoints

## 🔧 Using Replit Database

If you want to use Replit's built-in database:

1. **Left sidebar** → Click **Database** icon
2. **Create database** (if needed)
3. **Copy connection string**
4. **Add to Secrets**: `DATABASE_URL=<connection-string>`
5. **Restart Repl**

---

**Ready to deploy? Just push to GitHub and import to Replit!** 🚀

