"""
⚠️ EDUCATIONAL EXAMPLE - DO NOT USE ON YELLOWPAGES ⚠️

This script demonstrates Selenium scraping techniques for EDUCATIONAL purposes.
It includes the code structure you provided, but with corrections and warnings.

❌ DO NOT USE THIS ON YELLOWPAGES:
   - YellowPages explicitly forbids scraping
   - You will get 403 errors
   - Violates Terms of Service
   - Can result in legal action

✅ USE INSTEAD:
   - google_places_scraper.py (Google Places API)
   - Sites that explicitly allow scraping
   - Your own websites
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import random


def search_orthopedic_doctor_EDUCATIONAL_ONLY():
    """
    ⚠️ EDUCATIONAL EXAMPLE ONLY ⚠️
    
    This demonstrates Selenium scraping structure.
    DO NOT use on YellowPages - it's forbidden and will fail.
    
    Use google_places_scraper.py instead for legal doctor data.
    """
    
    print("=" * 70)
    print("⚠️  EDUCATIONAL EXAMPLE - DO NOT USE ON YELLOWPAGES ⚠️")
    print("=" * 70)
    print("\nYellowPages explicitly forbids scraping.")
    print("This will result in 403 errors and violates their Terms of Service.")
    print("\n✅ Use google_places_scraper.py instead for legal doctor data.\n")
    
    response = input("Continue with educational example? (yes/no): ").strip().lower()
    if response != "yes":
        print("Exiting. Use google_places_scraper.py for legal alternatives.")
        return
    
    # Configure Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # Uncomment for headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize the driver (FIXED: was missing proper setup)
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
    except Exception as e:
        print(f"❌ Failed to create Chrome driver: {e}")
        print("Make sure Chrome browser is installed.")
        return
    
    try:
        # ⚠️ WARNING: This will fail on YellowPages with 403 error
        target_url = site_url or 'https://www.yellowpages.com/'
        print(f"\n🌐 Opening {target_url}...")
        print("   ⚠️  If this is YellowPages, you will get 403 error!")
        driver.get(target_url)
        
        # Wait for page to load (FIXED: was time.sleep(3))
        time.sleep(3)
        
        try:
            # Find search box (FIXED: was findelement, should be find_element)
            # Also FIXED: By.NAME might not work, trying multiple selectors
            search_box = None
            
            # Try different selectors
            selectors = [
                (By.NAME, 'search_terms'),
                (By.NAME, 'searchterms'),
                (By.ID, 'search_terms'),
                (By.CSS_SELECTOR, 'input[name="search_terms"]'),
                (By.CSS_SELECTOR, 'input[type="search"]'),
            ]
            
            for by, value in selectors:
                try:
                    search_box = driver.find_element(by, value)
                    print(f"✅ Found search box using: {by}={value}")
                    break
                except NoSuchElementException:
                    continue
            
            if not search_box:
                raise NoSuchElementException("Could not find search box")
            
            # Input search term (FIXED: was sendkeys, should be send_keys)
            print("⌨️  Typing search query...")
            search_box.clear()
            search_box.send_keys('orthopedic doctor')
            
            # Add random delay (human-like behavior)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Submit (FIXED: was sendkeys, should be send_keys)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for results (FIXED: was time.sleep(5), better to use WebDriverWait)
            print("⏳ Waiting for results...")
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'result'))
                )
            except TimeoutException:
                print("⚠️  Results didn't load in time")
            
            time.sleep(3)  # Additional wait
            
            # Scrape results (FIXED: was findelements, should be find_elements)
            results = driver.find_elements(By.CLASS_NAME, 'result')
            print(f"📋 Found {len(results)} results")
            
            if not results:
                print("⚠️  No results found. This is expected on YellowPages (403 block).")
                print("   YellowPages blocks automated access.")
                return
            
            # Extract data from results
            for i, result in enumerate(results[:5], 1):  # Limit to first 5
                try:
                    text = result.text
                    print(f"\n{i}. {text[:100]}...")  # Print first 100 chars
                except Exception as e:
                    print(f"   Error extracting result {i}: {e}")
        
        except NoSuchElementException as e:
            print(f"❌ Element not found: {e}")
            print("   This is expected - YellowPages blocks automated access.")
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            print("   YellowPages has anti-bot measures that prevent scraping.")
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("\n💡 This is why you should use Google Places API instead:")
        print("   - Legal and reliable")
        print("   - No 403 errors")
        print("   - Better data quality")
        print("   - See google_places_scraper.py")
    
    finally:
        driver.quit()
        print("\n✅ Browser closed")


def search_orthopedic_doctor_LEGAL_ALTERNATIVE():
    """
    ✅ LEGAL ALTERNATIVE using Google Places API
    
    This is what you should use instead of scraping YellowPages.
    """
    print("\n" + "=" * 70)
    print("✅ LEGAL ALTERNATIVE: Google Places API")
    print("=" * 70)
    print("\nInstead of scraping YellowPages (which is forbidden), use:")
    print("   python google_places_scraper.py")
    print("\nBenefits:")
    print("   ✅ Legal and official")
    print("   ✅ No 403 errors")
    print("   ✅ Reliable data")
    print("   ✅ Free tier available")
    print("\nSee google_places_scraper.py for implementation.")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("⚠️  YELLOWPAGES SCRAPING EXAMPLE (EDUCATIONAL ONLY)")
    print("=" * 70)
    print("\nThis script demonstrates Selenium structure but:")
    print("   ❌ Will NOT work on YellowPages (403 errors)")
    print("   ❌ Violates YellowPages Terms of Service")
    print("   ❌ Can result in legal action")
    print("\n✅ Use google_places_scraper.py instead!\n")
    
    choice = input("1. See educational example (will fail)\n2. See legal alternative\nChoice (1/2): ").strip()
    
    if choice == "1":
        search_orthopedic_doctor_EDUCATIONAL_ONLY()
    elif choice == "2":
        search_orthopedic_doctor_LEGAL_ALTERNATIVE()
    else:
        print("Invalid choice. Use google_places_scraper.py for legal doctor data.")

