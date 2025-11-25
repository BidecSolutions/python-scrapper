# Backend Repository Setup Guide

This guide helps you create a separate backend repository from your monorepo.

## Step 1: Create Backend Repository Structure

### Files to Include

```
leadflux-backend/
├── app/                    # FastAPI application
│   ├── __init__.py
│   ├── api/                # API routes
│   ├── core/               # Database, ORM, config
│   ├── services/           # Business logic
│   ├── scraper/            # Scraping logic
│   ├── sources/            # Data sources
│   ├── workers/            # Background workers
│   ├── utils/              # Utilities
│   ├── schemas/            # Pydantic schemas
│   └── ai/                 # AI services
├── migrations/             # Database migration scripts
├── alembic/                # Alembic configuration
├── config/                 # Configuration files
├── tests/                  # Test files
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Python project config
├── alembic.ini             # Alembic config (copy from .example)
├── create_user.py          # User creation script
├── migrate_*.py            # Migration scripts
├── init_db.py              # Database initialization
├── .env.example            # Environment variables example
├── .gitignore              # Git ignore rules
└── README.md               # Backend documentation
```

## Step 2: Create Backend Repository

### Option A: Manual Setup

1. **Create new directory**
   ```bash
   mkdir leadflux-backend
   cd leadflux-backend
   ```

2. **Copy backend files**
   ```bash
   # From your original project root
   cp -r app/ ../leadflux-backend/
   cp -r migrations/ ../leadflux-backend/
   cp -r alembic/ ../leadflux-backend/
   cp -r config/ ../leadflux-backend/
   cp -r tests/ ../leadflux-backend/
   cp requirements.txt ../leadflux-backend/
   cp pyproject.toml ../leadflux-backend/
   cp create_user.py ../leadflux-backend/
   cp migrate_*.py ../leadflux-backend/
   cp init_db.py ../leadflux-backend/
   ```

3. **Create backend-specific files**
   - `.gitignore` (backend-specific)
   - `.env.example`
   - `README.md` (backend documentation)

4. **Initialize git**
   ```bash
   cd leadflux-backend
   git init
   git add .
   git commit -m "Initial commit: Backend API"
   git remote add origin https://github.com/yourusername/leadflux-backend.git
   git push -u origin main
   ```

### Option B: Use Git Subtree (Preserve History)

```bash
# From original project root
git subtree push --prefix . origin backend-main --exclude=frontend
```

## Step 3: Create Backend-Specific Files

### `.gitignore` (Backend)

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
.venv/
ENV/
env/
env.bak/
venv.bak/

# Database
*.db
*.sqlite
*.sqlite3
lead_scraper.db

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Alembic
alembic.ini
!alembic.ini.example

# Uploads (if needed)
uploads/
!uploads/.gitkeep
```

### `.env.example` (Backend)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/leadflux

# JWT
JWT_SECRET_KEY=your-secret-key-change-this-min-32-chars

# API Keys (Optional)
GOOGLE_PLACES_API_KEY=
GOOGLE_SEARCH_API_KEY=
GOOGLE_SEARCH_CX=
BING_SEARCH_API_KEY=
GROQ_API_KEY=
OPENCAGE_API_KEY=

# Server
HOST=0.0.0.0
PORT=8000
```

### `README.md` (Backend)

```markdown
# LeadFlux Backend API

FastAPI backend for the LeadFlux lead generation platform.

## Quick Start

### Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Initialize database
python init_db.py

# Create super admin user
python create_user.py

# Run server
uvicorn app.api.server:app --reload --port 8000
```

## Deployment

See deployment guides for:
- Railway
- Render
- Fly.io

## API Documentation

Once running, visit: http://localhost:8000/docs
```

## Step 4: Update Backend Code

### Update CORS Settings

```python
# app/api/server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",
        "https://your-custom-domain.com",
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Update Database Configuration

Ensure `DATABASE_URL` uses PostgreSQL in production (not SQLite).

## Step 5: Deploy Backend

See `VERCEL_DEPLOYMENT.md` for backend deployment options (Railway, Render, Fly.io).

## Benefits

✅ Clean separation of concerns  
✅ Independent versioning  
✅ Easier to scale  
✅ Clearer codebase  
✅ Better CI/CD pipelines  

