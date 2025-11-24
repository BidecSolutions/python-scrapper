"""Google Places API source"""
import os
from typing import Iterable, Optional
import requests
from app.core.models import Lead
from app.core.config import settings
from app.sources.base import SourceBase
from app.utils.http import make_request
import time


class GooglePlacesSource(SourceBase):
    """Source for leads from Google Places API"""
    
    BASE_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_PLACES_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY is required")
    
    def search(self, niche: str, location: Optional[str] = None) -> Iterable[Lead]:
        """Search for businesses using Google Places API"""
        query = f"{niche} in {location}" if location else niche
        
        params = {
            "query": query,
            "key": self.api_key,
        }
        
        url = self.BASE_URL
        
        while True:
            response = make_request(url, params=params)
            if not response:
                break
            
            try:
                data = response.json()
            except ValueError:
                break
            
            if data.get("status") != "OK":
                break
            
            for result in data.get("results", []):
                # Get place details for website
                website = None
                place_id = result.get("place_id")
                if place_id:
                    website = self._get_website(place_id)
                
                # Parse location
                city, country = None, None
                if location:
                    from app.utils.geo import parse_location
                    city, country = parse_location(location)
                
                yield Lead(
                    id=None,
                    name=result.get("name"),
                    niche=niche,
                    website=website,
                    emails=[],
                    phones=[],
                    address=result.get("formatted_address"),
                    source="google_places",
                    city=city,
                    country=country,
                )
            
            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break
            
            # Google requires a delay before using next_page_token
            time.sleep(2)
            
            params = {
                "pagetoken": next_page_token,
                "key": self.api_key,
            }
    
    def _get_website(self, place_id: str) -> Optional[str]:
        """Get website URL for a place using Place Details API"""
        params = {
            "place_id": place_id,
            "fields": "website",
            "key": self.api_key,
        }
        
        response = make_request(self.DETAILS_URL, params=params)
        if not response:
            return None
        
        try:
            data = response.json()
            if data.get("status") == "OK":
                result = data.get("result", {})
                return result.get("website")
        except ValueError:
            pass
        
        return None

