# Quick Start: Separate Frontend and Backend Repos

## 🎯 Goal

Split your monorepo into:
- **Frontend repo** → Deploy to Vercel (easy, no root directory config needed!)
- **Backend repo** → Deploy to Railway/Render/Fly.io

## ✅ Step 1: Create Frontend Repository

### From Your Current Project

```bash
# Navigate to frontend directory
cd frontend

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Frontend only"

# Create new GitHub repo first, then:
git remote add origin https://github.com/yourusername/leadflux-frontend.git
git branch -M main
git push -u origin main
```

### Deploy to Vercel

1. Go to: https://vercel.com/new
2. Import your **frontend repository**
3. **No root directory config needed!** (it's already the root)
4. Add environment variable: `NEXT_PUBLIC_API_URL` = your backend URL
5. Deploy!

**That's it!** Much simpler than before.

## ✅ Step 2: Create Backend Repository

### Create Backend Structure

```bash
# From project root, create backend directory
mkdir ../leadflux-backend
cd ../leadflux-backend

# Copy backend files (Windows PowerShell)
# From original project root:
Copy-Item -Path "app" -Destination "../leadflux-backend/" -Recurse
Copy-Item -Path "migrations" -Destination "../leadflux-backend/" -Recurse
Copy-Item -Path "alembic" -Destination "../leadflux-backend/" -Recurse
Copy-Item -Path "config" -Destination "../leadflux-backend/" -Recurse
Copy-Item -Path "tests" -Destination "../leadflux-backend/" -Recurse
Copy-Item -Path "requirements.txt" -Destination "../leadflux-backend/"
Copy-Item -Path "pyproject.toml" -Destination "../leadflux-backend/"
Copy-Item -Path "create_user.py" -Destination "../leadflux-backend/"
Copy-Item -Path "init_db.py" -Destination "../leadflux-backend/"
Copy-Item -Path "migrate_*.py" -Destination "../leadflux-backend/"

# Create backend-specific files
cd ../leadflux-backend
```

### Initialize Backend Repo

```bash
cd ../leadflux-backend

# Initialize git
git init

# Create .gitignore (see BACKEND_REPO_SETUP.md)
# Create .env.example (see BACKEND_REPO_SETUP.md)
# Create README.md (see BACKEND_REPO_SETUP.md)

# Add and commit
git add .
git commit -m "Initial commit: Backend API"

# Create GitHub repo, then:
git remote add origin https://github.com/yourusername/leadflux-backend.git
git branch -M main
git push -u origin main
```

## ✅ Step 3: Deploy Backend

### Railway (Recommended)

1. Go to: https://railway.app
2. New Project → Deploy from GitHub
3. Select your **backend repository**
4. Add PostgreSQL database
5. Set environment variables:
   - `DATABASE_URL` (from PostgreSQL)
   - `JWT_SECRET_KEY`
   - Other API keys
6. Deploy!

## ✅ Step 4: Update Frontend Environment Variable

In Vercel Dashboard → Your Frontend Project → Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

## ✅ Step 5: Update Backend CORS

In your backend code (`app/api/server.py`):

```python
allow_origins=[
    "https://your-frontend.vercel.app",
    "http://localhost:3000",
]
```

## 📋 Checklist

### Frontend Repo
- [ ] Created GitHub repository
- [ ] Pushed frontend code
- [ ] Deployed to Vercel
- [ ] Set `NEXT_PUBLIC_API_URL` environment variable
- [ ] Tested deployment

### Backend Repo
- [ ] Created GitHub repository
- [ ] Pushed backend code
- [ ] Deployed to Railway/Render/Fly.io
- [ ] Set environment variables
- [ ] Updated CORS settings
- [ ] Tested API endpoints

## 🎉 Benefits

✅ **No root directory config needed** - Frontend repo is already at root  
✅ **Cleaner deployments** - Each repo deploys independently  
✅ **Easier to manage** - No confusion about what to deploy  
✅ **Better CI/CD** - Separate pipelines  

---

**See `SEPARATE_REPOS_GUIDE.md` for detailed instructions!**

