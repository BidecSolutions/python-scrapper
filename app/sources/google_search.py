"""Google Custom Search API source"""
import os
from typing import Iterable, Optional
import httpx
from app.core.models import Lead
from app.core.config import settings
from app.sources.base import SourceBase
import logging

logger = logging.getLogger(__name__)

GOOGLE_SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"


class GoogleSearchSource(SourceBase):
    """Source for leads from Google Custom Search API"""
    
    def __init__(self, api_key: Optional[str] = None, cx: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_SEARCH_API_KEY
        self.cx = cx or settings.GOOGLE_SEARCH_CX
        
        if not self.api_key:
            raise ValueError("GOOGLE_SEARCH_API_KEY is required")
        if not self.cx:
            raise ValueError("GOOGLE_SEARCH_CX is required")
    
    def search(self, niche: str, location: Optional[str] = None) -> Iterable[Lead]:
        """Search for businesses using Google Custom Search API"""
        query = f"{niche} {location}" if location else niche
        
        per_page = 10
        max_results = 100  # Google Custom Search API limit
        start_index = 1
        
        # Use sync httpx client since this is called from sync context
        with httpx.Client(timeout=20.0) as client:
            while start_index <= 91:  # Google API max start index
                params = {
                    "key": self.api_key,
                    "cx": self.cx,
                    "q": query,
                    "start": start_index,
                    "num": per_page,
                }
                
                try:
                    response = client.get(GOOGLE_SEARCH_API_URL, params=params)
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPError as e:
                    logger.error(f"Google Search API error: {e}")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in Google Search: {e}")
                    break
                
                items = data.get("items", [])
                if not items:
                    break
                
                # Parse location
                city, country = None, None
                if location:
                    from app.utils.geo import parse_location
                    city, country = parse_location(location)
                
                for item in items:
                    link = item.get("link")
                    title = item.get("title", "")
                    
                    if not link:
                        continue
                    
                    # Extract snippet for potential address parsing
                    snippet = item.get("snippet", "")
                    
                    yield Lead(
                        id=None,
                        name=title,
                        niche=niche,
                        website=link,
                        emails=[],
                        phones=[],
                        address=None,  # Could parse from snippet if needed
                        source="google_search",
                        city=city,
                        country=country,
                    )
                
                # Check if there are more results
                if start_index + len(items) > max_results:
                    break
                
                start_index += len(items)
                
                # Check if there's a next page
                if len(items) < per_page:
                    break

