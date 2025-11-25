# Quick Deployment Checklist

## ✅ Pre-Deployment Checklist

### Frontend (Vercel)
- [ ] Code pushed to Git repository (GitHub/GitLab/Bitbucket)
- [ ] `frontend/vercel.json` created
- [ ] `frontend/.gitignore` configured
- [ ] `next.config.js` optimized for production
- [ ] Environment variables ready:
  - [ ] `NEXT_PUBLIC_API_URL` (your backend URL)

### Backend (Railway/Render/Fly.io)
- [ ] Backend deployed to hosting platform
- [ ] Database configured (PostgreSQL, not SQLite)
- [ ] Environment variables set:
  - [ ] `DATABASE_URL`
  - [ ] `JWT_SECRET_KEY`
  - [ ] API keys (Google, Groq, etc.)
- [ ] Database migrations run
- [ ] Super admin user created
- [ ] Health endpoint working (`/health`)
- [ ] CORS configured to allow Vercel domain

## 🚀 Deployment Steps

### Step 1: Deploy Backend (Choose one)

#### Option A: Railway (Recommended)
```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Add PostgreSQL database
railway add

# 5. Set environment variables
railway variables set DATABASE_URL=<postgres-url>
railway variables set JWT_SECRET_KEY=<your-secret-key>

# 6. Deploy
railway up
```

#### Option B: Render
1. Go to https://render.com
2. Create New → Web Service
3. Connect repository
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn app.api.server:app --host 0.0.0.0 --port $PORT`
6. Add PostgreSQL database
7. Set environment variables

### Step 2: Deploy Frontend to Vercel

#### Quick Method (CLI)
```bash
cd frontend
npm i -g vercel
vercel login
vercel
```

#### Or Use Dashboard
1. Go to https://vercel.com/new
2. Import your repository
3. **IMPORTANT**: Set root directory to `frontend`
4. Add environment variable: `NEXT_PUBLIC_API_URL`
5. Deploy!

## 📝 Environment Variables

### Frontend (Vercel)
```env
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

### Backend (Railway/Render)
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
JWT_SECRET_KEY=your-secret-key-here
GOOGLE_PLACES_API_KEY=optional
GROQ_API_KEY=optional
```

## 🔍 Post-Deployment Verification

- [ ] Frontend loads at Vercel URL
- [ ] Backend health check works: `https://backend-url.com/health`
- [ ] Can login with admin credentials
- [ ] API calls work (check browser console)
- [ ] No CORS errors
- [ ] Database connections working

## 🆘 Common Issues

### CORS Error
**Problem**: Frontend can't call backend API

**Solution**: Update backend CORS settings:
```python
# app/api/server.py
allow_origins=[
    "https://your-app.vercel.app",
    "https://your-custom-domain.com"
]
```

### Environment Variables Not Working
**Problem**: `NEXT_PUBLIC_API_URL` not accessible

**Solution**: 
1. Check variables in Vercel Dashboard
2. Redeploy after adding variables
3. Ensure variable names start with `NEXT_PUBLIC_`

### Database Connection Failed
**Problem**: Backend can't connect to database

**Solution**:
1. Verify `DATABASE_URL` format
2. Check database is accessible
3. Ensure SSL is enabled if required

## 📚 Full Documentation

See `VERCEL_DEPLOYMENT.md` for detailed instructions.

