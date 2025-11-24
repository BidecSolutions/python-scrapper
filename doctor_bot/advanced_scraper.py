"""Advanced scraper with anti-detection techniques for legitimate use only"""
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
import random
import csv
import os
from datetime import datetime
from urllib.parse import urljoin


# ⚠️ LEGAL WARNING ⚠️
# These techniques are for LEGITIMATE use only on sites that explicitly allow scraping.
# Using these to bypass blocks on sites that forbid scraping is:
# - Illegal in many jurisdictions
# - Violates Terms of Service
# - Can result in legal action
# - Unethical
#
# Only use on sites that:
# - Explicitly allow scraping in their Terms of Service
# - Have permissive robots.txt
# - You have written permission to scrape


class AdvancedScraper:
    """Advanced scraper with anti-detection and human-like behavior"""
    
    def __init__(self, headless=True, use_proxy=False, proxy=None):
        """
        Initialize advanced scraper
        
        Args:
            headless: Run browser in headless mode
            use_proxy: Whether to use proxy (requires proxy config)
            proxy: Proxy configuration (e.g., "http://proxy:port")
        """
        self.headless = headless
        self.use_proxy = use_proxy
        self.proxy = proxy
        self.driver = None
    
    def _get_random_user_agent(self):
        """Get a random realistic user agent"""
        user_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]
        return random.choice(user_agents)
    
    def _get_random_viewport_size(self):
        """Get random realistic viewport size"""
        viewports = [
            (1920, 1080),  # Full HD
            (1366, 768),   # Common laptop
            (1536, 864),   # Common laptop
            (1440, 900),   # MacBook
            (1280, 720),   # HD
        ]
        return random.choice(viewports)
    
    def _create_stealth_options(self):
        """Create Chrome options with anti-detection features"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # Basic stealth
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        user_agent = self._get_random_user_agent()
        chrome_options.add_argument(f"user-agent={user_agent}")
        
        # Random viewport
        width, height = self._get_random_viewport_size()
        chrome_options.add_argument(f"--window-size={width},{height}")
        
        # Language preferences (make it look like a real browser)
        chrome_options.add_argument("--lang=en-US,en")
        chrome_options.add_experimental_option("prefs", {
            "intl.accept_languages": "en-US,en;q=0.9",
        })
        
        # Disable automation flags
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        
        # Proxy (if configured)
        if self.use_proxy and self.proxy:
            chrome_options.add_argument(f"--proxy-server={self.proxy}")
        
        return chrome_options
    
    def _human_like_delay(self, min_seconds=0.5, max_seconds=2.0):
        """Add random human-like delay"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def _human_like_typing(self, element, text):
        """Type text with human-like delays between characters"""
        for char in text:
            element.send_keys(char)
            # Random delay between keystrokes (faster for common chars)
            if char == ' ':
                delay = random.uniform(0.05, 0.15)
            else:
                delay = random.uniform(0.08, 0.25)
            time.sleep(delay)
    
    def _scroll_page(self, driver):
        """Scroll page to mimic human behavior"""
        try:
            # Random scroll amount
            scroll_amount = random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            self._human_like_delay(0.5, 1.5)
            
            # Sometimes scroll back up a bit
            if random.random() > 0.7:
                scroll_back = random.randint(100, 300)
                driver.execute_script(f"window.scrollBy(0, -{scroll_back});")
                self._human_like_delay(0.3, 0.8)
        except Exception:
            pass  # Ignore scroll errors
    
    def _execute_stealth_script(self, driver):
        """Execute JavaScript to hide automation"""
        stealth_script = """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Chrome runtime
        window.chrome = {
            runtime: {}
        };
        """
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': stealth_script
        })
    
    def create_driver(self):
        """Create and configure Chrome driver with stealth features"""
        chrome_options = self._create_stealth_options()
        
        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # Execute stealth script
            self._execute_stealth_script(driver)
            
            # Set viewport
            width, height = self._get_random_viewport_size()
            driver.set_window_size(width, height)
            
            self.driver = driver
            return driver
        except Exception as e:
            raise RuntimeError(f"Failed to create Chrome driver: {e}")
    
    def scrape_with_stealth(self, query: str, cfg: dict):
        """
        Scrape with advanced anti-detection techniques
        
        ⚠️ WARNING: Only use on sites that explicitly allow scraping!
        """
        driver = self.create_driver()
        
        try:
            # Navigate with delay
            print(f"🌐 Opening {cfg['url']}...")
            driver.get(cfg["url"])
            self._human_like_delay(2, 4)  # Wait for page load
            
            # Sometimes scroll a bit
            if random.random() > 0.5:
                self._scroll_page(driver)
            
            # Find search box
            search_el = None
            if cfg.get("search_box_selector"):
                try:
                    search_el = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, cfg["search_box_selector"]))
                    )
                except TimeoutException:
                    raise RuntimeError(f"Search box not found: {cfg['search_box_selector']}")
            else:
                # Auto-detect (simplified version)
                try:
                    search_el = driver.find_element(By.CSS_SELECTOR, "input[type='search']")
                except:
                    raise RuntimeError("Could not find search box. Provide 'search_box_selector' in config.")
            
            # Human-like interaction with search box
            search_el.click()
            self._human_like_delay(0.3, 0.8)
            
            # Clear and type with human-like delays
            search_el.clear()
            self._human_like_delay(0.2, 0.5)
            self._human_like_typing(search_el, query)
            self._human_like_delay(0.5, 1.0)
            
            # Submit search
            if cfg.get("submit_selector"):
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, cfg["submit_selector"])
                    # Move to button first (human-like)
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    self._human_like_delay(0.3, 0.7)
                    btn.click()
                except NoSuchElementException:
                    search_el.send_keys(Keys.ENTER)
            else:
                search_el.send_keys(Keys.ENTER)
            
            # Wait for results with random delay
            base_wait = cfg.get("wait_seconds", 5)
            wait_time = base_wait + random.uniform(-1, 2)  # Add randomness
            print(f"⏳ Waiting {wait_time:.1f} seconds for results...")
            time.sleep(wait_time)
            
            # Scroll to load more content (if lazy loading)
            self._scroll_page(driver)
            time.sleep(1)
            
            # Parse results
            soup = BeautifulSoup(driver.page_source, "html.parser")
            results = []
            
            items = soup.select(cfg["result_item_selector"])
            print(f"📋 Found {len(items)} result items")
            
            for card in items:
                record = {}
                
                for field_name, selector in cfg.get("fields", {}).items():
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
                
                # Profile link
                link_sel = cfg.get("profile_link_selector")
                if link_sel:
                    a = card.select_one(link_sel)
                    if a and a.has_attr("href"):
                        href = a["href"]
                        if href.startswith("/"):
                            record["profile_link"] = urljoin(cfg["url"], href)
                        else:
                            record["profile_link"] = href
                    else:
                        record["profile_link"] = None
                
                if any(record.values()):
                    results.append(record)
            
            print(f"✅ Extracted {len(results)} valid records")
            return results
            
        except Exception as e:
            print(f"❌ Error: {e}")
            raise
        finally:
            if driver:
                driver.quit()


