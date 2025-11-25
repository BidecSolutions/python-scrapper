# 🚀 Deploy Backend to Vercel - Step by Step

## ✅ Files Ready

All configuration files are created:
- ✅ `vercel.json` - Vercel configuration
- ✅ `api/index.py` - Serverless function entry point
- ✅ `.vercelignore` - Excludes unnecessary files

## Method 1: Deploy via Vercel Dashboard (Recommended)

### Step 1: Push to GitHub

```bash
# Make sure you're in the project root
cd D:\laragon\www\python-scrapper

# Check if this is already a git repo
git status

# If not initialized:
git init
git add .
git commit -m "Initial commit: Backend with Vercel config"

# Add your GitHub remote
git remote add origin https://github.com/yourusername/leadflux-backend.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/new
   - Sign in or create account

2. **Import Repository**
   - Click "Import Git Repository"
   - Select your backend repository (leadflux-backend)
   - Click "Import"

3. **Configure Project**
   - **Framework Preset**: Leave as "Other" (or it may auto-detect)
   - **Root Directory**: Leave empty (it's already at root)
   - **Build Command**: Leave empty (Vercel will auto-detect Python)
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty

4. **Add Environment Variables**
   
   Click "Environment Variables" and add:
   
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
   JWT_SECRET_KEY=your-secret-key-minimum-32-characters-long
   ```
   
   Optional (add as needed):
   ```
   GOOGLE_PLACES_API_KEY=your-key
   GROQ_API_KEY=your-key
   GOOGLE_SEARCH_API_KEY=your-key
   GOOGLE_SEARCH_CX=your-key
   BING_SEARCH_API_KEY=your-key
   OPENCAGE_API_KEY=your-key
   ```
   
   **Important**: Check all three environments:
   - ✅ Production
   - ✅ Preview  
   - ✅ Development

5. **Deploy**
   - Click "Deploy" button
   - Wait for deployment to complete (2-5 minutes)

### Step 3: Set Up Database

**Option A: Vercel Postgres (Easiest)**

1. In Vercel Dashboard → Your Project
2. Go to "Storage" tab
3. Click "Create Database"
4. Select "Postgres"
5. Choose region and name
6. Click "Create"
7. Connection string is automatically added as `DATABASE_URL`

**Option B: External Database**

Use one of these providers:
- **Neon** (https://neon.tech) - Serverless PostgreSQL, free tier
- **Supabase** (https://supabase.com) - Free PostgreSQL
- **Railway** (https://railway.app) - PostgreSQL addon
- **Render** (https://render.com) - Managed PostgreSQL

Then add the connection string as `DATABASE_URL` environment variable.

## Method 2: Deploy via Vercel CLI

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Login

```bash
vercel login
```

### Step 3: Deploy

```bash
# From project root
cd D:\laragon\www\python-scrapper

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? (select your account)
# - Link to existing project? No (first time)
# - What's your project's name? leadflux-backend
# - In which directory is your code located? ./
```

### Step 4: Set Environment Variables

```bash
# Set environment variables
vercel env add DATABASE_URL production
vercel env add JWT_SECRET_KEY production
# ... add other variables as needed

# Deploy with environment variables
vercel --prod
```

## Step 4: Test Deployment

After deployment completes:

1. **Health Check**
   ```
   GET https://your-project.vercel.app/health
   ```
   Should return: `{"status": "healthy"}`

2. **Root Endpoint**
   ```
   GET https://your-project.vercel.app/
   ```
   Should return: `{"message": "Lead Scraper API", "version": "0.1.0"}`

3. **API Documentation**
   ```
   GET https://your-project.vercel.app/docs
   ```
   Should show FastAPI Swagger UI

## Step 5: Run Database Migrations

After deployment, you need to run migrations:

### Option A: Create Migration Endpoint

Add this to a route file:

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

Then call: `POST https://your-api.vercel.app/api/admin/migrate`

### Option B: Run Locally Against Production DB

```bash
# Set production database URL
$env:DATABASE_URL="postgresql+asyncpg://..."

# Run migrations
alembic upgrade head
```

## Step 6: Update CORS Settings

Update `app/api/server.py` to allow your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 7: Update Frontend

Update your frontend's environment variable:

```
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
```

## Troubleshooting

### Error: Module not found
- Check `requirements.txt` includes all dependencies
- Verify `PYTHONPATH` is set in `vercel.json`

### Error: Function timeout
- Increase `maxDuration` in `vercel.json` (Pro plan needed for > 30s)
- Optimize slow endpoints

### Error: Database connection failed
- Verify `DATABASE_URL` is set correctly
- Check database is accessible from internet
- Ensure SSL is enabled for production databases

### Error: Import error
- Check `api/index.py` imports are correct
- Verify `app/api/server.py` exports the app correctly

## Next Steps

1. ✅ Deploy to Vercel
2. ✅ Set up PostgreSQL database
3. ✅ Add environment variables
4. ✅ Run database migrations
5. ✅ Test API endpoints
6. ✅ Update frontend API URL
7. ✅ Update CORS settings

---

**Your backend will be live at**: `https://your-project.vercel.app`

**API Documentation**: `https://your-project.vercel.app/docs`

