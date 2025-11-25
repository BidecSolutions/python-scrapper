# Create Frontend Repository - Step by Step

## Quick Commands

### From Your Current Project

```bash
# 1. Navigate to frontend
cd frontend

# 2. Initialize git (if not already)
git init

# 3. Add all files
git add .

# 4. Commit
git commit -m "Initial commit: Frontend application"

# 5. Create GitHub repository first (via web interface)
#    Repository name: leadflux-frontend (or your choice)

# 6. Add remote and push
git remote add origin https://github.com/yourusername/leadflux-frontend.git
git branch -M main
git push -u origin main
```

## Files Already Prepared

✅ `frontend/vercel.json` - Simple Vercel config (no root directory needed!)  
✅ `frontend/.gitignore` - Frontend-specific ignore rules  
✅ `frontend/.env.local.example` - Environment variable template  
✅ `frontend/README.md` - Frontend documentation  

## Deploy to Vercel

1. **Go to Vercel**: https://vercel.com/new
2. **Import Repository**: Select your `leadflux-frontend` repo
3. **Framework**: Next.js (auto-detected)
4. **Root Directory**: Leave empty (it's already the root!)
5. **Environment Variable**: Add `NEXT_PUBLIC_API_URL` = your backend URL
6. **Deploy**: Click Deploy

**No root directory configuration needed!** Since the frontend is now its own repo, Vercel will automatically use it as the root.

## After Deployment

1. ✅ Frontend deployed at: `https://your-project.vercel.app`
2. ✅ Update backend CORS to allow your Vercel domain
3. ✅ Test the connection between frontend and backend

---

**Much simpler than the monorepo setup!**

