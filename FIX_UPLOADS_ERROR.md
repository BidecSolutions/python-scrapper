# Fix: Uploads Directory Read-Only Filesystem Error

## Problem Fixed

Error: `OSError: [Errno 30] Read-only file system: 'uploads'`

Vercel's serverless filesystem is read-only, so it can't create the `uploads` directory at module import time.

## Solution Applied

✅ **Made directory creation optional** - wrapped in try/except  
✅ **Set UPLOADS_DIR to None** if creation fails (serverless)  
✅ **Added check in upload function** - returns 503 if uploads not supported  
✅ **Updated delete function** - checks if UPLOADS_DIR exists  

## Changes Made

### 1. Directory Creation (lines 91-103)
```python
UPLOADS_DIR = Path("uploads/logos")
try:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError) as e:
    # Serverless platforms have read-only filesystem
    logger.warning(f"Could not create uploads directory: {e}")
    UPLOADS_DIR = None  # Disable file uploads on serverless
```

### 2. Upload Function (lines 112-117)
```python
if UPLOADS_DIR is None:
    raise HTTPException(
        status_code=503,
        detail="File uploads not supported on serverless platforms. Please use cloud storage (S3, Vercel Blob, etc.)"
    )
```

### 3. Delete Function (line 151)
```python
if org.logo_url and UPLOADS_DIR:  # Check UPLOADS_DIR exists
    # ... delete logic
```

## What This Means

✅ **API will start successfully** on serverless platforms  
✅ **All other routes work** (upload route returns 503 with helpful message)  
⚠️ **File uploads won't work** on Vercel (need cloud storage)  
✅ **No crashes** - graceful handling  

## For Production (Cloud Storage)

To enable file uploads on serverless, use:
- **Vercel Blob Storage** - Built-in Vercel storage
- **AWS S3** - Popular cloud storage
- **Cloudflare R2** - S3-compatible storage
- **Supabase Storage** - Easy to use

## Next Steps

### Step 1: Commit and Push

```bash
git add app/api/routes_settings.py
git commit -m "Fix uploads directory for serverless - make optional"
git push origin main
```

### Step 2: API Should Start

After pushing:
- ✅ API will deploy successfully
- ✅ No more read-only filesystem errors
- ✅ Upload endpoint will return 503 with helpful message

---

**After pushing, the API should start successfully!** 🚀

