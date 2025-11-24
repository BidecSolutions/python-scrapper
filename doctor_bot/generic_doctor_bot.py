"""Generic Doctor Search Bot - Single-file scraper with auto-detection"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import csv
import os
from datetime import datetime
from urllib.parse import urljoin


def auto_find_search_box(driver):
    """
    Try to automatically find a search input.
    Heuristics: input[type=search] or input whose name/id/placeholder
    contains common keywords.
    """
    # 1) Try <input type="search">
    try:
        el = driver.find_element(By.CSS_SELECTOR, "input[type='search']")
        return el
    except Exception:
        pass

    # 2) Try any <input> with search-like attributes
    candidates = driver.find_elements(By.TAG_NAME, "input")
    keywords = ["search", "query", "keyword", "doctor", "find", "what", "who", "lookup"]

    def score_input(inp):
        txt = (
            (inp.get_attribute("name") or "") + " " +
            (inp.get_attribute("id") or "") + " " +
            (inp.get_attribute("placeholder") or "") + " " +
            (inp.get_attribute("class") or "")
        ).lower()
        score = 0
        for kw in keywords:
            if kw in txt:
                score += 1
        return score

    best_el = None
    best_score = 0
    for inp in candidates:
        s = score_input(inp)
        if s > best_score:
            best_score = s
            best_el = inp

    return best_el if best_score > 0 else None


def scrape_site(query: str, cfg: dict):
    """
    Scrape a website that requires search interaction.
    
    cfg example (YOU customize this per site):
    
    cfg = {
      "url": "https://doctors.example.com",
      "search_box_selector": "input[name='q']",   # optional, auto if missing
      "submit_selector": "button.search-btn",     # optional, use Enter if missing
      "result_item_selector": ".doctor-card",     # required
      "fields": {                                 # required
        "name": ".doc-name",
        "specialty": ".doc-specialty",
        "phone": ".doc-phone",
        "address": ".doc-address"
      },
      "profile_link_selector": ".doc-name a",     # optional
      "wait_seconds": 5
    }
    
    Returns:
        List of dicts with extracted data
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
    except Exception as e:
        raise RuntimeError(f"Failed to create Chrome driver: {e}")

    try:
        print(f"🌐 Opening {cfg['url']}...")
        driver.get(cfg["url"])
        time.sleep(2)  # Initial page load

        # 1) Find search box
        search_el = None
        if cfg.get("search_box_selector"):
            try:
                search_el = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, cfg["search_box_selector"]))
                )
                print(f"✅ Found search box using selector: {cfg['search_box_selector']}")
            except TimeoutException:
                raise RuntimeError(f"Search box not found with selector: {cfg['search_box_selector']}")
        else:
            print("🔍 Auto-detecting search box...")
            search_el = auto_find_search_box(driver)
            if search_el:
                print("✅ Auto-detected search box")
            else:
                raise RuntimeError("Could not find search input. Provide 'search_box_selector' in config.")

        search_el.clear()
        search_el.send_keys(query)
        time.sleep(0.5)

        # 2) Submit search
        if cfg.get("submit_selector"):
            try:
                btn = driver.find_element(By.CSS_SELECTOR, cfg["submit_selector"])
                btn.click()
                print("✅ Clicked submit button")
            except NoSuchElementException:
                print("⚠️  Submit button not found, using Enter key")
                search_el.send_keys(Keys.ENTER)
        else:
            search_el.send_keys(Keys.ENTER)
            print("✅ Submitted search (Enter key)")

        # 3) Wait for results to load
        wait_seconds = cfg.get("wait_seconds", 5)
        print(f"⏳ Waiting {wait_seconds} seconds for results...")
        time.sleep(wait_seconds)

        # 4) Parse page HTML
        soup = BeautifulSoup(driver.page_source, "html.parser")
        results = []

        items = soup.select(cfg["result_item_selector"])
        print(f"📋 Found {len(items)} result items")

        for card in items:
            record = {}
            
            # Extract fields
            for field_name, selector in cfg.get("fields", {}).items():
                el = card.select_one(selector)
                if el:
                    # Try text first, then attributes
                    text = el.get_text(strip=True)
                    if text:
                        record[field_name] = text
                    elif el.has_attr("href"):
                        record[field_name] = el["href"]
                    elif el.has_attr("src"):
                        record[field_name] = el["src"]
                    else:
                        record[field_name] = None
                else:
                    record[field_name] = None

            # Optional profile link
            link_sel = cfg.get("profile_link_selector")
            if link_sel:
                a = card.select_one(link_sel)
                if a and a.has_attr("href"):
                    href = a["href"]
                    # Make absolute URL if relative
                    if href.startswith("/"):
                        record["profile_link"] = urljoin(cfg["url"], href)
                    else:
                        record["profile_link"] = href
                else:
                    record["profile_link"] = None

            # Only add if we got at least one field
            if any(record.values()):
                results.append(record)

        print(f"✅ Extracted {len(results)} valid records")
        return results

    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        raise
    finally:
        driver.quit()


