# Render.com Environment Variables

## Required Variables

Set these in Render Dashboard → Your Web Service → Environment:

### DATABASE_URL
- **Auto-set** from PostgreSQL database
- Format: `postgresql://user:password@host:5432/database`
- Don't set manually - Render connects it automatically

### JWT_SECRET_KEY
- **Required** for authentication
- Generate a random 32+ character string
- Example: `openssl rand -hex 32`
- Or use: https://randomkeygen.com/

### PYTHON_VERSION
- **Optional** but recommended
- Value: `3.12.0` (or your preferred version)

## Optional API Keys

Add these if you use the features:

### Google Places API
```
GOOGLE_PLACES_API_KEY=your-key
```

### Google Search API
```
GOOGLE_SEARCH_API_KEY=your-key
GOOGLE_SEARCH_CX=your-search-engine-id
```

### Bing Search API
```
BING_SEARCH_API_KEY=your-key
```

### Groq AI (LLM)
```
GROQ_API_KEY=your-key
```

### OpenCage Geocoding
```
OPENCAGE_API_KEY=your-key
```

## How to Set in Render

1. Go to: https://dashboard.render.com
2. Click your **Web Service**
3. Go to **Environment** tab
4. Click **Add Environment Variable**
5. Enter **Key** and **Value**
6. Click **Save Changes**
7. Service will auto-redeploy

## Generate JWT Secret Key

### Option 1: Online
- Visit: https://randomkeygen.com/
- Use "CodeIgniter Encryption Keys" (64 chars)

### Option 2: Command Line
```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

### Option 3: Python
```python
import secrets
print(secrets.token_urlsafe(32))
```

---

**Set these before deploying!**

