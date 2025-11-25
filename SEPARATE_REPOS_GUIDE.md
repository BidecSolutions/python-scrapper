# Guide: Separating Frontend and Backend into Different Repositories

This guide will help you split your monorepo into two separate repositories for cleaner deployment.

## Overview

- **Frontend Repository**: Next.js app → Deploy to Vercel
- **Backend Repository**: FastAPI app → Deploy to Railway/Render/Fly.io

## Step 1: Create Frontend Repository

### Option A: Create New Repository from Frontend Folder

1. **Create a new GitHub repository**
   - Go to GitHub → New Repository
   - Name: `leadflux-frontend` (or your preferred name)
   - Make it private/public as needed
   - Don't initialize with README

2. **Prepare frontend folder**
   ```bash
   # Navigate to frontend directory
   cd frontend
   
   # Initialize git (if not already)
   git init
   
   # Add all files
   git add .
   
   # Commit
   git commit -m "Initial commit: Frontend only"
   
   # Add remote
   git remote add origin https://github.com/yourusername/leadflux-frontend.git
   
   # Push
   git push -u origin main
   ```

### Option B: Use Git Subtree (Keep History)

If you want to preserve git history:

```bash
# From project root
git subtree push --prefix frontend origin frontend-main
```

## Step 2: Create Backend Repository

1. **Create a new GitHub repository**
   - Name: `leadflux-backend` (or your preferred name)

2. **Prepare backend files**
   ```bash
   # From project root, create backend-only structure
   # Copy all backend files to a new directory or use git subtree
   
   # Initialize git in backend directory
   cd ..  # Go to parent directory
   mkdir leadflux-backend
   cd leadflux-backend
   
   # Copy backend files (from original project)
   # Or use git subtree:
   ```

3. **Or manually copy files:**
   - Copy `app/` directory
   - Copy `migrations/` directory
   - Copy `requirements.txt`
   - Copy `pyproject.toml`
   - Copy `alembic.ini.example` → `alembic.ini`
   - Copy `alembic/` directory
   - Copy `config/` directory
   - Copy `create_user.py`
   - Copy all migration scripts
   - Copy `README.md` (backend-specific)
   - **DO NOT copy** `frontend/` directory
   - **DO NOT copy** `node_modules/`
   - **DO NOT copy** `package.json` (root)

## Step 3: Update Frontend Repository

### Files to Keep in Frontend Repo

```
frontend/
├── app/                    # Next.js pages
├── components/             # React components
├── contexts/               # React contexts
├── lib/                    # API client, utilities
├── types/                  # TypeScript types
├── public/                 # Static assets
├── .env.local.example      # Example env file
├── .gitignore              # Frontend-specific
├── next.config.js
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
└── README.md
```

### Create Frontend-Specific Files

1. **Update `.gitignore`** (frontend only)
2. **Create `.env.local.example`**
3. **Update `README.md`** (frontend-specific)
4. **Remove backend references**

## Step 4: Update Backend Repository

### Files to Keep in Backend Repo

```
backend/
├── app/                    # FastAPI application
│   ├── api/                # API routes
│   ├── core/               # Database, ORM
│   ├── services/           # Business logic
│   ├── scraper/            # Scraping logic
│   └── ...
├── migrations/             # Database migrations
├── alembic/                # Alembic config
├── config/                 # Configuration
├── requirements.txt
├── pyproject.toml
├── alembic.ini
├── create_user.py
├── migrate_*.py            # Migration scripts
├── .env.example            # Backend env example
├── .gitignore              # Backend-specific
└── README.md
```

## Step 5: Deploy Frontend to Vercel

### From Frontend Repository

1. **Go to Vercel Dashboard**
   - https://vercel.com/new
   - Import your **frontend repository**

