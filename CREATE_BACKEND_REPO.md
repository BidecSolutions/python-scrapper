# Create Backend Repository - Step by Step

## Quick Commands

### Windows PowerShell

```powershell
# 1. From project root, create backend directory
cd ..
mkdir leadflux-backend
cd leadflux-backend

# 2. Copy backend files from original project
# (Run from original project root)
Copy-Item -Path "app" -Destination "../leadflux-backend/" -Recurse
Copy-Item -Path "migrations" -Destination "../leadflux-backend/" -Recurse
if (Test-Path "alembic") { Copy-Item -Path "alembic" -Destination "../leadflux-backend/" -Recurse }
if (Test-Path "config") { Copy-Item -Path "config" -Destination "../leadflux-backend/" -Recurse }
if (Test-Path "tests") { Copy-Item -Path "tests" -Destination "../leadflux-backend/" -Recurse }
Copy-Item -Path "requirements.txt" -Destination "../leadflux-backend/" -ErrorAction SilentlyContinue
Copy-Item -Path "pyproject.toml" -Destination "../leadflux-backend/" -ErrorAction SilentlyContinue
Copy-Item -Path "create_user.py" -Destination "../leadflux-backend/" -ErrorAction SilentlyContinue
Copy-Item -Path "init_db.py" -Destination "../leadflux-backend/" -ErrorAction SilentlyContinue
Get-ChildItem -Path "." -Filter "migrate_*.py" | Copy-Item -Destination "../leadflux-backend/"

# 3. Navigate to backend directory
cd ../leadflux-backend

# 4. Create backend-specific files
# (See BACKEND_REPO_SETUP.md for file contents)

# 5. Initialize git
git init
git add .
git commit -m "Initial commit: Backend API"

# 6. Create GitHub repository first (via web interface)
#    Repository name: leadflux-backend

# 7. Add remote and push
git remote add origin https://github.com/yourusername/leadflux-backend.git
git branch -M main
git push -u origin main
```

## Files to Create

### `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/

# Virtual Environment
venv/
.venv/
ENV/
env/

# Database
*.db
*.sqlite
lead_scraper.db

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# Logs
*.log

# OS
.DS_Store
```

### `.env.example`

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/leadflux
JWT_SECRET_KEY=your-secret-key-min-32-chars
GOOGLE_PLACES_API_KEY=
GROQ_API_KEY=
```

### `README.md`

```markdown
# LeadFlux Backend API

FastAPI backend for LeadFlux platform.

## Quick Start

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python init_db.py
python create_user.py
uvicorn app.api.server:app --reload
```

Visit: http://localhost:8000/docs
```

## Deploy to Railway

1. Go to: https://railway.app
2. New Project → Deploy from GitHub
3. Select `leadflux-backend` repository
4. Add PostgreSQL database
5. Set environment variables
6. Deploy!

---

**See `BACKEND_REPO_SETUP.md` for complete details!**

