"""
LinkedIn Profile Scraper using Playwright
Uses browser automation to scrape LinkedIn profiles more reliably
"""
import logging
import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
import re

logger = logging.getLogger(__name__)


class LinkedInPlaywrightScraper:
    """Scrape LinkedIn profiles using Playwright browser automation"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the scraper
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self._playwright = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    async def scrape_profile(self, profile_url: str, wait_for_js: bool = True) -> Dict[str, Any]:
        """
        Scrape a LinkedIn profile page
        
        Args:
            profile_url: Full LinkedIn profile URL (e.g., https://www.linkedin.com/in/username/)
            wait_for_js: Wait for JavaScript to load content
        
        Returns:
            Dictionary with extracted profile data
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use async context manager.")
        
        # Clean and validate URL
        profile_url = self._clean_profile_url(profile_url)
        if not profile_url:
            raise ValueError(f"Invalid LinkedIn profile URL: {profile_url}")
        
        # Create a new page with realistic browser settings
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to profile page
            logger.info(f"Navigating to LinkedIn profile: {profile_url}")
            await page.goto(profile_url, wait_until='networkidle', timeout=self.timeout)
            
            # Wait for main content to load
            if wait_for_js:
                # Wait for profile header to appear
                try:
                    await page.wait_for_selector('h1', timeout=10000)
                except PlaywrightTimeoutError:
                    logger.warning("Profile header not found, continuing anyway")
            
            # Extract profile data
            profile_data = await self._extract_profile_data(page)
            
            return profile_data
            
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout loading profile {profile_url}: {e}")
            raise Exception(f"Timeout loading LinkedIn profile: {str(e)}")
        except Exception as e:
            logger.error(f"Error scraping profile {profile_url}: {e}")
            raise
        finally:
            await context.close()
    
    def _clean_profile_url(self, url: str) -> Optional[str]:
        """Clean and validate LinkedIn profile URL"""
        if not url:
            return None
        
        # Remove query parameters
        url = url.split('?')[0]
        
        # Remove overlay paths
        if '/overlay/' in url:
            match = re.match(r'(https?://[^/]+/in/[^/]+)', url)
            if match:
                url = match.group(1)
            else:
                return None
        
        # Validate it's a profile URL
        if not re.match(r'https?://(www\.)?linkedin\.com/in/[^/]+/?$', url):
            return None
        
        # Ensure no trailing slash
        url = url.rstrip('/')
        
        return url
    
    async def _extract_profile_data(self, page: Page) -> Dict[str, Any]:
        """Extract profile data from the page"""
        data = {
            'full_name': None,
            'first_name': None,
            'last_name': None,
            'headline': None,
            'company_name': None,
            'location': None,
            'about': None,
            'experience': [],
            'education': [],
            'skills': [],
            'linkedin_url': page.url,
        }
        
        try:
            # Extract name - try multiple selectors
            name_selectors = [
                'h1.text-heading-xlarge',
                'h1[class*="text-heading"]',
                '.pv-text-details__left-panel h1',
                '.top-card-layout__title',
                'main h1',
                'h1',
            ]
            
            for selector in name_selectors:
                name_element = await page.query_selector(selector)
                if name_element:
                    full_name = await name_element.inner_text()
                    full_name = full_name.strip()
                    if full_name and len(full_name) > 2:
                        data['full_name'] = full_name
                        # Split name
                        parts = full_name.split()
                        if parts:
                            data['first_name'] = parts[0]
                            data['last_name'] = ' '.join(parts[1:]) if len(parts) > 1 else ''
                        break
            
            # Extract headline
            headline_selectors = [
                '.text-body-medium.break-words',
                '.pv-text-details__left-panel .text-body-medium',
                '.top-card-layout__headline',
                '[data-test-id="headline"]',
            ]
            
            for selector in headline_selectors:
                headline_element = await page.query_selector(selector)
                if headline_element:
                    headline = await headline_element.inner_text()
                    headline = headline.strip()
                    if headline:
                        data['headline'] = headline
                        break
            
            # Extract location
            location_selectors = [
                '.text-body-small.inline.t-black--light.break-words',
                '.pv-text-details__left-panel .text-body-small',
                '[data-test-id="location"]',
            ]
            
            for selector in location_selectors:
                location_element = await page.query_selector(selector)
                if location_element:
                    location = await location_element.inner_text()
                    location = location.strip()
                    # Filter out "connections" text
                    if location and 'connection' not in location.lower() and len(location) < 100:
                        data['location'] = location
                        break
            
            # Extract company (from current position)
            company_selectors = [
                '.pv-text-details__left-panel .text-body-medium',
                '.pv-entity__secondary-title',
                '.experience-section .pv-entity__summary-info h3',
            ]
            
            for selector in company_selectors:
                company_element = await page.query_selector(selector)
                if company_element:
                    company = await company_element.inner_text()
                    company = company.strip()
                    if company:
                        data['company_name'] = company
                        break
            
            # Extract About section
            about_selectors = [
                '.pv-about-section .pv-about__summary-text',
                '.about-section .text-body-medium',
                '[data-test-id="about-section"]',
            ]
            
            for selector in about_selectors:
                about_element = await page.query_selector(selector)
                if about_element:
                    about = await about_element.inner_text()
                    about = about.strip()
                    if about:
                        data['about'] = about
                        break
            
            # Extract experience (simplified - just current)
            experience_elements = await page.query_selector_all('.experience-section .pv-entity__summary-info')
            for exp_element in experience_elements[:3]:  # Limit to first 3
                try:
                    title_element = await exp_element.query_selector('h3')
                    company_element = await exp_element.query_selector('.pv-entity__secondary-title')
                    
                    if title_element:
                        title = await title_element.inner_text()
                        company = ''
                        if company_element:
                            company = await company_element.inner_text()
                        
                        data['experience'].append({
                            'title': title.strip(),
                            'company': company.strip(),
                        })
                except Exception as e:
                    logger.debug(f"Error extracting experience: {e}")
            
            logger.info(f"Successfully extracted profile data for: {data.get('full_name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
            # Return partial data if available
        
        return data
    
    async def scrape_multiple_profiles(self, profile_urls: list[str], delay: float = 2.0) -> list[Dict[str, Any]]:
        """
        Scrape multiple LinkedIn profiles with delays to avoid rate limiting
        
        Args:
            profile_urls: List of LinkedIn profile URLs
            delay: Delay between requests in seconds
        
        Returns:
            List of extracted profile data dictionaries
        """
        results = []
        
        for i, url in enumerate(profile_urls):
            try:
                logger.info(f"Scraping profile {i+1}/{len(profile_urls)}: {url}")
                profile_data = await self.scrape_profile(url)
                results.append(profile_data)
                
                # Add delay between requests (except for last one)
                if i < len(profile_urls) - 1:
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                results.append({
                    'linkedin_url': url,
                    'error': str(e),
                    'success': False
                })
        
        return results


# Convenience function for synchronous use
async def scrape_linkedin_profile(profile_url: str, headless: bool = True) -> Dict[str, Any]:
    """
    Convenience function to scrape a single LinkedIn profile
    
    Args:
        profile_url: LinkedIn profile URL
        headless: Run browser in headless mode
    
    Returns:
        Dictionary with extracted profile data
    """
    async with LinkedInPlaywrightScraper(headless=headless) as scraper:
        return await scraper.scrape_profile(profile_url)

