# Legal Sites for Testing Scrapers

⚠️ **IMPORTANT**: Always verify current Terms of Service and robots.txt before scraping any site. This list is for reference only and may become outdated.

## Sites That Generally Allow Scraping

### Public Data Directories

1. **OpenStreetMap Nominatim** (Geocoding)
   - URL: `https://nominatim.openstreetmap.org/`
   - Status: ✅ Allows automated access with rate limits
   - robots.txt: Permits scraping with respectful rate limits
   - Use case: Geocoding addresses

2. **Wikipedia** (Content)
   - URL: `https://www.wikipedia.org/`
   - Status: ✅ Allows scraping (check robots.txt for specific pages)
   - robots.txt: Generally permissive
   - Use case: Extracting structured data from articles

3. **Common Crawl** (Web Archive)
   - URL: `https://commoncrawl.org/`
   - Status: ✅ Explicitly allows scraping
   - Use case: Large-scale web data

### Your Own Sites

4. **Your Own Website**
   - Status: ✅ Always legal to scrape your own site
   - Use case: Testing, data extraction from your own content

5. **Test/Demo Sites**
   - Status: ✅ Safe for testing
   - Examples:
     - `http://quotes.toscrape.com/` - Simple scraping practice
     - `https://scrapethissite.com/` - Designed for scraping practice

## Sites That DO NOT Allow Scraping

❌ **DO NOT SCRAPE THESE** (explicitly forbidden):

- **YellowPages** ⚠️ **STRICTLY FORBIDDEN** - Active anti-bot measures, 403 errors, violates ToS
- LinkedIn
- Facebook
- Instagram
- Twitter/X
- Google (except via official APIs)
- Most social media platforms
- Most business directories (unless explicitly stated otherwise)

### YellowPages Specifically

**YellowPages explicitly forbids scraping:**
- Their Terms of Service prohibit automated access
- Their robots.txt blocks bots
- They have active anti-bot detection (403 errors)
- Violating their ToS can result in legal action

**✅ Use Google Places API instead** - See `LEGAL_ALTERNATIVES.md` and `google_places_scraper.py`

## How to Check if a Site Allows Scraping

### 1. Check robots.txt

Visit: `https://example.com/robots.txt`

Look for:
```
User-agent: *
Disallow: /          # ❌ Blocks all scraping
Allow: /             # ✅ Allows scraping
```

### 2. Check Terms of Service

Look for sections about:
- "Automated access"
- "Scraping"
- "Data mining"
- "Bots"

### 3. Check for Public APIs

Many sites prefer you use their API instead:
- Google Places API
- Yelp Fusion API
- Facebook Graph API
- LinkedIn API

## Safe Testing Approach

1. **Start with your own site** or a test site
2. **Use mock data** (see `test_with_mock.py`)
3. **Test selectors** before running on real sites
4. **Respect rate limits** even on allowed sites
5. **Check regularly** - Terms of Service can change

## Example: Testing with Quotes Site

```python
# Safe test site for practice
site_config = {
    "url": "http://quotes.toscrape.com/",
    "result_item_selector": ".quote",
    "fields": {
        "text": ".text",
        "author": ".author",
        "tags": ".tag"
    }
}
```

## Legal Alternatives

Instead of scraping, consider:

1. **Official APIs** - Most sites provide these
2. **Data partnerships** - Contact site owners
3. **Public datasets** - Use existing open data
4. **Your own data** - Build your own directory

## Disclaimer

This list is provided for informational purposes only. Always verify current Terms of Service and robots.txt before scraping any website. Laws and terms can change. You are responsible for compliance with all applicable laws and terms of service.

