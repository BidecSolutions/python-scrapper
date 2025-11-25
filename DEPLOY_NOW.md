# 🚀 Deploy Backend to Vercel - Quick Guide

## ✅ Ready to Deploy!

All configuration files are ready:
- ✅ `vercel.json` - Vercel configuration
- ✅ `api/index.py` - Serverless function entry point (with Mangum)
- ✅ `.vercelignore` - Excludes frontend and unnecessary files
- ✅ `requirements.txt` - Updated with Mangum adapter

## 📋 Deployment Steps

### 1. Push to GitHub

```bash
# Make sure you're in project root
cd D:\laragon\www\python-scrapper

# If not already a git repo:
git init
git add .
git commit -m "Add Vercel configuration for backend deployment"

# Add your GitHub remote (if not already added)
git remote add origin https://github.com/yourusername/leadflux-backend.git
git branch -M main
git push -u origin main
```

### 2. Deploy to Vercel Dashboard

1. **Go to**: https://vercel.com/new
2. **Sign in** or create account
3. **Import Git Repository**:
   - Click "Import Git Repository"
   - Select your backend repository
   - Click "Import"

4. **Configure Project**:
   - **Framework Preset**: "Other" (or auto-detect)
   - **Root Directory**: Leave empty
   - **Build Command**: Leave empty
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty

5. **Add Environment Variables**:
   - Click "Environment Variables"
   - Add these (check all environments: Production, Preview, Development):
     ```
     DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
     JWT_SECRET_KEY=your-secret-key-minimum-32-characters
     ```
   - Add optional API keys if needed:
     ```
     GOOGLE_PLACES_API_KEY=your-key
     GROQ_API_KEY=your-key
     ```

6. **Deploy**:
   - Click "Deploy"
   - Wait 2-5 minutes for deployment

### 3. Set Up Database

**Easiest Option: Vercel Postgres**

1. Vercel Dashboard → Your Project → "Storage" tab
2. Click "Create Database" → "Postgres"
3. Choose region and name
4. Click "Create"
5. Connection string is automatically added as `DATABASE_URL`

**Alternative: External Database**

- **Neon** (https://neon.tech) - Free serverless Postgres
- **Supabase** (https://supabase.com) - Free Postgres
- **Railway** (https://railway.app) - Postgres addon
- **Render** (https://render.com) - Managed Postgres

Then add connection string as `DATABASE_URL` environment variable.

### 4. Test Your Deployment

After deployment, test these URLs:

```bash
# Health check
https://your-project.vercel.app/health
# Should return: {"status": "healthy"}

# Root endpoint
https://your-project.vercel.app/
# Should return: {"message": "Lead Scraper API", "version": "0.1.0"}

# API Documentation
https://your-project.vercel.app/docs
# Should show FastAPI Swagger UI
```

### 5. Run Database Migrations

After deployment, run migrations:

**Option A: Via Migration Endpoint** (add to your routes)

```python
@router.post("/admin/migrate")
async def run_migrations():
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    return {"status": "migrations completed"}
```

Then call: `POST https://your-api.vercel.app/api/admin/migrate`

**Option B: Run Locally Against Production DB**

```powershell
# Set production DATABASE_URL
$env:DATABASE_URL="postgresql+asyncpg://..."

# Run migrations
alembic upgrade head
```

### 6. Update Frontend

Update your frontend's environment variable:

```
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
```

## ⚠️ Important Notes

### Vercel Limitations

- **Function Timeout**: 10 seconds (Hobby) or 60 seconds (Pro)
- **Cold Starts**: First request may be slow
- **Memory**: 1GB default (can be increased)

### For Better Performance

Consider deploying to:
- **Railway** - Better for FastAPI, persistent connections
- **Render** - Easy deployment, no timeout limits
- **Fly.io** - Excellent performance

## 🎉 Done!

Your backend should now be live at:
- **API**: `https://your-project.vercel.app`
- **Docs**: `https://your-project.vercel.app/docs`

---

**Need help? Check `DEPLOY_TO_VERCEL_NOW.md` for detailed troubleshooting.**

