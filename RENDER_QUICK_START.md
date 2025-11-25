# Quick Start: Deploy to Render.com

## 🚀 Fast Deployment (5 Steps)

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Add Render configuration"
git push origin main
```

### Step 2: Go to Render

1. Visit: https://dashboard.render.com
2. Sign up/Login
3. Click "New +" → "Blueprint"

### Step 3: Connect Repository

1. Connect GitHub account
2. Select your repository: `python-scrapper`
3. Render will detect `render.yaml`
4. Click "Apply"

### Step 4: Set Environment Variables

After services are created:

1. **Web Service** → Environment
2. Add:
   ```
   JWT_SECRET_KEY=<generate random 32+ chars>
   ```
3. `DATABASE_URL` is auto-set from PostgreSQL

### Step 5: Deploy

- Render auto-deploys
- Wait 5-10 minutes
- Your API will be live!

## ✅ What Render Creates

- **Web Service** - Your FastAPI app
- **PostgreSQL Database** - Auto-configured

## 📋 After Deployment

1. **Test API**: `https://your-app.onrender.com/health`
2. **Run migrations**: Via Shell or migration endpoint
3. **Create admin user**: `python create_user.py` in Shell
4. **Update frontend**: Set `NEXT_PUBLIC_API_URL` to your Render URL

## 🎉 Done!

Your backend is now live on Render.com!

**See `RENDER_DEPLOYMENT.md` for detailed instructions.**