def save_results(results, query, filename="scraped_doctors.csv"):
    """Save results to CSV"""
    if not results:
        return
    
    for r in results:
        r["query"] = query
        r["timestamp"] = datetime.utcnow().isoformat()
    
    fieldnames = sorted(results[0].keys())
    file_exists = os.path.isfile(filename)
    
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    print(f"💾 Saved {len(results)} rows to {filename}")


def main():
    """
    ⚠️ CRITICAL LEGAL WARNING ⚠️
    
    These advanced techniques are for LEGITIMATE use ONLY:
    - Only on sites that explicitly allow scraping
    - With proper rate limiting
    - Respecting robots.txt
    - Following Terms of Service
    
    Using these to bypass blocks is:
    - Potentially illegal
    - Violates Terms of Service
    - Unethical
    - Can result in legal action
    
    You are responsible for compliance!
    """
    
    print("=" * 70)
    print("=== Advanced Doctor Scraper (Anti-Detection) ===")
    print("=" * 70)
    print("\n⚠️  LEGAL WARNING:")
    print("   These techniques are for LEGITIMATE use only!")
    print("   Only use on sites that explicitly allow scraping.")
    print("   Using to bypass blocks is illegal and unethical.\n")
    
    response = input("I understand and will only use this legally (yes/no): ").strip().lower()
    if response != "yes":
        print("Exiting. Please only use on sites that allow scraping.")
        return
    
    # Configure your site
    site_config = {
        "url": "https://doctors.example.com",  # UPDATE THIS
        "result_item_selector": ".doctor-card",
        "fields": {
            "name": ".doctor-name",
            "specialty": ".doctor-specialty",
            "phone": ".doctor-phone",
            "address": ".doctor-address"
        },
        "wait_seconds": 5
    }
    
    # Create scraper
    scraper = AdvancedScraper(
        headless=True,  # Set to False to see browser
        use_proxy=False,  # Set to True if you have proxy
        proxy=None  # "http://proxy:port" if using proxy
    )
    
    while True:
        q = input("\nEnter search query (or 'q' to quit): ").strip()
        if not q or q.lower() == "q":
            break
        
        try:
            results = scraper.scrape_with_stealth(q, site_config)
            if results:
                print(f"\n✅ Found {len(results)} results")
                for i, r in enumerate(results[:3], 1):
                    print(f"{i}. {r.get('name')} - {r.get('specialty')}")
                save_results(results, q)
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")

