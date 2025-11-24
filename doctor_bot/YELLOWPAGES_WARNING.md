# ⚠️ CRITICAL WARNING: YellowPages Scraping

## YellowPages Explicitly Forbids Scraping

**DO NOT attempt to scrape YellowPages, even with advanced techniques.**

### Why YellowPages Blocks Scraping

1. **Terms of Service**
   - YellowPages Terms of Service explicitly prohibit automated access
   - Violating ToS can result in legal action
   - They actively enforce these terms

2. **Technical Blocks**
   - Active anti-bot detection
   - 403 Forbidden errors
   - IP blocking
   - CAPTCHA challenges

3. **Legal Consequences**
   - Terms of Service violations
   - Potential legal action
   - IP bans
   - Account suspensions (if applicable)

### What Happens When You Try

```
❌ 403 Forbidden Error
❌ Access Denied
❌ IP Blocked
❌ Legal Risk
```

**Even with:**
- Headless browsers
- Proxy rotation
- Anti-detection techniques
- Human-like behavior

**YellowPages will still block you because they explicitly forbid it.**

---

## ✅ Legal Alternatives

### 1. Google Places API (Recommended)

**Best alternative for business/doctor listings:**

```bash
cd doctor_bot
python google_places_scraper.py
```

**Benefits:**
- ✅ Legal and official
- ✅ No 403 errors
- ✅ Reliable and stable
- ✅ Free tier: $200/month credit
- ✅ Better data quality

**Get API Key:**
1. Go to https://console.cloud.google.com/
2. Create project
3. Enable "Places API"
4. Create API key

### 2. BetterDoctor API

For medical professionals specifically:
- Official API for doctors
- Comprehensive data
- Legal access

### 3. Contact YellowPages Directly

For business use:
- Request official data access
- Negotiate data partnership
- Get written permission

### 4. Build Your Own Directory

- Use Google Places API to seed data
- Allow doctors to claim listings
- Build community-driven directory

---

## Code Example: What NOT to Do

```python
# ❌ DON'T DO THIS - It violates YellowPages ToS
driver.get('https://www.yellowpages.com/')
search_box = driver.find_element(By.NAME, 'search_terms')
search_box.send_keys('orthopedic doctor')
# This will result in 403 error and legal risk
```

## Code Example: What TO Do Instead

```python
# ✅ DO THIS - Legal Google Places API
from google_places_scraper import GooglePlacesDoctorScraper

scraper = GooglePlacesDoctorScraper(api_key="YOUR_KEY")
results = scraper.search_doctors(
    specialty="orthopedic doctor",
    location="New York, NY"
)
# This works legally and reliably
```

---

## Comparison

| Aspect | Scraping YellowPages | Google Places API |
|--------|---------------------|-------------------|
| **Legal** | ❌ Violates ToS | ✅ Official API |
| **Works?** | ❌ 403 errors | ✅ Always works |
| **Reliable** | ❌ Breaks often | ✅ Stable |
| **Data Quality** | ⚠️ Varies | ✅ High |
| **Legal Risk** | ⚠️ High | ✅ None |
| **Cost** | Free (but illegal) | Free tier available |

---

## Educational Code

If you want to see how Selenium scraping works (for educational purposes on sites that allow it), see:
- `educational_example.py` - Shows structure but won't work on YellowPages
- `generic_doctor_bot.py` - Generic scraper for sites that allow it
- `advanced_scraper.py` - Advanced techniques (for legal sites only)

**But remember:** None of these will work on YellowPages, and attempting to use them violates their Terms of Service.

---

## Summary

**Don't scrape YellowPages. Use Google Places API instead.**

1. ✅ Get Google Places API key (free tier available)
2. ✅ Use `google_places_scraper.py`
3. ✅ Get legal, reliable doctor data
4. ✅ No legal risk
5. ✅ Better results

**See `LEGAL_ALTERNATIVES.md` for complete guide.**

