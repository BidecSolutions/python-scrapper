# 🚨 CRITICAL: Fix Vercel Deployment Error

## The Problem

Error: `FUNCTION_INVOCATION_FAILED` - Vercel is deploying from the wrong directory.

## ✅ REQUIRED: Set Root Directory in Vercel Dashboard

**The `vercel.json` file alone is NOT enough. You MUST set it in the dashboard.**

### Quick Fix (3 Steps):

1. **Open Vercel Dashboard**
   - Go to: https://vercel.com/dashboard
   - Click your project

2. **Set Root Directory**
   - Settings → General → Root Directory
   - Click "Edit"
   - Type: `frontend`
   - Click "Save"

3. **Redeploy**
   - Deployments tab
   - Click "Redeploy" on latest deployment

## Detailed Steps with Screenshots Guide

### Step 1: Navigate to Settings
```
Dashboard → Your Project → Settings (top menu) → General (left sidebar)
```

### Step 2: Edit Root Directory
- Scroll to "Root Directory" section
- Click **"Edit"** button
- **Clear any existing value**
- Type: `frontend` (lowercase, no quotes, no slashes)
- Click **"Save"**

### Step 3: Add Environment Variable
- Settings → Environment Variables (left sidebar)
- Click **"Add New"**
  - **Key:** `NEXT_PUBLIC_API_URL`
  - **Value:** Your backend URL (e.g., `https://api.yourdomain.com`)
  - **Environments:** Check Production, Preview, Development
- Click **"Save"**

### Step 4: Redeploy
- Go to **"Deployments"** tab
- Find latest deployment
- Click **"..."** (three dots menu)
- Click **"Redeploy"**
- Confirm

## What You Should See After Fix

✅ Build logs show: "Installing dependencies..." (in frontend directory)  
✅ Build logs show: "Building Next.js application..."  
✅ No Python-related errors  
✅ Deployment succeeds  

## If It Still Doesn't Work

### Option A: Delete and Re-import Project

1. Delete the project in Vercel Dashboard
2. Go to "Add New Project"
3. Import your repository
4. **IMPORTANT:** Before clicking "Deploy":
   - Click "Edit" under "Root Directory"
   - Set to: `frontend`
5. Add environment variable: `NEXT_PUBLIC_API_URL`
6. Click "Deploy"

### Option B: Use Vercel CLI from Frontend Directory

```bash
cd frontend
npm i -g vercel
vercel login
vercel --prod
```

When prompted:
- Set up and deploy? **Yes**
- Which scope? **Your account**
- Link to existing project? **No** (or Yes if reconnecting)
- What's your project's name? **Enter a name**
- In which directory is your code located? **./** (current directory)

## Checklist

Before redeploying, ensure:
- [ ] Root Directory is set to `frontend` in Vercel Dashboard
- [ ] Environment variable `NEXT_PUBLIC_API_URL` is added
- [ ] Backend is deployed and accessible
- [ ] Backend URL is correct in environment variable

## Still Stuck?

1. Go to Vercel Dashboard → Deployments
2. Click on the failed deployment
3. Click "View Build Logs"
4. Copy the error message
5. Check what directory it's trying to build from
6. If it shows root directory, the Root Directory setting didn't apply

## Expected Build Log Output (After Fix)

```
Installing dependencies...
> npm install
... (packages installing)

Building application...
> npm run build
> next build
... (Next.js building)

Build completed successfully!
```

If you see Python or backend-related errors, the root directory is still not set correctly.

