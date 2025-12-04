"""Google Maps scraper with advanced anti-detection features"""
import logging
import time
import random
import re
from typing import List, Dict, Optional, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

from app.scraper.extractor import extract_contacts
from app.utils.text import normalize_email, normalize_phone

logger = logging.getLogger(__name__)


class GoogleMapsScraper:
    """
    Google Maps scraper with anti-detection techniques.
    
    ⚠️ IMPORTANT: Only use this for legitimate purposes. Be respectful of Google's
    Terms of Service and rate limits. Consider using the official Google Places API
    for production use.
    """
    
    GOOGLE_MAPS_URL = "https://www.google.com/maps"
    
    def __init__(self, headless: bool = True, use_stealth: bool = True):
        """
        Initialize Google Maps scraper
        
        Args:
            headless: Run browser in headless mode
            use_stealth: Use advanced stealth techniques to avoid detection
        """
        self.headless = headless
        self.use_stealth = use_stealth
        self.driver = None
    
    def _get_driver(self):
        """Get or create Chrome driver with anti-detection features"""
        if self.driver is None:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless=new")
            
            # Basic Chrome options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Anti-detection features
            if self.use_stealth:
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Random user agent
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ]
                chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
            
            # Additional stealth options
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            chrome_options.add_argument("--disable-site-isolation-trials")
            
            try:
                # Try to use webdriver-manager if available
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    self.driver = webdriver.Chrome(
                        service=Service(ChromeDriverManager().install()),
                        options=chrome_options
                    )
                except ImportError:
                    # Fallback to system Chrome
                    self.driver = webdriver.Chrome(options=chrome_options)
                
                # Remove webdriver property to avoid detection
                if self.use_stealth:
                    self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                        'source': '''
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            });
                        '''
                    })
                    # Override navigator.plugins
                    self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                        'source': '''
                            Object.defineProperty(navigator, 'plugins', {
                                get: () => [1, 2, 3, 4, 5]
                            });
                        '''
                    })
                    
            except Exception as e:
                logger.error(f"Failed to create Chrome driver: {e}")
                raise ValueError(f"Chrome driver not available: {e}")
        
        return self.driver
    
    def _human_like_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add human-like random delay"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def _scroll_page(self, element=None, scroll_amount: int = 400):
        """Scroll the page like a human would"""
        driver = self._get_driver()
        if element:
            driver.execute_script("arguments[0].scrollTop += arguments[1];", element, scroll_amount)
        else:
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        self._human_like_delay(0.3, 0.8)
    
    def search_places(
        self,
        query: str,
        location: Optional[str] = None,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search Google Maps for places and extract business information
        
        Args:
            query: Search query (e.g., "orthopedic doctor", "find doctor")
            location: Optional location (e.g., "New York", "New York, NY")
            max_results: Maximum number of results to return
        
        Returns:
            List of dictionaries with business information:
            {
                "name": str,
                "address": str,
                "phone": str,
                "email": str | None,
                "website": str | None,
                "rating": float | None,
                "reviews": int | None,
                "category": str | None
            }
        """
        driver = self._get_driver()
        results = []
        
        try:
            # Build search query
            search_query = f"{query}"
            if location:
                search_query += f" in {location}"
            
            logger.info(f"Searching Google Maps for: {search_query}")
            
            # Navigate to Google Maps
            driver.get(self.GOOGLE_MAPS_URL)
            self._human_like_delay(2, 4)
            
            # Find and interact with search box
            try:
                # Try different selectors for the search box
                search_selectors = [
                    "input#searchboxinput",
                    "input[aria-label='Search Google Maps']",
                    "input[placeholder*='Search']",
                    "input[name='q']",
                    "#searchboxinput"
                ]
                
                search_box = None
                for selector in search_selectors:
                    try:
                        search_box = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if not search_box:
                    raise ValueError("Could not find Google Maps search box")
                
                # Clear and type search query with human-like typing
                search_box.clear()
                for char in search_query:
                    search_box.send_keys(char)
                    if random.random() > 0.7:  # Occasional pause
                        time.sleep(random.uniform(0.1, 0.3))
                
                self._human_like_delay(0.5, 1.0)
                
                # Submit search
                search_box.send_keys(Keys.ENTER)
                self._human_like_delay(3, 5)  # Wait for results to load
                
            except Exception as e:
                logger.error(f"Error interacting with search box: {e}")
                raise ValueError(f"Failed to perform search: {e}")
            
            # Wait for results panel to appear
            try:
                # Wait for sidebar with results
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[role='main']"))
                )
                self._human_like_delay(2, 3)
            except TimeoutException:
                logger.warning("Results panel did not appear - page might have loaded differently")
            
            # Wait for results to load
            self._human_like_delay(3, 5)
            
            # Extract results by clicking on each result link to open details panel
            extracted_names = set()
            scroll_attempts = 0
            max_scroll_attempts = 15
            
            while len(results) < max_results and scroll_attempts < max_scroll_attempts:
                # Wait for results to load
                self._human_like_delay(2, 3)
                
                # Find clickable result links using Selenium
                try:
                    # Get all result links from the sidebar
                    result_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
                    
                    # Filter to only get links from the results list (not the map)
                    valid_links = []
                    for link in result_links:
                        try:
                            # Check if link is visible and in results panel
                            if link.is_displayed():
                                href = link.get_attribute('href')
                                if href and '/maps/place/' in href:
                                    # Extract place name from link or nearby text
                                    parent = link.find_element(By.XPATH, "./..")
                                    text = parent.text.strip() if parent else ""
                                    
                                    # Skip if it's clearly a UI element
                                    if not self._is_valid_business_name(text.split('\n')[0] if text else ""):
                                        continue
                                    
                                    valid_links.append(link)
                        except Exception:
                            continue
                    
                    logger.info(f"Found {len(valid_links)} valid result links")
                    
                    found_new = False
                    for link in valid_links:
                        if len(results) >= max_results:
                            break
                        
                        try:
                            # Scroll link into view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                            self._human_like_delay(0.5, 1.0)
                            
                            # Click on the link to open details
                            link.click()
                            self._human_like_delay(2, 3)
                            
                            # Extract from details panel
                            business_data = self._extract_from_details_panel(driver)
                            
                            if business_data and business_data.get("name"):
                                name = business_data.get("name")
                                if name and name not in extracted_names:
                                    extracted_names.add(name)
                                    results.append(business_data)
                                    found_new = True
                                    logger.info(f"Extracted: {name}")
                            
                        except Exception as e:
                            logger.debug(f"Error extracting from link: {e}")
                            continue
                    
                    if found_new and len(results) < max_results:
                        # Scroll down to load more results
                        try:
                            scrollable = driver.find_element(By.CSS_SELECTOR, "div[role='main']")
                            driver.execute_script("arguments[0].scrollTop += 1000;", scrollable)
                            self._human_like_delay(2, 3)
                            scroll_attempts += 1
                        except Exception:
                            scroll_attempts += 1
                    else:
                        if scroll_attempts > 3:
                            logger.info("No new results found, stopping")
                            break
                        scroll_attempts += 1
                    
                except Exception as e:
                    logger.warning(f"Error finding result links: {e}")
                    scroll_attempts += 1
                    
                if scroll_attempts >= max_scroll_attempts:
                    break
                
                # Scroll down to load more results
                if len(results) < max_results:
                    try:
                        # Find the scrollable results panel
                        scrollable_selectors = [
                            "div[role='main']",
                            ".m6QErb",
                            "[aria-label*='Results']"
                        ]
                        
                        scrollable_element = None
                        for selector in scrollable_selectors:
                            try:
                                scrollable_element = driver.find_element(By.CSS_SELECTOR, selector)
                                break
                            except NoSuchElementException:
                                continue
                        
                        if scrollable_element:
                            self._scroll_page(scrollable_element, scroll_amount=500)
                        else:
                            # Fallback: scroll the page
                            driver.execute_script("window.scrollBy(0, 500);")
                            self._human_like_delay(1, 2)
                        
                        scroll_attempts += 1
                        
                        # Wait for new content to load
                        self._human_like_delay(2, 3)
                        
                        if not found_new:
                            logger.info("No new results found, stopping scroll")
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error scrolling: {e}")
                        break
                else:
                    break
            
            logger.info(f"Successfully extracted {len(results)} businesses")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error during Google Maps scraping: {e}", exc_info=True)
            raise
        finally:
            # Don't close driver here - let it be reused
            pass
    
    def _extract_business_info_from_soup(self, item_element, driver) -> Optional[Dict[str, Any]]:
        """
        Extract business information from a BeautifulSoup element
        
        Args:
            item_element: BeautifulSoup element
            driver: Selenium driver for additional interactions
        
        Returns:
            Dictionary with business information or None
        """
        business_data = {
            "name": None,
            "address": None,
            "phone": None,
            "email": None,
            "website": None,
            "rating": None,
            "reviews": None,
            "category": None
        }
        
        try:
            # Handle BeautifulSoup element
            soup = item_element
            if not hasattr(soup, 'select_one'):
                # Not a BeautifulSoup element, try to convert
                if hasattr(item_element, 'get_attribute') and callable(item_element.get_attribute):
                    # Selenium element
                    html = item_element.get_attribute('outerHTML')
                    soup = BeautifulSoup(html, 'html.parser')
                else:
                    logger.debug("Invalid element type for extraction")
                    return None
            
            # Extract name - try multiple approaches
            name_text = None
            
            # Try direct text extraction from common name containers
            name_selectors = [
                "span.DUwDvf",
                ".qBF1Pd",
                "div.fontHeadlineLarge",
                "[data-value='name']",
                ".qBF1Pd.fontHeadlineLarge",
                "a[href*='/maps/place/']",
            ]
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    name_text = name_elem.get_text(strip=True)
                    if name_text and len(name_text) > 2:
                        business_data["name"] = name_text
                        break
            
            # If no name found, try to get text from the element itself
            if not business_data["name"]:
                direct_text = soup.get_text(strip=True) if hasattr(soup, 'get_text') else None
                if direct_text and len(direct_text) > 2 and len(direct_text) < 100:
                    candidate_name = direct_text.split('\n')[0].strip()
                    # Filter out UI elements
                    if self._is_valid_business_name(candidate_name):
                        business_data["name"] = candidate_name
            
            # Validate and filter out UI elements from extracted name
            if business_data["name"]:
                if not self._is_valid_business_name(business_data["name"]):
                    return None  # Skip this item if it's not a valid business name
            
            # Extract address
            address_selectors = [
                "span[data-value='address']",
                ".W4Efsd:last-of-type span.W4Efsd:last-of-type span",
                ".Io6YTe",
                "[data-value='address']"
            ]
            for selector in address_selectors:
                addr_elem = soup.select_one(selector)
                if addr_elem:
                    business_data["address"] = addr_elem.get_text(strip=True)
                    break
            
            # Extract rating
            rating_elem = soup.select_one("span.MW4etd, span.fontBodyMedium")
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                # Extract numeric rating
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        business_data["rating"] = float(rating_match.group(1))
                    except ValueError:
                        pass
            
            # Extract category
            category_elem = soup.select_one(".W4Efsd span.W4Efsd")
            if category_elem:
                business_data["category"] = category_elem.get_text(strip=True)
            
            # Try to click on the result to get more details (phone, website)
            # Only if it's a Selenium element with a callable click method
            if hasattr(item_element, 'click') and callable(getattr(item_element, 'click', None)):
                try:
                    # Click on the item
                    item_element.click()
                    self._human_like_delay(2, 3)
                    
                    # Extract phone and website from detailed view
                    page_source = driver.page_source
                    detail_soup = BeautifulSoup(page_source, 'html.parser')
                    
                    # Extract phone
                    phone_selectors = [
                        "[data-value='phone']",
                        "button[data-item-id*='phone']",
                        "a[href^='tel:']"
                    ]
                    for selector in phone_selectors:
                        phone_elem = detail_soup.select_one(selector)
                        if phone_elem:
                            phone_text = phone_elem.get_text(strip=True)
                            if phone_text:
                                business_data["phone"] = normalize_phone(phone_text)
                            # Also check href attribute
                            if phone_elem.get('href', '').startswith('tel:'):
                                tel = phone_elem.get('href').replace('tel:', '').strip()
                                business_data["phone"] = normalize_phone(tel)
                            if business_data["phone"]:
                                break
                    
                    # Extract website
                    website_selectors = [
                        "a[data-value='website']",
                        "a[href*='http'][aria-label*='Website']",
                        "a[href^='http']"
                    ]
                    for selector in website_selectors:
                        website_elem = detail_soup.select_one(selector)
                        if website_elem:
                            href = website_elem.get('href', '')
                            if href and href.startswith('http'):
                                business_data["website"] = href
                                break
                    
                    # Extract email from website if available
                    if business_data["website"]:
                        business_data["email"] = self._extract_email_from_website(business_data["website"])
                    
                except (ElementClickInterceptedException, TimeoutException) as e:
                    logger.debug(f"Could not click item for details: {e}")
                except Exception as e:
                    logger.debug(f"Error extracting details: {e}")
            
            # Only return if we have at least a name
            if business_data["name"]:
                return business_data
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Error extracting business info: {e}")
            return None
    
    def _extract_from_details_panel(self, driver) -> Optional[Dict[str, Any]]:
        """
        Extract business information from the Google Maps details panel after clicking on a result
        
        Args:
            driver: Selenium driver
        
        Returns:
            Dictionary with business information or None
        """
        business_data = {
            "name": None,
            "address": None,
            "phone": None,
            "email": None,
            "website": None,
            "rating": None,
            "reviews": None,
            "category": None
        }
        
        try:
            # Wait for details panel to load
            self._human_like_delay(1, 2)
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract name from details panel
            name_selectors = [
                "h1[data-attrid='title']",
                "h1.DUwDvf",
                "h1.qrShPb",
                "div[data-attrid='title']",
                "h1",
            ]
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    name_text = name_elem.get_text(strip=True)
                    if name_text and self._is_valid_business_name(name_text):
                        business_data["name"] = name_text
                        break
            
            # Extract address
            address_selectors = [
                "button[data-item-id='address']",
                "div.Io6YTe.fontBodyMedium",
                "div[data-value='address']",
                "span[data-value='address']",
            ]
            for selector in address_selectors:
                addr_elem = soup.select_one(selector)
                if addr_elem:
                    address_text = addr_elem.get_text(strip=True)
                    if address_text and len(address_text) > 10:  # Address should be reasonably long
                        business_data["address"] = address_text
                        break
            
            # Extract phone - try both button and link
            phone_selectors = [
                "button[data-item-id*='phone']",
                "a[href^='tel:']",
                "span[data-value='phone']",
            ]
            for selector in phone_selectors:
                phone_elem = soup.select_one(selector)
                if phone_elem:
                    phone_text = phone_elem.get_text(strip=True)
                    if phone_text:
                        business_data["phone"] = normalize_phone(phone_text)
                    # Also check href for tel: links
                    href = phone_elem.get('href', '')
                    if href.startswith('tel:'):
                        tel = href.replace('tel:', '').strip()
                        business_data["phone"] = normalize_phone(tel)
                    if business_data["phone"]:
                        break
            
            # Extract website
            website_selectors = [
                "a[data-item-id='authority']",
                "a[aria-label*='Website']",
                "a[aria-label*='website']",
            ]
            for selector in website_selectors:
                website_elem = soup.select_one(selector)
                if website_elem:
                    href = website_elem.get('href', '')
                    if href and ('http://' in href or 'https://' in href):
                        business_data["website"] = href
                        break
            
            # Extract rating
            rating_elem = soup.select_one("span.MW4etd")
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        business_data["rating"] = float(rating_match.group(1))
                    except ValueError:
                        pass
            
            # Extract category/type
            category_elem = soup.select_one("button[jsaction*='pane.category']")
            if category_elem:
                business_data["category"] = category_elem.get_text(strip=True)
            
            # Only return if we have at least a name
            if business_data["name"] and self._is_valid_business_name(business_data["name"]):
                return business_data
            else:
                return None
                
        except Exception as e:
            logger.debug(f"Error extracting from details panel: {e}")
            return None
    
    def _extract_email_from_website(self, website_url: str) -> Optional[str]:
        """
        Extract email from a business website
        
        Args:
            website_url: URL of the business website
        
        Returns:
            Email address if found, None otherwise
        """
        try:
            driver = self._get_driver()
            
            # Navigate to website
            driver.get(website_url)
            self._human_like_delay(2, 3)
            
            # Get page source and extract emails
            page_source = driver.page_source
            emails, _ = extract_contacts(page_source)
            
            if emails:
                # Return the first valid email
                for email in emails:
                    normalized = normalize_email(email)
                    if normalized and len(normalized) > 5:
                        return normalized
            
        except Exception as e:
            logger.debug(f"Error extracting email from {website_url}: {e}")
        
        return None
    
    def _is_valid_business_name(self, name: str) -> bool:
        """
        Validate if a string looks like a real business name
        
        Args:
            name: String to validate
        
        Returns:
            True if it looks like a valid business name, False otherwise
        """
        if not name or len(name) < 2:
            return False
        
        # Filter out UI control text
        ui_keywords = [
            "collapse", "expand", "close", "open", "menu", "filter", "search",
            "rating", "hours", "directions", "save", "share", "more", "less",
            "show", "hide", "view", "edit", "delete", "add", "remove",
            "all filters", "side panel", "collapse side", "expand side",
            "back", "next", "previous", "page", "results", "map"
        ]
        
        name_lower = name.lower()
        for keyword in ui_keywords:
            if keyword in name_lower:
                return False
        
        # Filter out strings that are mostly special characters or numbers
        if len(name) < 3:
            return False
        
        # Should have at least some letters
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        # Should not be just special characters
        if re.match(r'^[\W_]+$', name):
            return False
        
        # Should not be too long (likely concatenated UI elements)
        if len(name) > 200:
            return False
        
        return True
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

