# 🚨 URGENT: Fix Vercel Python Import Error

## The Error (From Your Logs)

```
Error importing `app/main.py`: Traceback (most recent call last)
File "/var/task/vc__handler__python.py"
```

**This means Vercel is trying to run your Python backend instead of deploying Next.js frontend!**

## ✅ THE FIX (Do This Now)

### Step 1: Set Root Directory in Vercel Dashboard

**THIS IS CRITICAL - The vercel.json file alone won't work!**

1. Go to: **https://vercel.com/dashboard**
2. Click on your project: **python-scrapper**
3. Click **Settings** (top menu)
4. Click **General** (left sidebar)
5. Scroll down to **"Root Directory"**
6. Click **"Edit"** button
7. **Clear any existing value**
8. Type: `frontend` (exactly this, lowercase, no quotes)
9. Click **"Save"**

### Step 2: Verify It's Set

After saving, you should see:
- **Root Directory:** `frontend` (displayed in settings)

### Step 3: Add Environment Variable

1. Still in Settings, click **"Environment Variables"** (left sidebar)
2. Click **"Add New"**
3. **Key:** `NEXT_PUBLIC_API_URL`
4. **Value:** Your backend URL (e.g., `https://your-backend.railway.app`)
5. Check all environments: **Production**, **Preview**, **Development**
6. Click **"Save"**

### Step 4: Redeploy

1. Go to **"Deployments"** tab (top menu)
2. Find the latest deployment
3. Click the **"..."** (three dots) menu
4. Click **"Redeploy"**
5. Click **"Redeploy"** again to confirm

## What Should Happen After Fix

✅ Build logs should show:
- "Installing dependencies..." (from frontend directory)
- "Building Next.js application..."
- NO Python-related errors
- NO "Error importing app/main.py"

✅ Deployment should succeed

## If Root Directory Setting Doesn't Appear

If you don't see "Root Directory" option:

1. **Delete the project** (Settings → General → Delete Project)
2. **Re-import** (Add New Project → Import Repository)
3. **BEFORE clicking Deploy:**
   - Click **"Edit"** under "Root Directory"
   - Set to: `frontend`
4. Add environment variable
5. Click **"Deploy"**

## Alternative: Deploy Only Frontend Directory

If dashboard settings don't work, use Vercel CLI from frontend directory:

```bash
# Navigate to frontend
cd frontend

# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

When prompted:
- Set up and deploy? **Yes**
- Which scope? **Your account**
- Link to existing project? **No** (creates new project)
- What's your project's name? **python-scrapper-frontend** (or any name)
- In which directory is your code located? **./** (current directory, which is frontend)

## Why This Error Happens

Vercel is detecting:
- `app/main.py` (Python file)
- `requirements.txt` (Python dependencies)
- Root `package.json` (monorepo setup)

And trying to deploy them as serverless functions.

**Setting Root Directory to `frontend` tells Vercel:**
- "Only look in the `frontend` folder"
- "Ignore everything else"
- "This is a Next.js project, not Python"

## Verification Checklist

After setting root directory, check:

- [ ] Root Directory shows `frontend` in Vercel Dashboard
- [ ] Environment variable `NEXT_PUBLIC_API_URL` is set
- [ ] Build logs show Next.js commands (not Python)
- [ ] No "Error importing app/main.py" in logs
- [ ] Deployment succeeds

## Still Getting Errors?

1. **Check Build Logs:**
   - Go to Deployments → Click failed deployment → View Build Logs
   - Look for what directory it's building from
   - If you see `app/main.py` mentioned, root directory is NOT set correctly

2. **Try Deleting and Re-importing:**
   - Sometimes Vercel caches the old configuration
   - Delete project and re-import fresh

3. **Use Vercel CLI:**
   - Deploy from `frontend` directory directly
   - This bypasses dashboard configuration issues

---

**The key is: Root Directory MUST be set to `frontend` in the Vercel Dashboard!**

