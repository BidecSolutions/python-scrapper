# Copy Frontend to New Repository

## What You Need to Do

Since you've already created the new repository, you just need to copy all files from the `frontend` folder to your new repo.

## Option 1: Manual Copy (Windows)

### Step 1: Copy All Files

1. **Open File Explorer**
   - Navigate to: `D:\laragon\www\python-scrapper\frontend`
   - Select ALL files and folders (Ctrl+A)
   - Copy (Ctrl+C)

2. **Navigate to Your New Repo**
   - Go to where you cloned your new frontend repository
   - Example: `D:\laragon\www\leadflux-frontend` (or wherever it is)

3. **Paste All Files**
   - Paste (Ctrl+V) all files into the new repo folder
   - If asked to replace files, click "Yes to All"

### Step 2: Commit and Push

```bash
# Navigate to your new repo
cd D:\laragon\www\leadflux-frontend  # (or your repo path)

# Check status
git status

# Add all files
git add .

# Commit
git commit -m "Initial commit: Frontend files"

# Push to GitHub
git push origin main
```

## Option 2: PowerShell Script (Automated)

Run this from your project root:

```powershell
# Set your new repo path here
$newRepoPath = "D:\laragon\www\leadflux-frontend"  # CHANGE THIS!

# Source path (current frontend folder)
$sourcePath = "D:\laragon\www\python-scrapper\frontend"

# Copy all files
Write-Host "Copying files from $sourcePath to $newRepoPath..." -ForegroundColor Cyan
Copy-Item -Path "$sourcePath\*" -Destination "$newRepoPath\" -Recurse -Force

Write-Host "Files copied successfully!" -ForegroundColor Green
Write-Host "`nNow go to your new repo and run:" -ForegroundColor Yellow
Write-Host "  cd $newRepoPath" -ForegroundColor White
Write-Host "  git add ." -ForegroundColor White
Write-Host "  git commit -m 'Initial commit: Frontend files'" -ForegroundColor White
Write-Host "  git push origin main" -ForegroundColor White
```

## Option 3: Using Git (Preserves History)

If you want to preserve git history:

```bash
# From project root
cd frontend
git remote add new-origin https://github.com/yourusername/your-new-repo.git
git push new-origin main
```

## Files That Should Be Copied

Make sure these are copied:
- ✅ `app/` (all Next.js pages)
- ✅ `components/` (all React components)
- ✅ `contexts/` (React contexts)
- ✅ `lib/` (API client, utilities)
- ✅ `types/` (TypeScript types)
- ✅ `public/` (static assets)
- ✅ `package.json`
- ✅ `package-lock.json`
- ✅ `tsconfig.json`
- ✅ `next.config.js`
- ✅ `tailwind.config.ts`
- ✅ `postcss.config.js`
- ✅ `.gitignore`
- ✅ `vercel.json`
- ✅ `README.md`
- ✅ `.env.local.example`

## Files to EXCLUDE (Don't Copy)

- ❌ `node_modules/` (will be reinstalled)
- ❌ `.next/` (build output, will be regenerated)
- ❌ `.env.local` (contains sensitive local config)

## After Copying

1. **Navigate to New Repo**
   ```bash
   cd path/to/your/new/repo
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Create .env.local**
   ```bash
   copy .env.local.example .env.local
   # Then edit .env.local with your backend URL
   ```

4. **Test Locally**
   ```bash
   npm run dev
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "Initial commit: Frontend application"
   git push origin main
   ```

6. **Deploy to Vercel**
   - Go to Vercel Dashboard
   - Import your new repository
   - Add environment variable: `NEXT_PUBLIC_API_URL`
   - Deploy!

## Verify Everything Copied

Check that these folders exist in your new repo:
- `app/` ✓
- `components/` ✓
- `lib/` ✓
- `public/` ✓
- `package.json` ✓

---

**Need help? Let me know your new repo path and I can create a custom script!**

