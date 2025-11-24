# Legal Alternatives to Scraping YellowPages

## ⚠️ YellowPages Does NOT Allow Scraping

**YellowPages explicitly forbids automated scraping in their Terms of Service.**

- Their `robots.txt` blocks most automated access
- Their Terms of Service prohibit scraping
- They have active anti-bot measures (403 errors)
- Violating their ToS can result in legal action

**DO NOT attempt to scrape YellowPages, even with advanced techniques.**

---

## ✅ Legitimate Alternatives

### 1. Google Places API (Recommended)

**Best option for business/doctor listings:**

```python
# Install: pip install googlemaps
import googlemaps

gmaps = googlemaps.Client(key='YOUR_API_KEY')

# Search for orthopedic doctors
places = gmaps.places_nearby(
    location=(40.7128, -74.0060),  # NYC coordinates
    radius=5000,
    type='doctor',
    keyword='orthopedic'
)

for place in places['results']:
    print(f"Name: {place['name']}")
    print(f"Address: {place.get('vicinity', 'N/A')}")
    print(f"Rating: {place.get('rating', 'N/A')}")
```

**Benefits:**
- ✅ Legal and official
- ✅ High-quality data
- ✅ Regular updates
- ✅ No anti-bot issues
- ✅ Free tier available

**Pricing:** Free tier: $200 credit/month (covers ~40,000 requests)

---

### 2. BetterDoctor API

**Medical professional directory:**

```python
import requests

api_key = "YOUR_API_KEY"
url = "https://api.betterdoctor.com/v1/doctors"

params = {
    "specialty_uid": "orthopedic-surgeon",
    "location": "37.773,-122.413,100",
    "user_key": api_key
}

response = requests.get(url, params=params)
doctors = response.json()['data']

for doctor in doctors:
    print(f"Name: {doctor['profile']['first_name']} {doctor['profile']['last_name']}")
    print(f"Specialty: {doctor['specialties'][0]['name']}")
```

**Benefits:**
- ✅ Designed for medical professionals
- ✅ Comprehensive data
- ✅ Legal API access

**Pricing:** Free tier available, paid plans for more data

---

### 3. Healthgrades API (Unofficial)

**Note:** Healthgrades doesn't have an official public API, but they may offer data partnerships for businesses.

**Contact them directly for:**
- Business partnerships
- Data licensing
- API access agreements

---

### 4. WebMD Provider Directory

**For medical professionals:**

- Some data available through partnerships
- Contact WebMD for business access
- May have API for healthcare organizations

---

### 5. Build Your Own Directory

**Create your own database:**

1. **Manual Collection**
   - Use Google Places API to seed data
   - Allow doctors to claim/update listings
   - Build community-driven directory

2. **Public Health Data**
   - State medical board databases (often public)
   - Hospital directories (many are public)
   - Insurance provider directories

3. **Data Partnerships**
   - Partner with medical associations
   - License data from legitimate providers
   - Aggregate from multiple legal sources

---

## Implementation: Google Places API Integration

Here's a complete example using Google Places API:

```python
# google_places_scraper.py
import googlemaps
import csv
from datetime import datetime

class GooglePlacesDoctorScraper:
    """Legal alternative to scraping YellowPages"""
    
    def __init__(self, api_key):
        self.client = googlemaps.Client(key=api_key)
    
    def search_doctors(self, specialty, location, radius=5000):
        """
        Search for doctors using Google Places API
        
        Args:
            specialty: e.g., "orthopedic doctor"
            location: (lat, lng) tuple or address string
            radius: Search radius in meters
        """
        # Search nearby
        places = self.client.places_nearby(
            location=location,
            radius=radius,
            type='doctor',
            keyword=specialty
        )
        
        results = []
        for place in places.get('results', []):
            # Get detailed info
            details = self.client.place(
                place_id=place['place_id'],
                fields=['name', 'formatted_address', 'formatted_phone_number', 
                       'website', 'rating', 'opening_hours', 'types']
            )
            
            result = {
                'name': details['result'].get('name'),
                'address': details['result'].get('formatted_address'),
                'phone': details['result'].get('formatted_phone_number'),
                'website': details['result'].get('website'),
                'rating': details['result'].get('rating'),
                'specialty': specialty,
                'source': 'google_places',
                'timestamp': datetime.utcnow().isoformat()
            }
            results.append(result)
        
        return results
    
    def save_to_csv(self, results, filename='doctors_google_places.csv'):
        """Save results to CSV"""
        if not results:
            return
        
        fieldnames = sorted(results[0].keys())
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"✅ Saved {len(results)} results to {filename}")


# Usage
if __name__ == "__main__":
    API_KEY = "YOUR_GOOGLE_PLACES_API_KEY"
    scraper = GooglePlacesDoctorScraper(API_KEY)
    
    # Search for orthopedic doctors in NYC
    results = scraper.search_doctors(
        specialty="orthopedic doctor",
        location="40.7128,-74.0060",  # NYC
        radius=10000  # 10km
    )
    
    print(f"Found {len(results)} doctors")
    scraper.save_to_csv(results)
```

---

## Comparison: Scraping vs. APIs

| Aspect | Scraping YellowPages | Google Places API |
|--------|---------------------|-------------------|
| **Legal** | ❌ Violates ToS | ✅ Official API |
| **Reliability** | ❌ 403 errors, blocks | ✅ Stable |
| **Data Quality** | ⚠️ Varies | ✅ High quality |
| **Maintenance** | ❌ Breaks often | ✅ Stable |
| **Cost** | Free (but illegal) | Free tier available |
| **Rate Limits** | ❌ IP bans | ✅ Clear limits |
| **Legal Risk** | ⚠️ High | ✅ None |

---

## Getting Started with Google Places API

1. **Get API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable "Places API"
   - Create API key
   - Set usage limits

2. **Install Library:**
   ```bash
   pip install googlemaps
   ```

3. **Use the Code:**
   - See `google_places_scraper.py` example above
   - Replace `YOUR_API_KEY` with your key
   - Start searching!

---

## Other Legal Data Sources

### State Medical Boards
Many state medical boards have public directories:
- California Medical Board
- New York State Department of Health
- Texas Medical Board
- etc.

These are often available as:
- Public databases
- CSV downloads
- Searchable websites (with proper API access)

### Hospital Directories
Many hospitals have public directories:
- Often allow proper API access
- Contact hospital IT departments
- May have partnerships available

### Insurance Provider Directories
Insurance companies often have provider directories:
- Some offer API access
- May require partnership agreements
- Often more comprehensive than YellowPages

---

## Summary

**Don't scrape YellowPages.** Instead:

1. ✅ Use **Google Places API** (best option)
2. ✅ Use **BetterDoctor API** (for medical professionals)
3. ✅ Contact **YellowPages** for official data access
4. ✅ Build your own directory from legal sources
5. ✅ Partner with medical associations

**Remember:** Legal data access is:
- More reliable
- Higher quality
- No legal risk
- Better long-term solution

