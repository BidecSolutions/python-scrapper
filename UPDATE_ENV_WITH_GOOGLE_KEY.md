# Quick Update: Add Google Search API Key

## Your API Key
```
AIzaSyAY6YoEnC96FDlOH50NV-1jpyLb5HpndAE
```

## Add to .env File

Open `python-scrapper/.env` and add:

```env
GOOGLE_SEARCH_API_KEY=AIzaSyAY6YoEnC96FDlOH50NV-1jpyLb5HpndAE
```

## ⚠️ Important: You Also Need CX

Google Custom Search requires a **Custom Search Engine ID (CX)**.

### Get Your CX:

1. Go to: https://programmablesearchengine.google.com/controlpanel/create
2. Create a new search engine:
   - Sites to search: `*` (to search entire web)
   - Name: Any name you like
3. After creating, copy the **Search engine ID**
4. Add to `.env`:
   ```env
   GOOGLE_SEARCH_CX=your_cx_id_here
   ```

## After Updating .env

Restart your backend:
```bash
# Stop backend (Ctrl+C)
cd python-scrapper
python main.py
```

Then try creating a job again - it should work with Google Search!

