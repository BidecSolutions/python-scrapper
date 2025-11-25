# Quick Guide: Copy Frontend to New Repo

## Simple Steps

### Method 1: Using PowerShell Script (Easiest)

1. **Run this command** (replace with your new repo path):
   ```powershell
   .\copy-frontend.ps1 -NewRepoPath "D:\laragon\www\your-new-frontend-repo"
   ```

### Method 2: Manual Copy (Fast)

1. **Open File Explorer**
   - Go to: `D:\laragon\www\python-scrapper\frontend`
   - Select ALL (Ctrl+A)
   - Copy (Ctrl+C)

2. **Paste to New Repo**
   - Go to your new frontend repository folder
   - Paste (Ctrl+V)
   - If asked to replace, click "Yes to All"

3. **Commit and Push**
   ```bash
   cd path/to/your/new/frontend-repo
   npm install
   git add .
   git commit -m "Initial commit: Frontend files"
   git push origin main
   ```

## What Gets Copied

✅ All folders: `app/`, `components/`, `lib/`, `contexts/`, `types/`, `public/`  
✅ All config files: `package.json`, `tsconfig.json`, `next.config.js`, etc.  
✅ Documentation: `README.md`  
✅ Vercel config: `vercel.json`  

## What Gets Excluded (Don't Copy)

❌ `node_modules/` - Install with `npm install`  
❌ `.next/` - Generated during build  
❌ `.env.local` - Contains local secrets  

## After Copying

1. **Navigate to new repo**
   ```bash
   cd path/to/your/new/repo
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create .env.local** (from example)
   ```bash
   copy .env.local.example .env.local
   ```
   Then edit `.env.local` and add your backend URL

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Initial commit: Frontend application"
   git push origin main
   ```

5. **Deploy to Vercel**
   - Go to Vercel Dashboard
   - Import your repository
   - Add `NEXT_PUBLIC_API_URL` environment variable
   - Deploy!

---

**That's it! Your frontend is ready to deploy! 🚀**

