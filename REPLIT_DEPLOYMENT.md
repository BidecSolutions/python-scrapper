# Deploy Backend to Replit - Complete Guide

## Why Replit?

Replit is a great platform for Python backends:
- ✅ **Easy setup** - Just import repository
- ✅ **Built-in database** - Replit DB included
- ✅ **Free tier** - Good for development
- ✅ **Automatic deployments** - Deploys on push
- ✅ **Live collaboration** - Team features
- ✅ **Simple hosting** - One-click deploy

## Step 1: Prepare Your Repository

### Files Created

✅ `.replit` - Replit configuration  
✅ `main.py` - Replit entry point  
✅ `replit.nix` - Nix package configuration  
✅ `requirements.txt` - Python dependencies  

### Verify Files

Make sure these exist:
- `app/api/server.py` - FastAPI application
- `requirements.txt` - All dependencies
- `.replit` - Replit configuration
- `main.py` - Entry point

## Step 2: Push to GitHub

```bash
git add .replit main.py replit.nix
git commit -m "Add Replit deployment configuration"
git push origin main
```

## Step 3: Import to Replit

### Option A: Import from GitHub (Recommended)

1. **Go to Replit**
   - Visit: https://replit.com
   - Sign up or log in

2. **Create Repl**
   - Click **"Create Repl"** (or "+ Create")
   - Select **"Import from GitHub"**
   - Paste your repository URL: `https://github.com/yourusername/python-scrapper`
   - Click **"Import from GitHub"**

3. **Configure**
   - **Name**: `leadflux-backend` (or your choice)
   - **Template**: Python (auto-detected)
   - **Public/Private**: Your choice
   - Click **"Import"**

### Option B: Create New Repl

1. **Create Repl**
   - Click **"Create Repl"**
   - Select **"Python"** template
   - Name: `leadflux-backend`

2. **Connect GitHub**
   - Click **"Version control"** (left sidebar)
   - Click **"Import from GitHub"**
   - Paste repository URL
   - Click **"Import"**

## Step 4: Install Dependencies

Replit will auto-install from `requirements.txt`, but verify:

1. **Open Shell** (bottom panel or Tools → Shell)
2. **Run**:
   ```bash
   pip install -r requirements.txt
   ```

Or click **"Run"** button - Replit will install dependencies automatically.

## Step 5: Set Environment Variables

### In Replit

1. **Click Secrets** (lock icon in left sidebar)
   - Or: Tools → Secrets

2. **Add Secrets**:
   ```
   DATABASE_URL=sqlite:///./lead_scraper.db
   JWT_SECRET_KEY=<generate random 32+ chars>
   ```
   
   Optional API keys:
   ```
   GOOGLE_PLACES_API_KEY=your-key
   GROQ_API_KEY=your-key
   GOOGLE_SEARCH_API_KEY=your-key
   GOOGLE_SEARCH_CX=your-key
   OPENCAGE_API_KEY=your-key
   ```

3. **For PostgreSQL** (if using external):
   ```
   DATABASE_URL=postgresql://user:password@host:5432/database
   ```

### Using Replit Database

Replit includes a built-in database:

1. **Open Database** (left sidebar → Database icon)
2. **Create new database** (if needed)
3. **Use connection string** provided by Replit
4. **Or use SQLite** for simpler setup (default)

## Step 6: Run and Test

### Run Locally in Replit

1. **Click "Run"** button (top center)
2. **Or**: Press `Ctrl+Enter` (Windows) / `Cmd+Enter` (Mac)
3. **Wait** for server to start
4. **Check console** for: `Application startup complete`

### Test Endpoints

1. **Health Check**:
   - URL shown in console (e.g., `https://your-repl.repl.co`)
   - Visit: `https://your-repl.repl.co/health`
   - Should return: `{"status": "healthy"}`

2. **API Docs**:
   - Visit: `https://your-repl.repl.co/docs`
   - Should show FastAPI Swagger UI

## Step 7: Deploy to Production

### Enable Always-On (Free Tier)

1. **Click "Run"** tab
2. **Toggle "Always On"** (if available)
3. **Note**: Free tier may spin down after inactivity

### Enable Webview

1. **Click "Run"** tab
2. **Check "Always On"**
3. Your app will be accessible at: `https://your-repl.repl.co`

### Production Deployment

1. **Upgrade to Hacker Plan** (optional, for always-on)
2. **Or**: Keep free tier (spins down after inactivity)

## Step 8: Run Database Migrations

### Option A: Via Replit Shell

1. **Open Shell** (bottom panel)
2. **Run**:
   ```bash
   alembic upgrade head
   ```

### Option B: Via Migration Endpoint

Add migration endpoint, then call:
```
POST https://your-repl.repl.co/api/admin/migrate
```

## Step 9: Create Admin User

### Via Shell

```bash
python create_user.py
```

Or use the signup endpoint.

## Step 10: Update Frontend

Update your frontend's environment variable:

```
NEXT_PUBLIC_API_URL=https://your-repl.repl.co
```

## Step 11: Update CORS

Update `app/api/server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",
        "https://your-repl.repl.co",  # Add Replit URL
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Replit Features

### Built-in Database

Replit includes a database:
- **Access**: Left sidebar → Database icon
- **Use connection string** from Replit
- **Or use SQLite** for simpler setup

### Secrets Management

- **Access**: Left sidebar → Secrets (lock icon)
- **Secure**: Encrypted environment variables
- **Easy**: UI-based management

### Automatic Deployments

- **Auto-deploys** on git push
- **Or manual deploy** via Run button
- **Live URL**: `https://your-repl.repl.co`

## Environment Variables Reference

### Required
```
DATABASE_URL=sqlite:///./lead_scraper.db
JWT_SECRET_KEY=<generate random 32+ chars>
```

### Optional (API Keys)
```
GOOGLE_PLACES_API_KEY=your-key
GROQ_API_KEY=your-key
GOOGLE_SEARCH_API_KEY=your-key
GOOGLE_SEARCH_CX=your-key
OPENCAGE_API_KEY=your-key
```

## Troubleshooting

### App Not Starting

1. **Check logs** - Console shows errors
2. **Verify dependencies** - Run `pip install -r requirements.txt`
3. **Check main.py** - Entry point correct

### Port Issues

- Replit provides `$PORT` automatically
- Check `.replit` file has correct port config
- Default: Port 8000

### Database Connection

1. **Check DATABASE_URL** - In Secrets
2. **Test connection** - Via Shell
3. **Use Replit DB** - Built-in database

### Module Not Found

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Check requirements.txt** - All dependencies listed
3. **Restart Repl** - Click Stop, then Run

## Replit Advantages

✅ **Easy setup** - Just import from GitHub  
✅ **Built-in database** - No external setup needed  
✅ **Free tier** - Good for development  
✅ **Live collaboration** - Team features  
✅ **Simple hosting** - One-click deploy  

## Next Steps

1. ✅ Import repository to Replit
2. ✅ Install dependencies
3. ✅ Set environment variables (Secrets)
4. ✅ Run application
5. ✅ Test endpoints
6. ✅ Run database migrations
7. ✅ Create admin user
8. ✅ Update frontend API URL
9. ✅ Update CORS settings

---

**Replit is great for quick deployments and development!** 🚀

