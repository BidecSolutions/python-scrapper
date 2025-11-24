# Quick Start Guide

Get up and running with the Lead Scraper in 5 minutes!

## Prerequisites

- Python 3.9+
- PostgreSQL (optional, for database features)
- API keys (Google Places API and/or Bing Search API)

## Installation

1. **Clone and navigate to the project:**
```bash
cd "F:\Web Scraping"
```

2. **Create a virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On Linux/Mac
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
# Copy the example .env file
copy .env.example .env  # On Windows
# or
cp .env.example .env  # On Linux/Mac

# Edit .env and add your API keys:
# - GOOGLE_PLACES_API_KEY (optional, for Google Places source)
# - GOOGLE_SEARCH_API_KEY + GOOGLE_SEARCH_CX (recommended, for Google Custom Search)
# - BING_SEARCH_API_KEY (optional, for Bing web search)
```

## Get API Keys

### Google Custom Search API (Recommended)

1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Create a new search engine (or use existing one)
3. Note your **Search Engine ID (CX)** - it looks like `e67e705775eee4075`
4. Go to [Google Cloud Console](https://console.cloud.google.com/)
5. Enable the **"Custom Search JSON API"** in APIs & Services → Library
6. Create credentials (API Key) in APIs & Services → Credentials
7. Copy both to your `.env` file:
   ```
   GOOGLE_SEARCH_API_KEY=your_api_key_here
   GOOGLE_SEARCH_CX=your_search_engine_id_here
   ```

### Google Places API Key (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Places API"
4. Create credentials (API Key)
5. Copy the key to your `.env` file

### Bing Search API Key (Optional)

1. Go to [Azure Portal](https://portal.azure.com/)
2. Create a "Bing Search v7" resource
3. Get your subscription key
4. Copy it to your `.env` file

## Usage

### CLI Usage (Simplest)

```bash
# Basic scraping
python -m app.main --niche "dentist clinic" --location "Karachi" --out leads.csv

# With more options
python -m app.main \
  --niche "doctor clinic" \
  --location "London" \
  --out results.json \
  --format json \
  --max-results 50 \
  --max-pages 10
```

### API Usage

1. **Start the API server:**
```bash
uvicorn app.api.server:app --reload --port 8000
```

2. **Open the interactive docs:**
   - Navigate to http://localhost:8000/docs
   - Try the `/api/scrape-async` endpoint

3. **Or use curl:**
```bash
curl -X POST "http://localhost:8000/api/scrape-async" \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "dentist clinic",
    "location": "Karachi",
    "max_results": 20,
    "max_pages_per_site": 5
  }'
```

### Database Setup (Optional)

If you want to use the database features:

1. **Create a PostgreSQL database:**
```bash
createdb lead_scraper
```

2. **Update your `.env` file:**
```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/lead_scraper
```

3. **Set up Alembic migrations:**
```bash
# Copy example files
copy alembic.ini.example alembic.ini
copy alembic\env.py.example alembic\env.py

# Edit alembic.ini and set sqlalchemy.url

# Initialize (if not already done)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

4. **Use the job-based endpoint:**
```bash
# The /api/jobs/run-once endpoint saves results to the database
curl -X POST "http://localhost:8000/api/jobs/run-once" \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "dentist clinic",
    "location": "Karachi",
    "max_results": 20,
    "max_pages_per_site": 5
  }'
```

## Example Output

The CSV/JSON output will contain:
- Business name
- Website URL
- Email addresses (extracted from website)
- Phone numbers (extracted from website)
- Address
- Source (google_places, web_search, etc.)
- City and country

## Troubleshooting

### "No API key" errors
- Make sure your `.env` file is in the project root
- Verify the API key names match exactly (case-sensitive)
- Restart your terminal/IDE after creating `.env`

### "Module not found" errors
- Make sure you activated your virtual environment
- Run `pip install -r requirements.txt` again

### Database connection errors
- Verify PostgreSQL is running
- Check your `DATABASE_URL` in `.env`
- Ensure the database exists

### No results found
- Try a different niche/location combination
- Check if your API keys have the right permissions
- Verify you're within API rate limits

## Next Steps

- Read the full [README.md](README.md) for advanced features
- Explore the API docs at http://localhost:8000/docs
- Customize sources in `app/sources/`
- Add new export formats in `app/services/export_service.py`

## Need Help?

- Check the README.md for detailed documentation
- Review the code comments for implementation details
- Test individual components using the test files

