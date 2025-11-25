# Vercel Deployment Guide

This guide will help you deploy the LeadFlux frontend to Vercel.

## Prerequisites

1. A [Vercel account](https://vercel.com/signup)
2. The frontend code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. Your FastAPI backend deployed and accessible via a public URL

## Deployment Steps

### 1. Deploy Backend First

**Important:** The backend API must be deployed and accessible before deploying the frontend.

#### Option A: Deploy Backend to Railway (Recommended)
1. Go to [Railway](https://railway.app/)
2. Create a new project
3. Connect your repository or deploy directly
4. Set the root directory to the project root (not frontend/)
5. Add environment variables (see Backend Environment Variables below)
6. Set up PostgreSQL database (Railway provides free PostgreSQL)
7. Update `DATABASE_URL` to use PostgreSQL connection string
8. Note your backend URL (e.g., `https://your-app.railway.app`)

#### Option B: Deploy Backend to Render
1. Go to [Render](https://render.com/)
2. Create a new Web Service
3. Connect your repository
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.api.server:app --host 0.0.0.0 --port $PORT`
6. Add environment variables
7. Add PostgreSQL database
8. Update `DATABASE_URL`

#### Option C: Deploy Backend to Fly.io
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Run: `fly launch`
3. Configure database and environment variables
4. Deploy: `fly deploy`

### 2. Deploy Frontend to Vercel

#### Method 1: Using Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit [vercel.com/new](https://vercel.com/new)
   - Sign in with GitHub/GitLab/Bitbucket

2. **Import Your Repository**
   - Click "Import Project"
   - Select your repository
   - **Important:** Set the root directory to `frontend`:
     - Click "Edit" under "Root Directory"
     - Enter: `frontend`
     - Click "Continue"

3. **Configure Build Settings**
   - Framework Preset: **Next.js** (auto-detected)
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)
   - Install Command: `npm install` (default)
   - Node.js Version: 18.x or higher

4. **Add Environment Variables**
   - Click "Environment Variables"
   - Add the following variables:

   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   ```

   **Production Environment Variables:**
   - `NEXT_PUBLIC_API_URL`: Your deployed backend API URL
     - Example: `https://leadflux-api.railway.app`
     - Or: `https://your-app.onrender.com`
     - Or: `https://your-app.fly.dev`

5. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete
   - Your app will be live at `https://your-project.vercel.app`

#### Method 2: Using Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Navigate to Frontend Directory**
   ```bash
   cd frontend
   ```

4. **Deploy**
   ```bash
   vercel
   ```
   
   - Follow the prompts:
     - Set up and deploy? **Yes**
     - Which scope? **Select your account**
     - Link to existing project? **No** (first time)
     - Project name? **Enter a name**
     - Directory? **./**
     - Override settings? **No**

5. **Add Environment Variables**
   ```bash
   vercel env add NEXT_PUBLIC_API_URL production
   ```
   - Enter your backend URL when prompted

6. **Redeploy with Environment Variables**
   ```bash
   vercel --prod
   ```

### 3. Environment Variables Reference

#### Frontend Environment Variables (Vercel)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://api.leadflux.com` |

#### Backend Environment Variables (Railway/Render/Fly.io)

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Yes |
| `GOOGLE_PLACES_API_KEY` | Google Places API key | Optional |
| `GOOGLE_SEARCH_API_KEY` | Google Search API key | Optional |
| `GOOGLE_SEARCH_CX` | Google Search Engine ID | Optional |
| `GROQ_API_KEY` | Groq API key for AI features | Optional |
| `BING_SEARCH_API_KEY` | Bing Search API key | Optional |

### 4. Post-Deployment Steps

1. **Verify Backend is Accessible**
   - Test: `https://your-backend-url.com/health`
   - Should return: `{"status": "healthy"}`

2. **Update Frontend API URL**
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Ensure `NEXT_PUBLIC_API_URL` points to your backend

3. **Test Frontend**
   - Visit your Vercel deployment URL
   - Try logging in
   - Check browser console for any API errors

4. **Set Up Custom Domain (Optional)**
   - Go to Vercel Dashboard → Your Project → Settings → Domains
   - Add your custom domain
   - Configure DNS as instructed

### 5. Database Setup

**Important:** SQLite won't work in production. You must use PostgreSQL.

1. **Create PostgreSQL Database**
   - Railway: Automatically provides PostgreSQL
   - Render: Create a PostgreSQL database service
   - Fly.io: Use `fly postgres create`

2. **Update Database Connection**
   - Update `DATABASE_URL` in backend environment variables:
     ```
     postgresql+asyncpg://user:password@host:port/database
     ```

3. **Run Migrations**
   - Connect to your deployed backend
   - Run database migrations:
     ```bash
     # Via SSH or CLI
     python migrate_db.py
     ```

4. **Create Super Admin User**
   - Connect to deployed backend
   - Run: `python create_user.py`

### 6. Troubleshooting

#### Frontend Issues

**Issue: API calls failing with CORS errors**
- Solution: Ensure backend CORS is configured to allow your Vercel domain
- Update backend `allow_origins` in `app/api/server.py`:
  ```python
  allow_origins=[
    "https://your-app.vercel.app",
    "https://your-custom-domain.com"
  ]
  ```

**Issue: Environment variables not working**
- Solution: 
  1. Check variables are set in Vercel Dashboard
  2. Redeploy after adding variables
  3. Ensure variable names start with `NEXT_PUBLIC_` for client-side access

**Issue: Build fails**
- Solution:
  - Check build logs in Vercel Dashboard
  - Ensure `package.json` has correct scripts
  - Verify Node.js version (18+)

#### Backend Issues

**Issue: Database connection fails**
- Solution:
  - Verify `DATABASE_URL` is correct
  - Check database is accessible from deployment platform
  - Ensure database credentials are correct

**Issue: API not responding**
- Solution:
  - Check backend logs
  - Verify backend is running
  - Check health endpoint: `/health`

### 7. Continuous Deployment

Vercel automatically deploys on every push to your main branch:

1. **Push to Main Branch**
   ```bash
   git push origin main
   ```

2. **Vercel Automatically Deploys**
   - Every push triggers a new deployment
   - Preview deployments for pull requests

3. **Check Deployment Status**
   - Go to Vercel Dashboard
   - View deployment history
   - Check build logs

### 8. Production Checklist

- [ ] Backend deployed and accessible
- [ ] Database configured (PostgreSQL)
- [ ] Environment variables set in backend
- [ ] Frontend environment variables set in Vercel
- [ ] CORS configured on backend
- [ ] Database migrations run
- [ ] Super admin user created
- [ ] Custom domain configured (optional)
- [ ] SSL certificates active
- [ ] Health checks passing

### 9. Recommended Architecture

```
┌─────────────────┐
│   Vercel        │  ← Frontend (Next.js)
│   Frontend      │
└────────┬────────┘
         │
         │ HTTPS
         │
         ▼
┌─────────────────┐
│   Railway/      │  ← Backend (FastAPI)
│   Render/Fly.io │
└────────┬────────┘
         │
         │ PostgreSQL
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │  ← Database
│   Database      │
└─────────────────┘
```

### 10. Cost Estimate

- **Vercel**: Free tier (Hobby) - Sufficient for most projects
- **Railway**: $5/month - Includes database
- **Render**: Free tier available (with limitations)
- **Fly.io**: Pay-as-you-go

### 11. Security Considerations

1. **Environment Variables**
   - Never commit `.env` files
   - Use Vercel environment variables for secrets
   - Rotate API keys regularly

2. **CORS**
   - Limit allowed origins in production
   - Don't use `allow_origins=["*"]` in production

3. **JWT Secret**
   - Use a strong, random JWT secret
   - Never commit secrets to Git

4. **Database**
   - Use strong database passwords
   - Enable SSL connections
   - Regular backups

## Support

For issues:
- Vercel Docs: https://vercel.com/docs
- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs

---

**Happy Deploying! 🚀**

