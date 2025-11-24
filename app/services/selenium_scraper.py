"""Selenium-based interactive web scraper for sites that require search interactions"""
import logging
import time
from typing import Dict, Any, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


class SeleniumScraper:
    """Interactive web scraper using Selenium for sites requiring search interactions"""
    
    def __init__(self, headless: bool = True):
        """
        Initialize Selenium scraper
        
        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        self.driver = None
    
    def _get_driver(self):
        """Get or create Chrome driver"""
        if self.driver is None:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
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
            except Exception as e:
                logger.error(f"Failed to create Chrome driver: {e}")
                raise ValueError(f"Chrome driver not available: {e}")
        
        return self.driver
    
    def scrape_with_search(
        self,
        query: str,
        config: Dict[str, Any],
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape a site that requires search interaction
        
        Args:
            query: Search query string
            config: Site configuration with selectors
            max_results: Maximum number of results to return
        
        Config structure:
        {
            "url": "https://example.com",
            "search_box_selector": "input[name='search']",
            "submit_selector": "button.search-submit",  # Optional
            "result_item_selector": ".result-item",
            "fields": {
                "name": ".name",
                "phone": ".phone",
                ...
            },
            "profile_link_selector": ".name a",  # Optional
            "wait_seconds": 5,  # Wait time after search
            "pagination": {  # Optional
                "next_button_selector": ".next-page",
                "max_pages": 3
            }
        }
        
        Returns:
            List of extracted records
        """
        driver = self._get_driver()
        results = []
        
        try:
            # 1. Navigate to site
            url = config.get("url")
            if not url:
                raise ValueError("config.url is required")
            
            logger.info(f"Navigating to {url}")
            driver.get(url)
            time.sleep(2)  # Initial page load
            
            # 2. Find and interact with search box
            search_box_selector = config.get("search_box_selector")
            if not search_box_selector:
                raise ValueError("config.search_box_selector is required")
            
            try:
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, search_box_selector))
                )
            except TimeoutException:
                raise ValueError(f"Search box not found with selector: {search_box_selector}")
            
            # Clear and type query
            search_box.clear()
            search_box.send_keys(query)
            time.sleep(0.5)
            
            # 3. Submit search
            submit_selector = config.get("submit_selector")
            if submit_selector:
                try:
                    submit_btn = driver.find_element(By.CSS_SELECTOR, submit_selector)
                    submit_btn.click()
                except NoSuchElementException:
                    logger.warning(f"Submit button not found, using Enter key")
                    search_box.send_keys(Keys.ENTER)
            else:
                search_box.send_keys(Keys.ENTER)
            
            # 4. Wait for results
            wait_seconds = config.get("wait_seconds", 5)
            time.sleep(wait_seconds)
            
            # 5. Extract results
            result_item_selector = config.get("result_item_selector")
            if not result_item_selector:
                raise ValueError("config.result_item_selector is required")
            
            fields = config.get("fields", {})
            profile_link_selector = config.get("profile_link_selector")
            
            # Handle pagination if configured
            max_pages = 1
            pagination = config.get("pagination")
            if pagination:
                max_pages = pagination.get("max_pages", 1)
            
            for page in range(max_pages):
                if page > 0:
                    # Navigate to next page
                    next_selector = pagination.get("next_button_selector") if pagination else None
                    if next_selector:
                        try:
                            next_btn = driver.find_element(By.CSS_SELECTOR, next_selector)
                            next_btn.click()
                            time.sleep(wait_seconds)
                        except NoSuchElementException:
                            logger.info("No more pages available")
                            break
                    else:
                        break
                
                # Parse current page
                soup = BeautifulSoup(driver.page_source, "html.parser")
                items = soup.select(result_item_selector)
                
                logger.info(f"Found {len(items)} items on page {page + 1}")
                
                for item in items:
                    if max_results and len(results) >= max_results:
                        break
                    
                    record = {}
                    
                    # Extract fields
                    for field_name, selector in fields.items():
                        el = item.select_one(selector)
                        if el:
                            # Try to get text first, then attributes
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
                    
                    # Extract profile link if configured
                    if profile_link_selector:
                        link_el = item.select_one(profile_link_selector)
                        if link_el and link_el.has_attr("href"):
                            href = link_el["href"]
                            # Make absolute URL if relative
                            if href.startswith("/"):
                                from urllib.parse import urljoin
                                record["profile_link"] = urljoin(url, href)
                            else:
                                record["profile_link"] = href
                    
                    # Only add if we got at least one field
                    if any(record.values()):
                        results.append(record)
                
                if max_results and len(results) >= max_results:
                    break
            
            logger.info(f"Extracted {len(results)} total results")
            return results[:max_results] if max_results else results
            
        except Exception as e:
            error_msg = str(e)
            # Check for common blocking patterns
            if "403" in error_msg or "forbidden" in error_msg.lower():
                raise ValueError(
                    "Access forbidden: This website blocks automated scraping. "
                    "Please check the site's Terms of Service and robots.txt. "
                    "Only scrape sites that explicitly allow automated access."
                )
            elif "blocked" in error_msg.lower() or "captcha" in error_msg.lower():
                raise ValueError(
                    "Website blocked automated access (likely detected bot). "
                    "This site may require manual interaction or has anti-bot protection."
                )
            logger.error(f"Error during scraping: {e}", exc_info=True)
            raise
        finally:
            # Don't close driver here - reuse it for multiple calls
            pass
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

