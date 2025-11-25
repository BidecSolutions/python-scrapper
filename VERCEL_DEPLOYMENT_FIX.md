# Fix Vercel Deployment Error - Step by Step

## The Error
```
500: INTERNAL_SERVER_ERROR
Code: FUNCTION_INVOCATION_FAILED
```

This happens because Vercel is trying to deploy from the root directory instead of `frontend`.

## ✅ SOLUTION: Set Root Directory in Vercel Dashboard

### Step 1: Go to Vercel Dashboard
1. Visit: https://vercel.com/dashboard
2. Login to your account

### Step 2: Open Your Project
1. Find and click on your project: **python-scrapper**

### Step 3: Open Settings
1. Click on **Settings** (top menu bar)
2. Click on **General** (left sidebar)

### Step 4: Set Root Directory
1. Scroll down to find **Root Directory** section
2. Click **Edit** button
3. Enter: `frontend` (just the word "frontend", no slashes)
4. Click **Save**

### Step 5: Add Environment Variable
1. Still in Settings, click **Environment Variables** (left sidebar)
2. Click **Add New**
3. Key: `NEXT_PUBLIC_API_URL`
4. Value: Your backend URL (e.g., `https://your-backend.railway.app`)
5. Select environment: **Production**, **Preview**, and **Development** (check all)
6. Click **Save**

### Step 6: Redeploy
1. Go to **Deployments** tab (top menu)
2. Click the **...** (three dots) on the latest deployment
3. Click **Redeploy**
4. Click **Redeploy** again to confirm

## Alternative: Delete and Re-import

If the above doesn't work:

1. **Delete Current Project**
   - Go to Settings → General
   - Scroll to bottom
   - Click **Delete Project**
   - Confirm deletion

2. **Import Fresh**
   - Click **Add New Project**
   - Import your repository
   - **BEFORE clicking Deploy:**
     - Click **Edit** next to "Root Directory"
     - Set to: `frontend`
     - Click **Continue**
   - Add environment variable: `NEXT_PUBLIC_API_URL`
   - Click **Deploy**

## Verify Configuration

After setting root directory, verify:
- Root Directory shows: `frontend`
- Build logs show Next.js commands
- No Python-related errors in logs

## Common Issues

### Issue: Still getting errors after setting root directory
**Solution:** 
- Clear browser cache
- Try redeploying again
- Check build logs for specific errors

### Issue: Environment variable not working
**Solution:**
- Make sure variable name is exactly: `NEXT_PUBLIC_API_URL`
- Redeploy after adding variables
- Check that it's enabled for all environments

### Issue: Backend connection fails
**Solution:**
- Verify backend is deployed and accessible
- Test backend URL directly in browser: `https://your-backend-url.com/health`
- Update CORS settings on backend to allow Vercel domain

## What Should Happen After Fix

✅ Build logs show: "Building Next.js application"  
✅ No Python/backend errors  
✅ Deployment completes successfully  
✅ App loads at your Vercel URL  

## Still Having Issues?

Check the build logs:
1. Go to Deployments
2. Click on the failed deployment
3. Click "View Build Logs"
4. Look for specific error messages
5. Share the error with me if you need help

