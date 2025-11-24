"""
⚠️ CORRECTED EDUCATIONAL EXAMPLE ⚠️

This shows the CORRECTED version of the code you provided.
It fixes all syntax errors and adds proper error handling.

❌ BUT: This will STILL NOT WORK on YellowPages
   - YellowPages explicitly forbids scraping
   - You will get 403 errors
   - Violates Terms of Service

✅ USE INSTEAD: google_places_scraper.py (legal alternative)
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

# Optional: For user-agent rotation (if you want to try on sites that allow scraping)
try:
    from fake_useragent import UserAgent
    HAS_FAKE_USERAGENT = True
except ImportError:
    HAS_FAKE_USERAGENT = False
    print("⚠️  fake-useragent not installed. Install with: pip install fake-useragent")


def search_orthopedic_doctor_CORRECTED():
    """
    CORRECTED version of your code with all syntax errors fixed.
    
    ⚠️ WARNING: This will NOT work on YellowPages (403 errors expected).
    Use google_places_scraper.py for legal doctor data instead.
    """
    
    print("=" * 70)
    print("⚠️  CORRECTED CODE EXAMPLE (Educational Only)")
    print("=" * 70)
    print("\nThis fixes all syntax errors in your code, but:")
    print("   ❌ Will NOT work on YellowPages (403 errors)")
    print("   ❌ Violates YellowPages Terms of Service")
    print("   ✅ Use google_places_scraper.py for legal data\n")
    
    response = input("Continue with corrected example? (yes/no): ").strip().lower()
    if response != "yes":
        print("Exiting. Use google_places_scraper.py for legal alternatives.")
        return
    
    # Set options for Chrome driver (FIXED: was addargument, should be add_argument)
    options = Options()
    options.add_argument('--headless=new')  # FIXED: was '--headless', new headless is better
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # FIXED: Incognito doesn't really help with detection, but keeping it
    options.add_argument('--incognito')
    
    # Optional: User-agent rotation (FIXED: was fakeuseragent, should be fake_useragent)
    if HAS_FAKE_USERAGENT:
        try:
            ua = UserAgent()
            random_ua = ua.random
            options.add_argument(f'user-agent={random_ua}')
            print(f"✅ Using random user-agent: {random_ua[:50]}...")
        except Exception as e:
            print(f"⚠️  Could not set random user-agent: {e}")
    else:
        # Fallback user-agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Initialize driver (FIXED: was webdrivermanager, should be webdriver_manager)
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        print("✅ Chrome driver initialized")
    except Exception as e:
        print(f"❌ Failed to create Chrome driver: {e}")
        print("Make sure Chrome browser is installed.")
        return
    
    try:
        # ⚠️ WARNING: This will fail on YellowPages
        print("\n🌐 Opening YellowPages (THIS WILL FAIL WITH 403)...")
        driver.get('https://www.yellowpages.com/')
        time.sleep(3)
        
        try:
            # Find search box (FIXED: was findelement, should be find_element)
            # FIXED: Try multiple selectors since YellowPages structure may vary
            search_box = None
            selectors = [
                (By.NAME, 'search_terms'),
                (By.NAME, 'searchterms'),
                (By.ID, 'search_terms'),
                (By.CSS_SELECTOR, 'input[name="search_terms"]'),
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
            
            # Add random delay (human-like)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Submit (FIXED: was sendkeys, should be send_keys)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for results (FIXED: Better to use WebDriverWait)
            print("⏳ Waiting for results...")
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'result'))
                )
            except TimeoutException:
                print("⚠️  Results didn't load - YellowPages likely blocked the request")
            
            time.sleep(5)
            
            # Get results (FIXED: was findelements, should be find_elements)
            results = driver.find_elements(By.CLASS_NAME, 'result')
            print(f"📋 Found {len(results)} result elements")
            
            if not results:
                print("\n❌ No results found.")
                print("   This is expected - YellowPages blocks automated access.")
                print("   You will get 403 Forbidden errors.")
                print("\n✅ Use google_places_scraper.py instead for legal doctor data.")
                return
            
            # Extract data (FIXED: was findelement, should be find_element)
            print("\n📊 Extracting data from results...")
            for i, result in enumerate(results[:5], 1):  # Limit to first 5
                try:
                    # FIXED: was findelement, should be find_element
                    name_elem = result.find_element(By.CLASS_NAME, 'business-name')
                    name = name_elem.text
                    
                    # FIXED: was findelements, should be find_elements
                    phone_elems = result.find_elements(By.CLASS_NAME, 'phone')
                    phone = phone_elems[0].text if phone_elems else 'N/A'
                    
                    # FIXED: was findelements, should be find_elements
                    address_elems = result.find_elements(By.CLASS_NAME, 'address')
                    address = address_elems[0].text if address_elems else 'N/A'
                    
                    print(f'{i}. Name: {name}, Phone: {phone}, Address: {address}')
                
                except Exception as e:
                    print(f"   ⚠️  Error extracting result {i}: {e}")
        
        except NoSuchElementException as e:
            print(f"❌ Element not found: {e}")
            print("   This is expected - YellowPages blocks automated access.")
            print("   You will get 403 Forbidden errors.")
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


def show_legal_alternative():
    """Show the legal alternative"""
    print("\n" + "=" * 70)
    print("✅ LEGAL ALTERNATIVE: Google Places API")
    print("=" * 70)
    print("\nInstead of trying to scrape YellowPages (which is forbidden), use:")
    print("   python google_places_scraper.py")
    print("\nThis provides:")
    print("   ✅ Legal access (official API)")
    print("   ✅ No 403 errors")
    print("   ✅ Reliable data")
    print("   ✅ Free tier available ($200/month credit)")
    print("   ✅ Better data quality than scraping")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("⚠️  CORRECTED CODE EXAMPLE (Educational Only)")
    print("=" * 70)
    print("\nThis fixes all syntax errors in your code:")
    print("   ✅ Fixed: addargument → add_argument")
    print("   ✅ Fixed: findelement → find_element")
    print("   ✅ Fixed: sendkeys → send_keys")
    print("   ✅ Fixed: webdrivermanager → webdriver_manager")
    print("   ✅ Fixed: fakeuseragent → fake_useragent")
    print("\nBUT: This will STILL NOT WORK on YellowPages!")
    print("   ❌ YellowPages explicitly forbids scraping")
    print("   ❌ You will get 403 errors")
    print("   ❌ Violates Terms of Service\n")
    
    choice = input("1. See corrected code (will fail on YellowPages)\n2. See legal alternative\nChoice (1/2): ").strip()
    
    if choice == "1":
        search_orthopedic_doctor_CORRECTED()
    elif choice == "2":
        show_legal_alternative()
    else:
        print("Invalid choice. Use google_places_scraper.py for legal doctor data.")

