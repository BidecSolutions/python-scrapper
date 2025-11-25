# 🚀 Quick Fix for Replit Deployment Error

## ⚡ Fastest Solution

### Step 1: Share the Error Message
**Please share the exact error message from Replit Console** so I can give you a specific fix!

### Step 2: Common Quick Fixes

#### Fix A: Nix Environment Build Error
**Error:** `attribute 'prybar-python312' missing` or `nix env: exit status 1`

**Solution:** ✅ Already fixed! The `replit.nix` has been updated. Just push to GitHub:
```bash
git commit -m "Fix replit.nix - remove prybar dependencies"
git push origin main
```
Then re-import or update your Replit project.

#### Fix B: Missing Module Error
**Error:** `ModuleNotFoundError: No module named 'X'`

**Solution:** In Replit Shell:
```bash
pip install -r requirements.txt
```

#### Fix C: Missing Secrets
**Error:** `KeyError: 'JWT_SECRET_KEY'` or database errors

**Solution:** 
1. Go to **Secrets** (lock icon in left sidebar)
2. Add:
   - Key: `JWT_SECRET_KEY`
   - Value: (any random 32+ character string)
3. Optional: `DATABASE_URL=sqlite:///./lead_scraper.db`

#### Fix D: Port Error
**Error:** `OSError: [Errno 48] Address already in use`

**Solution:** 
1. Click **Stop** button
2. Wait 5 seconds
3. Click **Run** again

#### Fix E: Import Error
**Error:** `ImportError: cannot import name 'app'` or `No module named 'app'`

**Solution:** Check PYTHONPATH is set:
1. Go to **Secrets**
2. Add: `PYTHONPATH=.` (if not already set)

### Step 3: Push Changes
The fixed files need to be pushed:
```bash
git commit -m "Fix Replit deployment configuration"
git push origin main
```

### Step 4: Verify in Replit
1. If you imported from GitHub: Click **Sync** or **Pull** to get latest changes
2. Check **Secrets** are set
3. Click **Run**

## 📋 Checklist

- [ ] Pushed `replit.nix` and `.replit` changes to GitHub
- [ ] Synced/Pulled in Replit
- [ ] Set `JWT_SECRET_KEY` in Secrets
- [ ] Clicked **Run**
- [ ] Checked Console for errors
- [ ] Tested `/health` endpoint

## 🔍 Still Not Working?

**Share these details:**
1. Full error message (copy from Console)
2. When it fails (building, starting, running)
3. What you've tried

---

**Most Common Issue:** Nix build error - Fixed! Just push and sync.

