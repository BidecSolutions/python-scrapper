"""Web search source using Bing Search API"""
from typing import Iterable, Optional
from urllib.parse import urlparse
import requests
from app.core.models import Lead
from app.core.config import settings
from app.sources.base import SourceBase
from app.utils.http import make_request


class WebSearchSource(SourceBase):
    """Source for leads from web search (Bing API)"""
    
    BASE_URL = "https://api.bing.microsoft.com/v7.0/search"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.BING_SEARCH_API_KEY
        if not self.api_key:
            # If no API key, this source won't work but won't crash
            pass
    
    def search(self, niche: str, location: Optional[str] = None) -> Iterable[Lead]:
        """Search for businesses using Bing Search API"""
        if not self.api_key:
            return  # Skip if no API key
        
        query = f"{niche} in {location}" if location else niche
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        
        params = {
            "q": query,
            "count": 50,  # Max results per page
            "mkt": "en-US",
        }
        
        response = make_request(self.BASE_URL, params=params, headers=headers)
        if not response:
            return
        
        try:
            data = response.json()
        except ValueError:
            return
        
        web_pages = data.get("webPages", {}).get("value", [])
        
        # Parse location
        city, country = None, None
        if location:
            from app.utils.geo import parse_location
            city, country = parse_location(location)
        
        for page in web_pages:
            url = page.get("url")
            name = page.get("name")
            
            # Extract domain as a simple name if no name
            if not name and url:
                parsed = urlparse(url)
                name = parsed.netloc.replace("www.", "")
            
            yield Lead(
                id=None,
                name=name,
                niche=niche,
                website=url,
                emails=[],
                phones=[],
                address=None,
                source="web_search",
                city=city,
                country=country,
            )

