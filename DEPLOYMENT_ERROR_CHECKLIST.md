# Vercel Deployment Error Checklist

## Current Issue: Module Not Found Errors

We've been fixing missing dependencies one by one:
1. ✅ Fixed: `mangum` - Added to requirements.txt
2. ✅ Fixed: `numpy` - Added to requirements.txt

## If You're Still Seeing Errors

### Step 1: Make Sure Changes Are Pushed

Check if your updated `requirements.txt` is pushed to GitHub:

```bash
# Check git status
git status

# If requirements.txt shows as modified:
git add requirements.txt
git commit -m "Add missing dependencies (numpy, mangum)"
git push origin main
```

### Step 2: Check the Specific Error

What error message are you seeing now?

**If it's still `ModuleNotFoundError: No module named 'numpy'`:**
- The changes haven't been pushed yet, or
- Vercel hasn't redeployed yet
- **Solution**: Push the changes and wait 2-3 minutes

**If it's a different module (e.g., `sklearn`, `pandas`, etc.):**
- That module is also missing
- **Solution**: Add it to `requirements.txt` and push

**If it's a different type of error:**
- Share the error message for help

## Common Missing Dependencies

Based on your codebase, these might also need to be explicit:

```txt
# Already in requirements.txt:
numpy>=1.24.0
scikit-learn>=1.3.0
pandas>=2.0.0
joblib>=1.3.0
```

If you see errors for:
- `sklearn` → Add `scikit-learn` (already there)
- `pd` or `pandas` → Add `pandas` (already there)
- Any other module → Add it to `requirements.txt`

## Quick Fix Process

For any `ModuleNotFoundError`:

1. **Identify the missing module** from the error
2. **Add it to `requirements.txt`**
3. **Commit and push:**
   ```bash
   git add requirements.txt
   git commit -m "Add [module-name] dependency"
   git push origin main
   ```
4. **Wait for Vercel to redeploy** (2-3 minutes)
5. **Check if error is resolved**

## Verify Deployment

After pushing:

1. Go to Vercel Dashboard → Your Project → Deployments
2. Click on the latest deployment
3. Check the build logs
4. Look for:
   - "Installing dependencies..."
   - Should see `numpy`, `mangum`, etc. being installed
   - No `ModuleNotFoundError` after installation

## If Errors Persist

1. Check Vercel build logs for specific errors
2. Verify all dependencies are in `requirements.txt`
3. Make sure `installCommand` is set in `vercel.json` (it is ✅)
4. Ensure changes are pushed to GitHub

---

**Next Step**: Push your changes and check what the new error is (if any)!

