# Chrome Extension Setup Guide

## Quick Start

1. **Open Chrome Extensions Page**
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)

2. **Load the Extension**
   - Click "Load unpacked"
   - Select the `chrome-extension/` folder from this project
   - The extension icon should appear in your toolbar

3. **Configure API URL**
   - Click the extension icon
   - Enter your LeadFlux API URL (default: `http://localhost:8000`)
   - Click "Save Settings"

4. **Use on LinkedIn**
   - Navigate to any LinkedIn profile
   - You'll see a "LeadFlux" widget on the profile
   - Click "Find Email" to find the person's email
   - Click "Save to Leads" to save it to your account

## Features

- ✅ Automatic profile detection
- ✅ Name and company extraction
- ✅ Email pattern matching
- ✅ SMTP verification
- ✅ Save to leads directly
- ✅ Confidence scoring

## File Structure

```
chrome-extension/
├── manifest.json      # Extension configuration
├── content.js         # LinkedIn page integration
├── content.css        # Widget styling
├── popup.html         # Settings popup UI
├── popup.js           # Settings logic
├── background.js      # Service worker
└── README.md          # Extension documentation
```

## Customization

### Change API URL

Edit `content.js` line 9:
```javascript
const API_URL = 'https://your-api-url.com';
```

Or use the popup settings (recommended).

### Styling

Edit `content.css` to customize the widget appearance.

### LinkedIn Selectors

If LinkedIn changes their HTML structure, update selectors in `content.js`:
- `extractName()` - Name extraction
- `extractCompany()` - Company extraction

## Troubleshooting

**Extension not appearing on LinkedIn:**
- Make sure you're on a profile page (`/in/username`)
- Check browser console for errors (F12)
- Verify API URL is correct

**API calls failing:**
- Check CORS settings on your backend
- Verify API URL is accessible
- Check browser console for network errors

**Email not found:**
- Try enabling SMTP verification (slower but more accurate)
- Check that domain is correct
- Some domains may not accept SMTP checks

## Production Deployment

1. **Update API URL** in `content.js` to production URL
2. **Create icons** (16x16, 48x48, 128x128 PNG files)
3. **Package extension**:
   - Go to `chrome://extensions/`
   - Click "Pack extension"
   - Select `chrome-extension/` folder
4. **Submit to Chrome Web Store** (optional)

## Security Notes

- Extension only runs on LinkedIn pages
- API calls are made directly from browser
- No data is stored locally (except API URL setting)
- All verification happens server-side

