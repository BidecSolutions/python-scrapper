# Quick Start: Deploy to Replit

## 🚀 Fast Deployment (4 Steps)

### Step 1: Push to GitHub

```bash
git add .replit main.py replit.nix
git commit -m "Add Replit deployment configuration"
git push origin main
```

### Step 2: Import to Replit

1. **Go to**: https://replit.com
2. **Click**: "Create Repl" → "Import from GitHub"
3. **Paste**: Your repository URL
4. **Click**: "Import from GitHub"

### Step 3: Set Environment Variables

1. **Click**: Secrets (lock icon in left sidebar)
2. **Add**:
   ```
   DATABASE_URL=sqlite:///./lead_scraper.db
   JWT_SECRET_KEY=<generate random 32+ chars>
   ```
3. **Click**: "Run" button

### Step 4: Test

After deployment:
- **Health**: `https://your-repl.repl.co/health`
- **Docs**: `https://your-repl.repl.co/docs`

## ✅ What Replit Provides

- ✅ **Auto-installs** dependencies from `requirements.txt`
- ✅ **Auto-runs** your application
- ✅ **Live URL** - `https://your-repl.repl.co`
- ✅ **Built-in database** (optional)

## 📋 After Deployment

1. Run migrations: `alembic upgrade head` (in Shell)
2. Create admin: `python create_user.py` (in Shell)
3. Update frontend: Set `NEXT_PUBLIC_API_URL` to your Replit URL
4. Update CORS: Add Replit URL to allowed origins

## 🎉 Done!

Your backend is now live on Replit!

**See `REPLIT_DEPLOYMENT.md` for detailed instructions.**

