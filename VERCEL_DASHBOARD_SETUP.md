# ⚠️ CRITICAL: Set Root Directory in Vercel Dashboard

## The Problem

Your build is failing because Vercel is still using the root directory. The error shows:
```
Error: ENOENT: no such file or directory, open '/vercel/path0/package.json'
Command "cd frontend && npm install" exited with 254
```

**This means the Root Directory is NOT set correctly in your Vercel Dashboard.**

## ✅ SOLUTION: Set Root Directory in Dashboard (REQUIRED)

### Step-by-Step Instructions:

1. **Go to Vercel Dashboard**
   - Open: https://vercel.com/dashboard
   - Make sure you're logged in

2. **Find Your Project**
   - Look for: **python-scrapper**
   - Click on it

3. **Open Settings**
   - Click **"Settings"** (top menu bar, next to "Deployments")

4. **Go to General Settings**
   - Click **"General"** (left sidebar, under Settings)

5. **Find Root Directory Section**
   - Scroll down until you see **"Root Directory"**
   - It might show "/" or be empty
   - Click the **"Edit"** button next to it

6. **Set Root Directory**
   - **Clear any existing value** (if there is one)
   - Type: `frontend` (lowercase, no quotes, no slashes)
   - Click **"Save"**

7. **Verify It's Set**
   - You should now see: **Root Directory: frontend**
   - If it still shows "/" or empty, try again

8. **Add Environment Variable (if not already added)**
   - Still in Settings, click **"Environment Variables"** (left sidebar)
   - Click **"Add New"**
   - **Key:** `NEXT_PUBLIC_API_URL`
   - **Value:** Your backend URL (e.g., `https://your-backend.railway.app`)
   - Select all environments: Production, Preview, Development
   - Click **"Save"**

9. **Redeploy**
   - Go to **"Deployments"** tab (top menu)
   - Find the latest/failed deployment
   - Click the **"..."** (three dots menu) on the right
   - Click **"Redeploy"**
   - Click **"Redeploy"** again to confirm

## What Should Happen After This

✅ Build logs should show:
```
Installing dependencies...
npm install
... (packages installing)

Building application...
npm run build
next build
... (Next.js building)
```

✅ NO more errors about `/vercel/path0/package.json`  
✅ Build completes successfully  
✅ Deployment succeeds  

## If You Don't See "Root Directory" Option

If you can't find the Root Directory setting:

1. **Delete the project** (Settings → General → scroll to bottom → Delete Project)
2. **Re-import** (Add New Project → Import Repository)
3. **During import**, BEFORE clicking "Deploy":
   - Look for "Root Directory" or "Configure Project"
   - Click "Edit" next to Root Directory
   - Set to: `frontend`
4. Add environment variable
5. Click "Deploy"

## Why This Is Required

- The `vercel.json` file helps, but Vercel Dashboard settings take precedence
- Root Directory must be set in BOTH places for maximum compatibility
- Dashboard setting ensures Vercel knows to only deploy from `frontend`

## Visual Guide

```
Vercel Dashboard
├── Your Project (python-scrapper)
    ├── Settings (top menu)
        ├── General (left sidebar)
            └── Root Directory ← EDIT THIS!
                └── Set to: frontend
        └── Environment Variables (left sidebar)
            └── Add: NEXT_PUBLIC_API_URL
    └── Deployments (top menu)
        └── Redeploy latest deployment
```

## Still Having Issues?

If after setting Root Directory in dashboard you still get errors:

1. **Check Build Logs:**
   - Deployments → Click failed deployment → View Build Logs
   - Look for what directory it's building from
   - Should see references to `frontend` directory

2. **Verify Root Directory:**
   - Go back to Settings → General
   - Confirm it shows: `frontend`
   - If it shows `/` or blank, it's not set correctly

3. **Try Deleting and Re-importing:**
   - Sometimes Vercel caches the configuration
   - Delete project and re-import fresh

---

**THE KEY: Root Directory MUST be set to `frontend` in Vercel Dashboard Settings!**

This is the ONLY way to fix the `/vercel/path0/package.json` error.

