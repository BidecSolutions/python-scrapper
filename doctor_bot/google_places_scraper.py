"""Legal alternative to scraping YellowPages - Uses Google Places API"""
import googlemaps
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class GooglePlacesDoctorScraper:
    """
    Legal alternative to scraping YellowPages.
    Uses Google Places API for doctor/business listings.
    
    ⚠️ Requires Google Places API key (free tier available)
    Get one at: https://console.cloud.google.com/
    """
    
    def __init__(self, api_key: str):
        """
        Initialize scraper with Google Places API key
        
        Args:
            api_key: Your Google Places API key
        """
        if not api_key or api_key == "YOUR_API_KEY":
            raise ValueError(
                "Google Places API key required. "
                "Get one at: https://console.cloud.google.com/"
            )
        self.client = googlemaps.Client(key=api_key)
    
    def search_doctors(
        self,
        specialty: str,
        location: str | Tuple[float, float],
        radius: int = 5000,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for doctors using Google Places API
        
        Args:
            specialty: Search term (e.g., "orthopedic doctor", "cardiologist")
            location: Address string or (lat, lng) tuple
            radius: Search radius in meters (default: 5000 = 5km)
            max_results: Maximum number of results (None = all)
        
        Returns:
            List of doctor records with name, address, phone, etc.
        """
        print(f"🔍 Searching for '{specialty}' near {location}...")
        
        # Search nearby places
        try:
            places = self.client.places_nearby(
                location=location,
                radius=radius,
                type='doctor',
                keyword=specialty
            )
        except Exception as e:
            raise RuntimeError(f"Google Places API error: {e}")
        
        results = []
        place_results = places.get('results', [])
        
        if max_results:
            place_results = place_results[:max_results]
        
        print(f"📋 Found {len(place_results)} places, fetching details...")
        
        for i, place in enumerate(place_results, 1):
            try:
                # Get detailed information
                details = self.client.place(
                    place_id=place['place_id'],
                    fields=[
                        'name',
                        'formatted_address',
                        'formatted_phone_number',
                        'website',
                        'rating',
                        'opening_hours',
                        'types',
                        'geometry'
                    ]
                )
                
                place_data = details.get('result', {})
                
                result = {
                    'name': place_data.get('name'),
                    'address': place_data.get('formatted_address'),
                    'phone': place_data.get('formatted_phone_number'),
                    'website': place_data.get('website'),
                    'rating': place_data.get('rating'),
                    'specialty': specialty,
                    'types': ', '.join(place_data.get('types', [])),
                    'source': 'google_places',
                    'place_id': place['place_id'],
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Add coordinates if available
                if 'geometry' in place_data:
                    loc = place_data['geometry'].get('location', {})
                    result['latitude'] = loc.get('lat')
                    result['longitude'] = loc.get('lng')
                
                results.append(result)
                print(f"   {i}. {result['name']}")
                
                # Rate limiting - be respectful
                if i % 10 == 0:
                    import time
                    time.sleep(1)  # Small delay every 10 requests
                    
            except Exception as e:
                print(f"   ⚠️  Error fetching details for place {i}: {e}")
                continue
        
        print(f"✅ Extracted {len(results)} doctor records")
        return results
    
    def search_by_address(
        self,
        specialty: str,
        address: str,
        radius: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Search for doctors near an address
        
        Args:
            specialty: Search term
            address: Address string (e.g., "New York, NY")
            radius: Search radius in meters
        """
        # Geocode address first
        try:
            geocode_result = self.client.geocode(address)
            if not geocode_result:
                raise ValueError(f"Could not geocode address: {address}")
            
            location = geocode_result[0]['geometry']['location']
            lat_lng = (location['lat'], location['lng'])
            
            return self.search_doctors(specialty, lat_lng, radius)
        except Exception as e:
            raise RuntimeError(f"Geocoding error: {e}")
    
    def save_to_csv(
        self,
        results: List[Dict[str, Any]],
        filename: str = 'doctors_google_places.csv'
    ):
        """Save results to CSV file"""
        if not results:
            print("⚠️  No results to save.")
            return
        
        fieldnames = sorted(results[0].keys())
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a' if file_exists else 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerows(results)
        
        print(f"💾 Saved {len(results)} results to {filename}")


def main():
    """Interactive CLI for Google Places doctor search"""
    print("=" * 70)
    print("=== Google Places Doctor Scraper (Legal Alternative) ===")
    print("=" * 70)
    print("\n✅ This uses the official Google Places API")
    print("✅ Legal, reliable, and high-quality data")
    print("✅ Free tier: $200 credit/month (~40,000 requests)\n")
    
    # Get API key
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        api_key = input("Enter your Google Places API key (or set GOOGLE_PLACES_API_KEY env var): ").strip()
    
    if not api_key or api_key == "YOUR_API_KEY":
        print("\n❌ API key required!")
        print("Get one at: https://console.cloud.google.com/")
        print("1. Create project")
        print("2. Enable 'Places API'")
        print("3. Create API key")
        return
    
    try:
        scraper = GooglePlacesDoctorScraper(api_key)
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    while True:
        print("\n" + "-" * 70)
        specialty = input("Enter specialty (e.g., 'orthopedic doctor', or 'q' to quit): ").strip()
        
        if not specialty or specialty.lower() == 'q':
            print("👋 Goodbye!")
            break
        
        location = input("Enter location (address or 'lat,lng', e.g., 'New York, NY'): ").strip()
        if not location:
            print("⚠️  Location required")
            continue
        
        try:
            radius = int(input("Enter search radius in meters (default 5000): ").strip() or "5000")
        except ValueError:
            radius = 5000
        
        try:
            # Try as coordinates first
            if ',' in location and location.replace(',', '').replace('.', '').replace('-', '').replace(' ', '').isdigit():
                lat, lng = map(float, location.split(','))
                results = scraper.search_doctors(specialty, (lat, lng), radius)
            else:
                # Treat as address
                results = scraper.search_by_address(specialty, location, radius)
            
            if results:
                print(f"\n📊 Results Summary:")
                print(f"   Total: {len(results)} doctors")
                print(f"   With phone: {sum(1 for r in results if r.get('phone'))}")
                print(f"   With website: {sum(1 for r in results if r.get('website'))}")
                print(f"   Average rating: {sum(r.get('rating', 0) or 0 for r in results) / len(results):.1f}")
                
                scraper.save_to_csv(results)
            else:
                print("⚠️  No results found. Try:")
                print("   - Different search terms")
                print("   - Larger radius")
                print("   - Different location")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\n💡 Troubleshooting:")
            print("   - Check API key is valid")
            print("   - Verify Places API is enabled")
            print("   - Check API quota/billing")
            print("   - Ensure location format is correct")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted. Goodbye!")

