# Quick Start: Deploy Backend to Vercel

## ✅ Files Created

I've already created all necessary files:
- ✅ `vercel.json` - Vercel configuration
- ✅ `api/index.py` - Serverless function entry point
- ✅ `.vercelignore` - Files to exclude

## 🚀 Deploy in 3 Steps

### Step 1: Push to GitHub

```bash
# If backend is already a separate repo:
git add .
git commit -m "Add Vercel configuration"
git push origin main
```

### Step 2: Deploy to Vercel

1. **Go to**: https://vercel.com/new
2. **Import** your backend repository
3. **Framework**: Leave as "Other" (auto-detect)
4. **Root Directory**: Leave empty
5. **Add Environment Variables**:
   - `DATABASE_URL` (PostgreSQL connection string)
   - `JWT_SECRET_KEY`
   - Other API keys as needed
6. **Click Deploy**

### Step 3: Configure Database

**Option A: Vercel Postgres** (Easiest)
- Vercel Dashboard → Your Project → Storage
- Create Postgres database
- Connection string auto-added as `DATABASE_URL`

**Option B: External Database**
- Use Neon, Supabase, Railway, or Render
- Add connection string as `DATABASE_URL` environment variable

## ⚠️ Important Limitations

Vercel serverless functions have:
- ⏱️ **10-60 second timeouts** (depending on plan)
- ❄️ **Cold starts** (first request may be slow)
- 📦 **Limited memory** (1GB default)

For production workloads, consider:
- **Railway** (recommended) - Better for FastAPI
- **Render** - Easy deployment
- **Fly.io** - Good performance

## 📋 After Deployment

1. ✅ Test API: `https://your-api.vercel.app/health`
2. ✅ View docs: `https://your-api.vercel.app/docs`
3. ✅ Run migrations (see VERCEL_BACKEND_DEPLOYMENT.md)
4. ✅ Update frontend `NEXT_PUBLIC_API_URL`
5. ✅ Update CORS settings

## 📚 Full Documentation

See `VERCEL_BACKEND_DEPLOYMENT.md` for:
- Complete deployment guide
- Database setup
- Running migrations
- Troubleshooting
- Alternative platforms

---

**Ready to deploy? Just push to GitHub and import in Vercel!** 🚀

