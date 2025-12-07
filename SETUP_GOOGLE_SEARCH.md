# Setup Google Custom Search API

## Your API Key
```
AIzaSyAY6YoEnC96FDlOH50NV-1jpyLb5HpndAE
```

## Required Configuration

Google Custom Search API requires **TWO** things:
1. ✅ **API Key** (you have this)
2. ❌ **Custom Search Engine ID (CX)** - You need to create this

## Step 1: Add API Key to .env

Add this to your `python-scrapper/.env` file:

```env
GOOGLE_SEARCH_API_KEY=AIzaSyAY6YoEnC96FDlOH50NV-1jpyLb5HpndAE
```

## Step 2: Create Custom Search Engine (CX)

### Option A: Create New Custom Search Engine

1. Go to: https://programmablesearchengine.google.com/controlpanel/create
2. Click **"Add"** or **"Create a custom search engine"**
3. Fill in:
   - **Sites to search**: Enter `*` (asterisk) to search the entire web
   - **Name**: "Lead Scraper Search" (or any name)
   - **Language**: Your preferred language
4. Click **"Create"**
5. Click **"Control Panel"** (or go to: https://programmablesearchengine.google.com/controlpanel/all)
6. Click on your search engine
7. Copy the **"Search engine ID"** (this is your CX)
8. Add it to your `.env` file:
   ```env
   GOOGLE_SEARCH_CX=your_cx_id_here
   ```

### Option B: Use Existing CX (if you have one)

If you already have a Custom Search Engine, just add its ID to `.env`:
```env
GOOGLE_SEARCH_CX=your_existing_cx_id
```

## Step 3: Update .env File

Your `.env` file should now have:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres.aashvhvwiayvniidvaqk:Newpass%402025%40@aws-1-ap-northeast-2.pooler.supabase.com:6543/Lead_scrapper

# JWT Secret Key
JWT_SECRET_KEY=your-secret-key-change-in-production-min-32-chars-please-use-a-secure-random-string

# Google Custom Search API
GOOGLE_SEARCH_API_KEY=AIzaSyAY6YoEnC96FDlOH50NV-1jpyLb5HpndAE
GOOGLE_SEARCH_CX=your_cx_id_here

# Optional: Other API Keys
# GOOGLE_PLACES_API_KEY=your_key_here
# BING_SEARCH_API_KEY=your_key_here
```

## Step 4: Restart Backend

After updating `.env`, restart your backend:

```bash
# Stop backend (Ctrl+C)
cd python-scrapper
python main.py
```

## Verify It Works

1. Create a new job in the frontend
2. Check backend logs - you should see:
   ```
   INFO: Google Custom Search source initialized successfully
   ```
3. Job should now find leads using Google Search!

## API Limits

- **Free Tier**: 100 searches per day
- **Paid Tier**: More searches available

## Troubleshooting

### Error: "GOOGLE_SEARCH_CX is required"
- Make sure you added `GOOGLE_SEARCH_CX` to your `.env` file
- Restart the backend after adding it

### Error: "API key not valid"
- Check that the API key is correct
- Make sure Custom Search API is enabled in Google Cloud Console

### No results found
- Check that your Custom Search Engine is set to search the entire web (`*`)
- Verify the API key has proper permissions

