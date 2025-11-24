"""Generic doctor scraper with auto-detection capabilities"""
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
import logging

logger = logging.getLogger(__name__)


def _auto_find_search_box(driver):
    """
    Try to automatically find a search box if selector is not provided.
    This is heuristic and won't work on every site, but helps sometimes.
    """
    # 1) try input[type=search]
    try:
        el = driver.find_element(By.CSS_SELECTOR, "input[type='search']")
        return el
    except Exception:
        pass
    
    # 2) try any <input> with search-related hints
    candidates = driver.find_elements(By.TAG_NAME, "input")
    keywords = ["search", "query", "keyword", "doctor", "find", "lookup"]
    
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
    
    if best_score > 0:
        logger.info(f"Auto-detected search box with score {best_score}")
        return best_el
    
    return None


def scrape_doctors(query: str, cfg: dict):
    """
    Scrape doctors from a website that requires search interaction.
    
    Args:
        query: Search query (e.g., "orthopedic doctor")
        cfg: Configuration dict with selectors
    
    Config example:
    {
      "url": "https://example-doctors.com",
      "search_box_selector": "input[name='search']",  # optional
      "submit_selector": "button.search-submit",      # optional
      "result_item_selector": ".doctor-card",
      "fields": {
        "name": ".doctor-name",
        "specialty": ".doctor-specialty",
        "phone": ".doctor-phone",
        "address": ".doctor-address"
      },
      "profile_link_selector": ".doctor-name a",      # optional
      "wait_seconds": 5
    }
    
    Returns:
        List of dicts with extracted doctor data
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
        logger.error(f"Failed to create Chrome driver: {e}")
        raise RuntimeError(f"Chrome driver not available: {e}")
    
    try:
        logger.info(f"Navigating to {cfg['url']}")
        driver.get(cfg["url"])
        time.sleep(2)  # Initial page load
        
        # 1. Get search box (config or auto)
        if cfg.get("search_box_selector"):
            try:
                search_el = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, cfg["search_box_selector"]))
                )
            except TimeoutException:
                raise RuntimeError(f"Search box not found with selector: {cfg['search_box_selector']}")
        else:
            search_el = _auto_find_search_box(driver)
            if not search_el:
                raise RuntimeError("Could not find search box – set 'search_box_selector' in config or ensure page has detectable search input.")
        
        search_el.clear()
        search_el.send_keys(query)
        time.sleep(0.5)
        
        # 2. Submit the form
        if cfg.get("submit_selector"):
            try:
                submit_btn = driver.find_element(By.CSS_SELECTOR, cfg["submit_selector"])
                submit_btn.click()
            except NoSuchElementException:
                logger.warning("Submit button not found, using Enter key")
                search_el.send_keys(Keys.ENTER)
        else:
            search_el.send_keys(Keys.ENTER)
        
        # 3. Wait for results
        wait_seconds = cfg.get("wait_seconds", 5)
        time.sleep(wait_seconds)
        
        # 4. Parse HTML with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        results = []
        
        items = soup.select(cfg["result_item_selector"])
        logger.info(f"Found {len(items)} result items")
        
        for item in items:
            record = {}
            
            # Extract each field defined in config
            for field_name, selector in cfg.get("fields", {}).items():
                el = item.select_one(selector)
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
                a = item.select_one(link_sel)
                if a and a.has_attr("href"):
                    href = a["href"]
                    # Make absolute URL if relative
                    if href.startswith("/"):
                        from urllib.parse import urljoin
                        record["profile_link"] = urljoin(cfg["url"], href)
                    else:
                        record["profile_link"] = href
                else:
                    record["profile_link"] = None
            
            # Only add if we got at least one field
            if any(record.values()):
                results.append(record)
        
        logger.info(f"Extracted {len(results)} valid records")
        return results
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    # Small demo – you must fill a real config yourself
    # ⚠️ WARNING: Only use on sites that allow scraping!
    
    config = {
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
    
    print("⚠️  This is a demo config. Replace with a real site that allows scraping!")
    print("⚠️  Always check robots.txt and Terms of Service before scraping!")
    
    # Uncomment to test:
    # data = scrape_doctors("orthopedic doctor", config)
    # print(f"Found {len(data)} doctors")
    # for doc in data[:3]:
    #     print(doc)

