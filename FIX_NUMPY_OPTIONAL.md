# Fix: Make ML Routes Optional

## Problem

Even though `numpy` is in `requirements.txt`, Vercel isn't installing it properly, causing the entire API to fail to start because `routes_ml.py` imports `numpy` at the top level.

## Solution Applied

I've made the ML routes **optional** so the API can start even if `numpy` isn't installed:

### Changes Made

1. **Made ML router import optional** in `app/api/server.py`:
   ```python
   try:
       from app.api.routes_ml import router as ml_router
       ML_ROUTES_AVAILABLE = True
   except ImportError as e:
       logger.warning(f"ML routes not available: {e}")
       ml_router = None
       ML_ROUTES_AVAILABLE = False
   ```

2. **Conditionally register ML routes**:
   ```python
   if ML_ROUTES_AVAILABLE and ml_router:
       app.include_router(ml_router, prefix="/api", tags=["ml"])
   else:
       logger.warning("ML routes not registered - numpy/scikit-learn may not be installed")
   ```

## What This Means

✅ **API will start successfully** even without `numpy`  
✅ **All other routes work** (jobs, leads, auth, etc.)  
⚠️ **ML routes won't be available** if `numpy` isn't installed  
✅ **No more crashes** on startup  

## Next Steps

### Step 1: Commit and Push

```bash
git add app/api/server.py
git commit -m "Make ML routes optional to handle missing numpy"
git push origin main
```

### Step 2: API Should Start

After pushing:
- ✅ API will deploy successfully
- ✅ Most endpoints will work
- ⚠️ ML endpoints won't be available (but won't crash the API)

### Step 3: Fix NumPy Installation (Optional)

If you need ML features, we can:
1. Check why Vercel isn't installing numpy
2. Try alternative approaches
3. Or use a different deployment platform (Railway, Render) that handles large dependencies better

## Benefits

- **API works immediately** - No more startup crashes
- **Graceful degradation** - ML features are optional
- **Better error handling** - Logs warnings instead of crashing

---

**After pushing, your API should deploy successfully!** 🚀

