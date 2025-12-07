"""Basic web search source that works without API keys (fallback)"""
from typing import Iterable, Optional
from urllib.parse import quote_plus
import requests
from app.core.models import Lead
from app.sources.base import SourceBase
from app.utils.http import make_request


class BasicWebSearchSource(SourceBase):
    """Basic web search source using direct HTML scraping (no API key required)"""
    
    def __init__(self):
        """Initialize basic web search source (always works, no API key needed)"""
        pass
    
    def search(self, niche: str, location: Optional[str] = None) -> Iterable[Lead]:
        """Search for businesses using basic web search (DuckDuckGo or similar)"""
        try:
            # Use DuckDuckGo HTML search (no API key required)
            query = f"{niche} in {location}" if location else niche
            encoded_query = quote_plus(query)
            
            # DuckDuckGo search URL
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = make_request(search_url, headers=headers, timeout=10)
            if not response:
                return
            
            # Parse HTML to extract results
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find result links (try multiple selectors for different search engines)
            results = []
            # Try DuckDuckGo structure
            results = soup.find_all('a', class_='result__a', limit=20)
            if not results:
                # Try alternative selectors
                results = soup.find_all('a', {'class': 'web-result'}, limit=20)
            if not results:
                # Try generic result links
                results = soup.select('a[href*="http"]', limit=20)
            
            # Parse location
            city, country = None, None
            if location:
                from app.utils.geo import parse_location
                city, country = parse_location(location)
            
            for result in results:
                try:
                    title = result.get_text(strip=True)
                    url = result.get('href', '')
                    
                    if not url or not title:
                        continue
                    
                    # Extract domain from URL
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    domain = parsed.netloc.replace('www.', '')
                    
                    if not domain:
                        continue
                    
                    # Create lead
                    lead = Lead(
                        name=title,
                        niche=niche,
                        website=url,
                        source="basic_web_search",
                        city=city,
                        country=country,
                    )
                    
                    yield lead
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            # If basic search fails, return empty (silent fail)
            return

