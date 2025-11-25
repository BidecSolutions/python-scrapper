# Quick Fix for Vercel Deployment Error

## The Problem

Error: "This Serverless Function has crashed" - Vercel is trying to deploy from the root directory instead of the `frontend` directory.

## Quick Fix (Choose One Method)

### ✅ Method 1: Set Root Directory in Vercel Dashboard (EASIEST)

1. Go to: https://vercel.com/dashboard
2. Click on your project: **python-scrapper**
3. Click **Settings** (top menu)
4. Click **General** (left sidebar)
5. Scroll to **Root Directory** section
6. Click **Edit**
7. Enter: `frontend`
8. Click **Save**
9. Go to **Deployments** tab
10. Click **Redeploy** → **Redeploy** (confirm)

### ✅ Method 2: Delete and Re-import

1. Go to Vercel Dashboard
2. Delete your current project
3. Click **Add New Project**
4. Import your repository
5. **IMPORTANT**: Before clicking "Deploy":
   - Click **"Edit"** next to **Root Directory**
   - Set it to: `frontend`
   - Add environment variable: `NEXT_PUBLIC_API_URL` = your backend URL
6. Click **Deploy**

### ✅ Method 3: Using Vercel CLI

```bash
# Install Vercel CLI if not installed
npm i -g vercel

# From project root
cd frontend
vercel --prod
```

## Required Environment Variable

**Don't forget to add this in Vercel Dashboard → Settings → Environment Variables:**

```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

Replace `https://your-backend-url.com` with your actual deployed backend URL (Railway, Render, Fly.io, etc.)

## After Fixing

1. ✅ Build should succeed
2. ✅ Deployment should complete
3. ✅ Your app should be live at `https://your-project.vercel.app`

## Still Having Issues?

Check the build logs in Vercel Dashboard → Deployments → Click on failed deployment → View logs

Common issues:
- Missing environment variables
- Backend not accessible
- Build errors in frontend code

