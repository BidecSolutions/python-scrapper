# Vercel Deployment Fix

## Problem

The error "This Serverless Function has crashed" occurs because Vercel is trying to deploy from the root directory instead of the `frontend` directory.

## Solution

I've created a root-level `vercel.json` that tells Vercel to use the `frontend` directory. However, **you need to configure this in the Vercel Dashboard**:

### Method 1: Set Root Directory in Vercel Dashboard (Recommended)

1. Go to your Vercel project dashboard
2. Click on **Settings**
3. Go to **General** settings
4. Scroll down to **Root Directory**
5. Click **Edit**
6. Set the root directory to: `frontend`
7. Click **Save**
8. Redeploy your project

### Method 2: Delete and Re-import Project

1. In Vercel Dashboard, delete your current project
2. Go to **Add New Project**
3. Import your repository again
4. **During import**, click **"Edit"** under **Root Directory**
5. Set it to: `frontend`
6. Add environment variable: `NEXT_PUBLIC_API_URL` = your backend URL
7. Click **Deploy**

### Method 3: Using Vercel CLI

If you're using the CLI, make sure you're in the project root and run:

```bash
vercel --cwd frontend
```

Or set it in `vercel.json` (already done) and run:

```bash
vercel
```

## Files Created

1. **Root `vercel.json`** - Configures Vercel to use `frontend` as root directory
2. **Root `.vercelignore`** - Excludes backend files from deployment
3. **Removed `frontend/vercel.json`** - Not needed, using root config

## Important Notes

1. **Root Directory MUST be set to `frontend`** in Vercel Dashboard
2. **Environment Variable** `NEXT_PUBLIC_API_URL` must be set to your backend URL
3. **Backend** must be deployed separately (Railway, Render, Fly.io, etc.)

## After Fixing

Once you set the root directory to `frontend`:
1. The build should succeed
2. Vercel will only deploy the Next.js frontend
3. Backend files will be ignored (thanks to `.vercelignore`)

## Quick Fix Steps

1. ✅ Root `vercel.json` created - sets root directory to `frontend`
2. ✅ `.vercelignore` created - excludes backend files
3. ⚠️ **YOU NEED TO**: Set root directory in Vercel Dashboard to `frontend`
4. ⚠️ **YOU NEED TO**: Add `NEXT_PUBLIC_API_URL` environment variable
5. ⚠️ **YOU NEED TO**: Redeploy

## Verification

After fixing, check:
- Build logs should show Next.js build commands
- No Python-related errors
- Build completes successfully
- Deployment succeeds

