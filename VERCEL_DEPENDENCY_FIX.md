# Fix: Vercel Not Installing Dependencies

## Problem

Even though `mangum` is in `requirements.txt`, Vercel isn't installing it, causing:
```
ModuleNotFoundError: No module named 'mangum'
```

## Solution Applied

I've made two changes:

### 1. Updated `api/index.py`

Made it try Mangum first, but fall back to direct app export if Mangum isn't available:

```python
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    # Fallback to direct app export
    handler = app
```

### 2. Updated `vercel.json`

Added explicit `installCommand` to ensure Vercel installs dependencies:

```json
{
  "installCommand": "pip install -r requirements.txt"
}
```

## Next Steps

### Step 1: Commit and Push

```bash
git add api/index.py vercel.json
git commit -m "Fix: Add installCommand and Mangum fallback"
git push origin main
```

### Step 2: Redeploy

After pushing:
- Vercel will automatically redeploy
- It will run `pip install -r requirements.txt`
- Mangum should be installed

### Step 3: Verify

Check deployment logs:
- Should see: "Installing dependencies..."
- Should see: `pip install -r requirements.txt`
- Should see: `mangum` being installed
- No more `ModuleNotFoundError`

## Alternative: If Mangum Still Doesn't Install

If the error persists, the fallback in `api/index.py` will try to use the app directly. However, this might not work on all Vercel plans.

**Best Solution**: Ensure `requirements.txt` is in the root and properly formatted, then redeploy.

---

**After pushing these changes, Vercel should install mangum!** 🚀

