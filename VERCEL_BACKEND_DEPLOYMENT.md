# Deploy Backend to Vercel - Complete Guide

## ⚠️ Important Note

Vercel supports Python serverless functions, but it's primarily designed for frontend/API routes. For full FastAPI applications with:
- Persistent database connections
- Background workers
- Long-running processes
- Large file uploads

Consider using **Railway**, **Render**, or **Fly.io** instead (see alternatives below).

However, if you want to deploy on Vercel, follow this guide.

## Step 1: Prepare Your Backend Repository

### Files Already Created

✅ `vercel.json` - Vercel configuration  
✅ `api/index.py` - Serverless function entry point  
✅ `.vercelignore` - Files to exclude from deployment  

### Required Files Structure

```
backend/
├── api/
│   └── index.py          # Vercel serverless entry point
├── app/                  # Your FastAPI application
│   ├── api/
│   │   └── server.py     # FastAPI app
│   └── ...
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel config
└── .vercelignore         # Ignore rules
```

## Step 2: Push to GitHub

```bash
# If you haven't created a backend repo yet:
git init
git add .
git commit -m "Initial commit: Backend API"
git remote add origin https://github.com/yourusername/leadflux-backend.git
git push -u origin main
```

## Step 3: Deploy to Vercel

### Using Vercel Dashboard

1. **Go to Vercel Dashboard**
   - https://vercel.com/new
   - Import your backend repository

2. **Configure Project**
   - Framework: **Other** (or leave auto-detect)
   - Root Directory: Leave empty (or `/`)
   - Build Command: Leave empty (Vercel will auto-detect Python)
   - Output Directory: Leave empty

3. **Set Environment Variables**
   Click "Environment Variables" and add:
   
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
   JWT_SECRET_KEY=your-secret-key-min-32-chars
   GOOGLE_PLACES_API_KEY=your-key
   GROQ_API_KEY=your-key
   ```
   
   Make sure to select **Production**, **Preview**, and **Development** for each variable.

4. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete

### Using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

## Step 4: Configure PostgreSQL Database

Vercel doesn't provide databases, so you need an external PostgreSQL database:

### Option A: Vercel Postgres (Recommended for Vercel)

1. In Vercel Dashboard → Your Project → Storage
2. Click "Create Database" → "Postgres"
3. Note the connection string
4. Add as `DATABASE_URL` environment variable

### Option B: External Database

Use any PostgreSQL provider:
- **Neon** (https://neon.tech) - Serverless Postgres
- **Supabase** (https://supabase.com) - Free tier
- **Railway** (https://railway.app) - PostgreSQL addon
- **Render** (https://render.com) - PostgreSQL

Add connection string as `DATABASE_URL` environment variable.

## Step 5: Update CORS Settings

After deployment, update CORS in `app/api/server.py`:

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

## Step 6: Run Database Migrations

After deploying, you need to run migrations:

### Option A: Using Vercel CLI

```bash
# SSH into Vercel function (not directly supported)
# Instead, create a migration endpoint
```

### Option B: Create Migration Script Endpoint

Add to `app/api/routes.py`:

```python
@router.post("/migrate")
async def run_migrations(db: Session = Depends(get_db)):
    """Run database migrations"""
    from alembic.config import Config
    from alembic import command
    
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    
    return {"status": "migrations completed"}
```

Then call: `POST https://your-api.vercel.app/api/migrate`

### Option C: Run Locally Against Production DB

```bash
# Set DATABASE_URL to production database
export DATABASE_URL=your-production-db-url

# Run migrations
alembic upgrade head
```

## Step 7: Test Your API

After deployment:

1. **Health Check**
   ```
   GET https://your-api.vercel.app/health
   ```

2. **API Docs**
   ```
   GET https://your-api.vercel.app/docs
   ```

3. **Root Endpoint**
   ```
   GET https://your-api.vercel.app/
   ```

## Limitations & Considerations

### ⚠️ Vercel Serverless Limitations

1. **Function Timeout**: 10 seconds (Hobby), 60 seconds (Pro)
2. **Cold Starts**: Functions may take time to start
3. **No Persistent Storage**: Use external database/storage
4. **No Background Workers**: Use external services (Upstash, etc.)
5. **File Uploads**: Limited to function memory

### ✅ When Vercel Works Well

- Simple API endpoints
- Stateless operations
- Quick responses (< 10 seconds)
- No long-running processes

### ❌ When to Use Alternatives

- Long-running operations
- Background workers
- Persistent connections
- Large file uploads
- WebSocket connections

## Alternative Deployment Options

### Option A: Railway (Recommended)

1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select backend repo
4. Add PostgreSQL database
5. Set environment variables
6. Deploy!

**Advantages:**
- ✅ Persistent connections
- ✅ Background workers
- ✅ PostgreSQL included
- ✅ No timeout limits
- ✅ Easy deployment

### Option B: Render

1. Go to https://render.com
2. New Web Service → GitHub
3. Select backend repo
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn app.api.server:app --host 0.0.0.0 --port $PORT`
6. Add PostgreSQL database
7. Deploy!

### Option C: Fly.io

```bash
fly launch
# Follow prompts
fly postgres create
fly secrets set DATABASE_URL=...
fly deploy
```

## Troubleshooting

### Error: Module not found

- Check `requirements.txt` has all dependencies
- Ensure `PYTHONPATH` is set correctly in `vercel.json`

### Error: Database connection failed

- Verify `DATABASE_URL` is set correctly
- Check database is accessible from internet
- Ensure SSL is enabled for production databases

### Error: Function timeout

- Optimize slow endpoints
- Move long operations to background workers
- Consider using Railway/Render for long-running tasks

### Error: CORS errors

- Update CORS settings in `app/api/server.py`
- Add frontend domain to `allow_origins`

## Next Steps

1. ✅ Deploy backend to Vercel
2. ✅ Set environment variables
3. ✅ Configure PostgreSQL database
4. ✅ Run database migrations
5. ✅ Update frontend `NEXT_PUBLIC_API_URL` to point to Vercel backend
6. ✅ Update CORS settings
7. ✅ Test API endpoints

## Quick Reference

**Backend URL**: `https://your-project.vercel.app`  
**API Docs**: `https://your-project.vercel.app/docs`  
**Health Check**: `https://your-project.vercel.app/health`

---

**Note**: For production workloads, consider Railway or Render for better reliability and fewer limitations.

