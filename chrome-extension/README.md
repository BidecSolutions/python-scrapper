# LeadFlux Email Finder - Chrome Extension

Chrome extension for finding and verifying email addresses from LinkedIn profiles.

## Google Maps Capture (New)

This extension can also capture Google Maps search results **as you scroll** (user-driven).

1. Open `https://www.google.com/maps`
2. Search for your niche + location
3. Open the extension popup → **Google Maps Capture**
4. Click **Start**
5. Scroll the results list to load more items
6. Click **Download CSV** or **Download JSON**

To import the JSON into the backend database, use `POST /api/google-maps/import`.

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder
5. The extension icon should appear in your toolbar

## Usage

1. Navigate to any LinkedIn profile page
2. The extension will automatically detect the profile
3. Click "Find Email" button that appears on the profile
4. The extension will:
   - Extract name and company from the profile
   - Call the LeadFlux API to find the email
   - Display the result with confidence score
5. Click "Save to Leads" to save the email to your LeadFlux account

## Configuration

1. Click the extension icon in the toolbar
2. Enter your LeadFlux API URL (default: `http://localhost:8002`)
3. Click "Save Settings"

## Features

- ✅ Automatic profile detection
- ✅ Name and company extraction
- ✅ Email pattern matching
- ✅ SMTP verification
- ✅ Save to leads directly
- ✅ Confidence scoring

## Development

To modify the extension:

1. Edit files in `chrome-extension/`
2. Go to `chrome://extensions/`
3. Click the refresh icon on the extension card
4. Reload the LinkedIn page

## API Requirements

The extension requires the LeadFlux API to be running with these endpoints:

- `POST /api/email-finder` - Find email from name + domain
- `POST /api/email-finder/save-to-leads` - Save email to leads
- `POST /api/google-maps/import` - Import captured Maps results (optional)

## Notes

- The extension only works on LinkedIn profile pages
- Make sure your API URL is accessible from the browser
- For production, update `API_URL` in `content.js` or use the popup settings

