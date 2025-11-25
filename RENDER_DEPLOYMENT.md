# Deploy Backend to Render.com - Complete Guide

## Why Render.com?

Render.com is **much better** for FastAPI backends than Vercel:
- ✅ **Persistent connections** - No cold starts
- ✅ **Writable filesystem** - Can create uploads directory
- ✅ **PostgreSQL included** - Easy database setup
- ✅ **No timeout limits** - Long-running operations work
- ✅ **Better Python support** - Designed for Python apps
- ✅ **Background workers** - Can run async tasks

## Step 1: Prepare Your Repository

### Files Already Created

✅ `render.yaml` - Render configuration file  
✅ `requirements.txt` - Python dependencies  
✅ `.gitignore` - Excludes unnecessary files  

### Verify Files

Make sure these files exist:
- `app/api/server.py` - FastAPI application
- `requirements.txt` - All dependencies
- `render.yaml` - Render configuration

## Step 2: Push to GitHub

```bash
# Make sure all changes are committed
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

## Step 3: Deploy to Render

### Option A: Using render.yaml (Recommended)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Sign up or log in

2. **New + Blueprint**
   - Click "New +" button
   - Select "Blueprint"
   - Connect your GitHub account
   - Select your repository: `python-scrapper` (or your backend repo)

3. **Render will auto-detect render.yaml**
   - It will create:
     - Web service (your FastAPI app)
     - PostgreSQL database
   - Click "Apply"

4. **Set Environment Variables**
   - Go to your web service
   - Settings → Environment
   - Add these variables:
     ```
     DATABASE_URL=<auto-set from database>
     JWT_SECRET_KEY=<generate a random 32+ character string>
     GOOGLE_PLACES_API_KEY=<your-key>
     GROQ_API_KEY=<your-key>
     ```
   - Other API keys as needed

5. **Deploy**
   - Render will automatically deploy
   - Wait 5-10 minutes for first deployment

### Option B: Manual Setup

1. **Create PostgreSQL Database**
   - New → PostgreSQL
   - Name: `leadflux-db`
   - Plan: Free
   - Region: Choose closest to you
   - Click "Create Database"
   - Note the connection string

2. **Create Web Service**
   - New → Web Service
   - Connect GitHub → Select your repository
   - Configure:
     - **Name**: `leadflux-backend`
     - **Environment**: `Python 3`
     - **Region**: Choose closest
     - **Branch**: `main`
     - **Root Directory**: Leave empty (or `/`)
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.api.server:app --host 0.0.0.0 --port $PORT`
     - **Plan**: Free

3. **Add Environment Variables**
   - In Web Service → Environment:
     ```
     DATABASE_URL=<from PostgreSQL database>
     JWT_SECRET_KEY=<generate random 32+ chars>
     PYTHON_VERSION=3.12.0
     ```
   - Add other API keys as needed

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment

## Step 4: Update Database URL

After creating the database:

1. **Get Connection String**
   - Go to your PostgreSQL database
   - Copy "Internal Database URL" or "External Database URL"
   - Format: `postgresql://user:password@host:5432/database`

2. **Set in Web Service**
   - Web Service → Environment
   - Add/Update: `DATABASE_URL` = your connection string

## Step 5: Run Database Migrations

After deployment:

### Option A: Via Migration Endpoint

Add this to your routes (if not already):

```python
@router.post("/admin/migrate")
async def run_migrations(db: Session = Depends(get_db)):
    """Run database migrations"""
    from alembic.config import Config
    from alembic import command
    
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    
    return {"status": "migrations completed"}
```

Then call: `POST https://your-app.onrender.com/api/admin/migrate`

### Option B: Using Render Shell

1. Go to Web Service → Shell
2. Run:
   ```bash
   alembic upgrade head
   ```

### Option C: Run Locally Against Production DB

```bash
# Set production DATABASE_URL
export DATABASE_URL=postgresql://...

# Run migrations
alembic upgrade head
```

## Step 6: Create Super Admin User

### Option A: Via Script

1. **Render Shell**:
   ```bash
   python create_user.py
   ```

2. **Or locally** (with production DATABASE_URL):
   ```bash
   export DATABASE_URL=postgresql://...
   python create_user.py
   ```

### Option B: Via API

After migrations, create user via signup endpoint or admin panel.

## Step 7: Update CORS Settings

Update `app/api/server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 8: Update Frontend

Update your frontend's environment variable:

```
NEXT_PUBLIC_API_URL=https://your-app.onrender.com
```

## Step 9: Test Deployment

After deployment completes:

1. **Health Check**
   ```
   GET https://your-app.onrender.com/health
   ```
   Should return: `{"status": "healthy"}`

2. **API Documentation**
   ```
   GET https://your-app.onrender.com/docs
   ```
   Should show FastAPI Swagger UI

3. **Root Endpoint**
   ```
   GET https://your-app.onrender.com/
   ```
   Should return: `{"message": "Lead Scraper API", "version": "0.1.0"}`

## Render.com Advantages

✅ **No cold starts** - Always running  
✅ **Writable filesystem** - Can create uploads directory  
✅ **PostgreSQL included** - Easy database setup  
✅ **No timeout limits** - Long operations work  
✅ **Better for Python** - Designed for Python apps  
✅ **Free tier available** - Good for development  

## Environment Variables Reference

### Required
```
DATABASE_URL=postgresql://user:password@host:5432/database
JWT_SECRET_KEY=your-secret-key-minimum-32-characters
```

### Optional (API Keys)
```
GOOGLE_PLACES_API_KEY=your-key
GROQ_API_KEY=your-key
GOOGLE_SEARCH_API_KEY=your-key
GOOGLE_SEARCH_CX=your-key
BING_SEARCH_API_KEY=your-key
OPENCAGE_API_KEY=your-key
```

## Troubleshooting

### Deployment Fails

1. **Check build logs** - Look for errors
2. **Verify requirements.txt** - All dependencies listed
3. **Check Python version** - Set `PYTHON_VERSION=3.12.0`

### Database Connection Fails

1. **Verify DATABASE_URL** - Check connection string
2. **Check database status** - Make sure it's running
3. **Test connection** - Use external connection string

### API Not Starting

1. **Check start command** - Should be: `uvicorn app.api.server:app --host 0.0.0.0 --port $PORT`
2. **Check logs** - Look for import errors
3. **Verify app structure** - `app/api/server.py` exists

### Slow First Request

- Normal on free tier (spins down after inactivity)
- Upgrade to paid plan for always-on

## Next Steps

1. ✅ Deploy to Render
2. ✅ Set up PostgreSQL database
3. ✅ Run database migrations
4. ✅ Create super admin user
5. ✅ Update frontend API URL
6. ✅ Update CORS settings
7. ✅ Test all endpoints

---

**Render.com is much better for FastAPI backends!** 🚀

