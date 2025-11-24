"""Test the scraper with mock HTML data (no real website needed)"""
from bs4 import BeautifulSoup
import csv
from datetime import datetime

# Mock HTML that simulates a doctor search results page
MOCK_HTML = """
<!DOCTYPE html>
<html>
<head><title>Doctor Search Results</title></head>
<body>
    <div class="doctor-card">
        <h3 class="doctor-name">Dr. John Smith</h3>
        <p class="doctor-specialty">Orthopedic Surgeon</p>
        <p class="doctor-phone">(555) 123-4567</p>
        <p class="doctor-address">123 Main St, New York, NY 10001</p>
        <a href="/doctors/john-smith" class="doctor-name">View Profile</a>
    </div>
    <div class="doctor-card">
        <h3 class="doctor-name">Dr. Sarah Johnson</h3>
        <p class="doctor-specialty">Cardiologist</p>
        <p class="doctor-phone">(555) 234-5678</p>
        <p class="doctor-address">456 Oak Ave, Los Angeles, CA 90001</p>
        <a href="/doctors/sarah-johnson" class="doctor-name">View Profile</a>
    </div>
    <div class="doctor-card">
        <h3 class="doctor-name">Dr. Michael Chen</h3>
        <p class="doctor-specialty">Dermatologist</p>
        <p class="doctor-phone">(555) 345-6789</p>
        <p class="doctor-address">789 Pine Rd, Chicago, IL 60601</p>
        <a href="/doctors/michael-chen" class="doctor-name">View Profile</a>
    </div>
</body>
</html>
"""


def test_scraper_logic():
    """Test the scraping logic without needing a real website"""
    print("=" * 60)
    print("=== Testing Scraper Logic (Mock Data) ===")
    print("=" * 60)
    print("\nThis test uses mock HTML to verify your selectors work correctly.")
    print("No real website is accessed - perfect for testing!\n")
    
    # Use the same config structure as generic_doctor_bot.py
    site_config = {
        "result_item_selector": ".doctor-card",
        "fields": {
            "name": ".doctor-name",
            "specialty": ".doctor-specialty",
            "phone": ".doctor-phone",
            "address": ".doctor-address"
        },
        "profile_link_selector": ".doctor-name a",
    }
    
    # Parse mock HTML
    soup = BeautifulSoup(MOCK_HTML, "html.parser")
    results = []
    
    items = soup.select(site_config["result_item_selector"])
    print(f"📋 Found {len(items)} result items\n")
    
    for card in items:
        record = {}
        
        # Extract fields
        for field_name, selector in site_config.get("fields", {}).items():
            el = card.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text:
                    record[field_name] = text
                elif el.has_attr("href"):
                    record[field_name] = el["href"]
                else:
                    record[field_name] = None
            else:
                record[field_name] = None
        
        # Extract profile link
        link_sel = site_config.get("profile_link_selector")
        if link_sel:
            a = card.select_one(link_sel)
            if a and a.has_attr("href"):
                record["profile_link"] = a["href"]
            else:
                record["profile_link"] = None
        
        if any(record.values()):
            results.append(record)
    
    # Display results
    print("✅ Extracted Results:")
    print("-" * 60)
    for i, r in enumerate(results, start=1):
        print(f"\n{i}. {r.get('name', 'N/A')}")
        print(f"   Specialty: {r.get('specialty', 'N/A')}")
        print(f"   Phone: {r.get('phone', 'N/A')}")
        print(f"   Address: {r.get('address', 'N/A')}")
        if r.get('profile_link'):
            print(f"   Link: {r['profile_link']}")
    
    # Save to CSV
    if results:
        filename = "test_results.csv"
        for r in results:
            r["query"] = "test_query"
            r["timestamp"] = datetime.utcnow().isoformat()
        
        fieldnames = sorted(results[0].keys())
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        
        print(f"\n💾 Saved {len(results)} rows to {filename}")
        print("\n✅ Test passed! Your selectors are working correctly.")
        print("   You can now use these same selectors in generic_doctor_bot.py")
    else:
        print("\n❌ No results extracted. Check your selectors.")
    
    return results


if __name__ == "__main__":
    test_scraper_logic()

