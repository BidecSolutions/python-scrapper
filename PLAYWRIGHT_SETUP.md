# Playwright Setup for LinkedIn Scraping

This project uses Playwright for browser automation to scrape LinkedIn profiles more reliably than DOM scraping.

## Installation

### 1. Install Playwright Python Package

```bash
pip install playwright>=1.40.0
```

Or if using requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

After installing the Python package, you need to install the browser binaries:

```bash
playwright install chromium
```

This will download the Chromium browser that Playwright uses for automation.

### 3. Verify Installation

You can test if Playwright is working by running:

```python
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://example.com')
        print(await page.title())
        await browser.close()

import asyncio
asyncio.run(test())
```

## Usage

### API Endpoints

The Playwright scraper is available through these endpoints:

1. **Single Profile Scraping**
   ```
   POST /api/leads/linkedin-scrape
   ```
   Body:
   ```json
   {
     "linkedin_url": "https://www.linkedin.com/in/username/",
     "auto_find_email": true,
     "skip_smtp": false,
     "headless": true
   }
   ```

2. **Batch Profile Scraping**
   ```
   POST /api/leads/linkedin-scrape-batch
   ```
   Body:
   ```json
   {
     "linkedin_urls": [
       "https://www.linkedin.com/in/user1/",
       "https://www.linkedin.com/in/user2/"
     ],
     "auto_find_email": true,
     "headless": true
   }
   ```

### Chrome Extension

The Chrome extension now includes an option to use Playwright scraping:

1. Open the LeadFlux scraper panel on LinkedIn
2. Check the "Use Playwright (Browser Automation)" checkbox
3. Select profiles and click "Scrape Selected Profiles"

The extension will call the `/api/leads/linkedin-scrape` endpoint for each profile.

## How It Works

1. **Browser Automation**: Playwright launches a headless Chromium browser
2. **Page Navigation**: Navigates to the LinkedIn profile URL
3. **Wait for JS**: Waits for JavaScript to load and render content
4. **Data Extraction**: Uses CSS selectors to extract profile data
5. **Lead Creation**: Automatically creates/updates leads in the database

## Advantages Over DOM Scraping

- ✅ More reliable for JavaScript-heavy pages
- ✅ Works with content that only appears after JS execution
- ✅ Can handle dynamic content loading
- ✅ Better at avoiding detection (uses realistic browser settings)
- ✅ Can scroll, click, and navigate like a real user

## Configuration

### Headless Mode

By default, Playwright runs in headless mode (no visible browser window). You can disable this by setting `headless: false` in the API request.

### Timeout Settings

Default timeout is 30 seconds. You can adjust this in `app/services/linkedin_playwright_scraper.py`:

```python
scraper = LinkedInPlaywrightScraper(headless=True, timeout=60000)  # 60 seconds
```

### Rate Limiting

The scraper includes automatic delays between requests (2 seconds by default) to avoid rate limiting. You can adjust this in the `scrape_multiple_profiles` method.

## Troubleshooting

### "Playwright scraper not available" Error

This means Playwright is not installed. Run:
```bash
pip install playwright
playwright install chromium
```

### Browser Installation Issues

If `playwright install` fails:
- Check your internet connection
- Try running with admin/sudo privileges
- On Linux, you may need additional dependencies:
  ```bash
  sudo apt-get install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
  ```

### Timeout Errors

If profiles are timing out:
- Increase the timeout value
- Check if LinkedIn is blocking requests
- Try running in non-headless mode to see what's happening

## Security Notes

- Playwright runs server-side, so it doesn't expose your LinkedIn session
- The scraper uses realistic browser settings to avoid detection
- Rate limiting is built-in to avoid overwhelming LinkedIn's servers
- Always respect LinkedIn's Terms of Service and rate limits

