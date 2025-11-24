"""CLI script to scrape doctors and save to CSV"""
import csv
import os
import sys
from datetime import datetime
from scraper import scrape_doctors
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ⚠️ IMPORTANT: Replace this with a REAL site config that allows scraping!
# Always check robots.txt and Terms of Service before using!
SITE_CONFIG = {
    "url": "https://example-doctors.com",
    "search_box_selector": "input[name='search']",
    "submit_selector": "button.search-submit",
    "result_item_selector": ".doctor-card",
    "fields": {
        "name": ".doctor-name",
        "specialty": ".doctor-specialty",
        "phone": ".doctor-phone",
        "address": ".doctor-address"
    },
    "profile_link_selector": ".doctor-name a",
    "wait_seconds": 5
}

CSV_FILE = "doctors_data.csv"


def save_to_csv(results, query):
    """Save scraping results to CSV file"""
    if not results:
        print("No results to save.")
        return
    
    # Add query + timestamp fields
    for r in results:
        r["query"] = query
        r["timestamp"] = datetime.utcnow().isoformat()
    
    fieldnames = sorted(results[0].keys())
    file_exists = os.path.isfile(CSV_FILE)
    
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
            logger.info(f"Created new CSV file: {CSV_FILE}")
        
        for row in results:
            writer.writerow(row)
    
    print(f"✅ Saved {len(results)} rows to {CSV_FILE}")


def check_config():
    """Warn if using example config"""
    if "example" in SITE_CONFIG.get("url", "").lower():
        print("\n" + "="*60)
        print("⚠️  WARNING: You're using the example config!")
        print("="*60)
        print("Please update SITE_CONFIG in collect_data.py with:")
        print("  - A real website URL that allows scraping")
        print("  - Correct CSS selectors for that site")
        print("  - Always check robots.txt and Terms of Service first!")
        print("="*60 + "\n")
        response = input("Continue anyway? (yes/no): ").strip().lower()
        if response != "yes":
            print("Exiting. Please update SITE_CONFIG first.")
            sys.exit(1)


def main():
    """Main CLI loop"""
    print("="*60)
    print("=== Doctor Scraper CLI ===")
    print("="*60)
    print("\n⚠️  Legal Notice:")
    print("   Only scrape websites that explicitly allow automated access.")
    print("   Check their robots.txt and Terms of Service before scraping.\n")
    
    check_config()
    
    # Show current CSV stats if it exists
    if os.path.isfile(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row_count = sum(1 for _ in reader)
        print(f"📊 Current dataset: {row_count} rows in {CSV_FILE}\n")
    
    while True:
        query = input("Enter search term (e.g. 'orthopedic doctor', or 'q' to quit): ").strip()
        
        if not query or query.lower() == "q":
            print("Goodbye!")
            break
        
        print(f"\n🔍 Scraping for: '{query}' ...")
        print("   This may take 10-30 seconds...\n")
        
        try:
            results = scrape_doctors(query, SITE_CONFIG)
        except Exception as e:
            print(f"❌ ERROR while scraping: {e}")
            print("\nTroubleshooting:")
            print("  - Check your internet connection")
            print("  - Verify the website is accessible")
            print("  - Ensure CSS selectors in SITE_CONFIG are correct")
            print("  - Check if the site blocks automated access (403 error)\n")
            continue
        
        print(f"✅ Found {len(results)} results.")
        
        if results:
            # Show preview
            print("\n📋 Preview (first result):")
            for key, value in list(results[0].items())[:5]:
                if value:
                    print(f"   {key}: {value}")
            
            save_to_csv(results, query)
        else:
            print("⚠️  No results found. Try:")
            print("  - Different search terms")
            print("  - Checking if selectors are correct")
            print("  - Verifying the site structure hasn't changed\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)

