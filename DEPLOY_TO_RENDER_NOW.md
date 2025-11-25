# 🚀 Deploy to Render.com - Step by Step

## ✅ Files Ready

I've created:
- ✅ `render.yaml` - Render configuration (auto-creates web service + database)
- ✅ `RENDER_DEPLOYMENT.md` - Complete deployment guide
- ✅ `RENDER_QUICK_START.md` - Quick reference
- ✅ `RENDER_ENVIRONMENT_VARS.md` - Environment variables guide

## 🎯 Quick Deployment (5 Steps)

### Step 1: Push to GitHub

```bash
git add render.yaml
git commit -m "Add Render.com deployment configuration"
git push origin main
```

### Step 2: Go to Render Dashboard

1. Visit: https://dashboard.render.com
2. Sign up or log in (free account works)

### Step 3: Create Blueprint

1. Click **"New +"** button (top right)
2. Select **"Blueprint"**
3. Connect your GitHub account (if not already)
4. Select your repository: `python-scrapper` (or your backend repo)
5. Render will detect `render.yaml`
6. Click **"Apply"**

### Step 4: Configure

Render will create:
- ✅ **Web Service** (your FastAPI app)
- ✅ **PostgreSQL Database** (auto-configured)

**Set Environment Variables:**

1. Click on your **Web Service**
2. Go to **Environment** tab
3. Add:
   ```
   JWT_SECRET_KEY=<generate random 32+ character string>
   ```
   - Generate: https://randomkeygen.com/ (use 64-char key)
   - Or: `openssl rand -hex 32`
4. `DATABASE_URL` is **auto-set** from PostgreSQL (don't set manually)

**Optional API Keys** (add if needed):
```
GOOGLE_PLACES_API_KEY=your-key
GROQ_API_KEY=your-key
```

### Step 5: Deploy

- Render automatically starts deployment
- Wait **5-10 minutes** for first deployment
- Check **Logs** tab for progress

## ✅ After Deployment

### Test Your API

1. **Health Check**
   ```
   https://your-app.onrender.com/health
   ```
   Should return: `{"status": "healthy"}`

2. **API Docs**
   ```
   https://your-app.onrender.com/docs
   ```
   Should show FastAPI Swagger UI

### Run Database Migrations

**Option A: Via Render Shell**

1. Web Service → **Shell** tab
2. Run:
   ```bash
   alembic upgrade head
   ```

**Option B: Via Migration Endpoint**

Add migration endpoint to your routes, then call:
```
POST https://your-app.onrender.com/api/admin/migrate
```

### Create Admin User

In Render Shell:
```bash
python create_user.py
```

Or use the signup endpoint.

## 🔧 Update Frontend

Update your frontend's environment variable:

```
NEXT_PUBLIC_API_URL=https://your-app.onrender.com
```

## 🎉 Why Render is Better

✅ **No cold starts** - Always running  
✅ **Writable filesystem** - Uploads directory works  
✅ **PostgreSQL included** - Easy database setup  
✅ **No timeout limits** - Long operations work  
✅ **Better Python support** - Designed for Python  
✅ **Free tier** - Good for development  

## 📋 Checklist

- [ ] Push `render.yaml` to GitHub
- [ ] Create Blueprint in Render
- [ ] Set `JWT_SECRET_KEY` environment variable
- [ ] Wait for deployment (5-10 min)
- [ ] Test `/health` endpoint
- [ ] Run database migrations
- [ ] Create admin user
- [ ] Update frontend `NEXT_PUBLIC_API_URL`
- [ ] Update CORS settings
- [ ] Test all endpoints

---

**Ready to deploy? Just push to GitHub and create the Blueprint in Render!** 🚀