2. **Configure Project**
   - Framework: Next.js (auto-detected)
   - Root Directory: **Leave empty** (or `/` since it's already the root)
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

3. **Add Environment Variable**
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: Your backend URL (e.g., `https://leadflux-api.railway.app`)

4. **Deploy**
   - Click "Deploy"
   - Should work immediately!

## Step 6: Deploy Backend Separately

### Option A: Railway (Recommended)

1. **Go to Railway**
   - https://railway.app
   - Create new project
   - Deploy from GitHub

2. **Select Backend Repository**
   - Choose your `leadflux-backend` repo

3. **Configure**
   - Root Directory: `/` (default)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.api.server:app --host 0.0.0.0 --port $PORT`

4. **Add PostgreSQL Database**
   - Railway → New → Database → PostgreSQL
   - Note the connection string

5. **Set Environment Variables**
   - `DATABASE_URL`: PostgreSQL connection string
   - `JWT_SECRET_KEY`: Your secret key
   - `GOOGLE_PLACES_API_KEY`: (optional)
   - `GROQ_API_KEY`: (optional)
   - Other API keys as needed

6. **Deploy**
   - Railway will auto-deploy

### Option B: Render

1. **Go to Render**
   - https://render.com
   - New → Web Service
   - Connect GitHub → Select backend repo

2. **Configure**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.api.server:app --host 0.0.0.0 --port $PORT`

3. **Add PostgreSQL**
   - New → PostgreSQL
   - Link to web service

4. **Set Environment Variables**
   - Same as Railway

### Option C: Fly.io

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **From Backend Repository**
   ```bash
   fly launch
   ```

3. **Follow prompts**
   - Select region
   - Create PostgreSQL database
   - Set environment variables

## Step 7: Update CORS on Backend

After deploying backend, update CORS to allow your Vercel frontend domain:

```python
# app/api/server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",
        "https://your-custom-domain.com",
        "http://localhost:3000",  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 8: Update Frontend API URL

In your frontend repository's Vercel environment variables:

```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

Or for Render:
```
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

## Benefits of Separate Repos

✅ **Cleaner deployments** - No confusion about what to deploy  
✅ **Independent versioning** - Frontend and backend can version separately  
✅ **Better CI/CD** - Separate pipelines for each  
✅ **Easier scaling** - Scale frontend and backend independently  
✅ **Clearer ownership** - Different teams can own different repos  
✅ **Simpler Vercel setup** - No root directory configuration needed  

## Migration Checklist

### Frontend Repository
- [ ] Create new GitHub repo for frontend
- [ ] Copy frontend folder to new repo
- [ ] Update `.gitignore` (remove backend references)
- [ ] Update `README.md` (frontend-specific)
- [ ] Create `.env.local.example`
- [ ] Remove any backend file references
- [ ] Commit and push
- [ ] Deploy to Vercel
- [ ] Set `NEXT_PUBLIC_API_URL` environment variable

### Backend Repository
- [ ] Create new GitHub repo for backend
- [ ] Copy backend files (app/, migrations/, etc.)
- [ ] Update `.gitignore` (remove frontend references)
- [ ] Update `README.md` (backend-specific)
- [ ] Create `.env.example`
- [ ] Remove frontend directory
- [ ] Commit and push
- [ ] Deploy to Railway/Render/Fly.io
- [ ] Set environment variables
- [ ] Update CORS settings
- [ ] Run database migrations
- [ ] Create super admin user

## Quick Commands

### Create Frontend Repo
```bash
cd frontend
git init
git add .
git commit -m "Initial commit: Frontend"
git remote add origin https://github.com/yourusername/leadflux-frontend.git
git push -u origin main
```

### Create Backend Repo
```bash
# From project root, create backend structure
mkdir ../leadflux-backend
cd ../leadflux-backend

# Copy backend files (manually or use rsync)
# Then:
git init
git add .
git commit -m "Initial commit: Backend"
git remote add origin https://github.com/yourusername/leadflux-backend.git
git push -u origin main
```

## Troubleshooting

### Frontend can't connect to backend
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify backend is deployed and accessible
- Check CORS settings on backend
- Test backend health endpoint: `https://your-backend.com/health`

### CORS errors
- Update backend CORS to include Vercel domain
- Ensure `allow_credentials=True` is set
- Check that backend allows your frontend origin

### Environment variables not working
- Redeploy after adding variables
- Check variable names are correct
- Ensure `NEXT_PUBLIC_` prefix for client-side variables

---

**This separation will make your deployments much cleaner and easier to manage!**