def save_results(results, query, filename="scraped_doctors.csv"):
    """Save scraping results to CSV file"""
    if not results:
        print("⚠️  No results to save.")
        return

    # Add metadata columns
    for r in results:
        r["query"] = query
        r["timestamp"] = datetime.utcnow().isoformat()

    fieldnames = sorted(results[0].keys())
    file_exists = os.path.isfile(filename)

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
            print(f"📄 Created new CSV file: {filename}")

        for row in results:
            writer.writerow(row)

    print(f"💾 Saved {len(results)} rows to {filename}")


def main():
    """
    🔧 TODO: EDIT THIS CONFIG FOR YOUR TARGET SITE
    
    Steps to configure:
    1. Open the target website in your browser
    2. Use Inspect Element (F12) to find CSS selectors:
       - Search input: Right-click → Inspect → Copy selector
       - Search button: Same process
       - Result cards: Container for each doctor listing
       - Fields inside cards: Name, specialty, phone, address selectors
    3. Update the config below with your selectors
    4. Test with a simple query first
    """
    
    site_config = {
        "url": "https://doctors.example.com",     # <-- PUT YOUR REAL URL HERE
        
        # Optional: Uncomment and set if auto-detection doesn't work
        # "search_box_selector": "input[name='q']",
        # "submit_selector": "button.search-btn",
        
        "result_item_selector": ".doctor-card",      # MUST match result cards on the page
        
        "fields": {
            "name": ".doctor-name",                  # Selector for doctor name
            "specialty": ".doctor-specialty",        # Selector for specialty
            "phone": ".doctor-phone",                # Selector for phone number
            "address": ".doctor-address"            # Selector for address
        },
        
        "profile_link_selector": ".doctor-name a",   # Optional: Link to doctor profile
        "wait_seconds": 5                            # Wait time after search (adjust if needed)
    }

    print("=" * 60)
    print("=== Generic Doctor Search Bot ===")
    print("=" * 60)
    print("\n⚠️  LEGAL NOTICE:")
    print("   Only use this on websites that explicitly allow automated scraping.")
    print("   Check their robots.txt and Terms of Service before using.")
    print("\n❌ DO NOT SCRAPE:")
    print("   - YellowPages (explicitly forbidden, 403 errors)")
    print("   - LinkedIn, Facebook, Instagram")
    print("   - Any site that blocks automated access")
    print("\n✅ LEGAL ALTERNATIVES:")
    print("   - Google Places API (see google_places_scraper.py)")
    print("   - BetterDoctor API")
    print("   - Sites that explicitly allow scraping\n")
    
    # Warn if using example config
    if "example" in site_config["url"].lower():
        print("⚠️  WARNING: You're using the example config!")
        print("   Please update 'site_config' in the script with:")
        print("   - A real website URL that allows scraping")
        print("   - Correct CSS selectors for that site")
        print("\n💡 Options:")
        print("   1. Test with mock data: python test_with_mock.py")
        print("   2. Use a practice site: http://quotes.toscrape.com/")
        print("   3. Use your own website")
        print("   4. See LEGAL_SITES.md for suggestions\n")
        response = input("Continue anyway? (yes/no): ").strip().lower()
        if response != "yes":
            print("Exiting. Please update the config first.")
            return

    # Show CSV stats if file exists
    csv_file = "scraped_doctors.csv"
    if os.path.isfile(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row_count = sum(1 for _ in reader)
        print(f"📊 Current dataset: {row_count} rows in {csv_file}\n")

    while True:
        q = input("Enter search text (e.g. 'orthopedic doctor', or 'q' to quit): ").strip()
        
        if not q or q.lower() == "q":
            print("👋 Goodbye!")
            break

        print(f"\n🔍 Searching '{q}' on {site_config['url']}...")
        print("   This may take 10-30 seconds...\n")
        
        try:
            results = scrape_site(q, site_config)
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error while scraping: {e}")
            print("\n💡 Troubleshooting:")
            
            if "403" in error_msg or "forbidden" in error_msg.lower():
                print("   ⚠️  This site blocks automated scraping (403 Forbidden)")
                print("   - This is a legal/technical block from the website")
                print("   - You cannot bypass this - it's against their Terms of Service")
                print("   - Try a different site that allows scraping")
                print("   - See LEGAL_SITES.md for suggestions")
                print("   - Or test with: python test_with_mock.py\n")
            else:
                print("   - Check your internet connection")
                print("   - Verify the website is accessible")
                print("   - Ensure CSS selectors in config are correct")
                print("   - Try increasing 'wait_seconds' if results don't load")
                print("   - Test selectors with: python test_with_mock.py\n")
            continue

        print(f"\n✅ Found {len(results)} results.")
        
        if results:
            # Show preview
            print("\n📋 Preview (first 5 results):")
            print("-" * 60)
            for i, r in enumerate(results[:5], start=1):
                name = r.get('name', 'N/A')
                specialty = r.get('specialty', 'N/A')
                phone = r.get('phone', 'N/A')
                address = r.get('address', 'N/A')
                print(f"{i}. {name}")
                print(f"   Specialty: {specialty}")
                print(f"   Phone: {phone}")
                print(f"   Address: {address}")
                if r.get('profile_link'):
                    print(f"   Link: {r['profile_link']}")
                print()
            
            save_results(results, q, csv_file)
        else:
            print("⚠️  No results found. Try:")
            print("   - Different search terms")
            print("   - Checking if selectors are correct")
            print("   - Verifying the site structure hasn't changed\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

