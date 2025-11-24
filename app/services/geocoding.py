"""Geocoding service using OpenCage and other providers"""
import os
import logging
import requests
from typing import Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# OpenCage configuration
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY", "")
OPENCAGE_URL = "https://api.opencagedata.com/geocode/v1/json"

# Google Geocoding (optional, for premium features)
GOOGLE_GEOCODING_API_KEY = os.getenv("GOOGLE_GEOCODING_API_KEY", "")
GOOGLE_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"


class GeocodingError(Exception):
    """Geocoding service error"""
    pass


def _call_opencage(query: str) -> Dict[str, Any]:
    """Call OpenCage geocoding API"""
    if not OPENCAGE_API_KEY:
        raise GeocodingError("OPENCAGE_API_KEY not configured")
    
    try:
        resp = requests.get(
            OPENCAGE_URL,
            params={
                "q": query,
                "key": OPENCAGE_API_KEY,
                "limit": 1,
                "no_annotations": 1,
            },
            timeout=10,
        )
        
        if resp.status_code != 200:
            raise GeocodingError(f"OpenCage error: {resp.status_code} {resp.text[:200]}")
        
        data = resp.json()
        
        if not data.get("results"):
            raise GeocodingError("No results found")
        
        return data["results"][0]
    except requests.RequestException as e:
        raise GeocodingError(f"Request failed: {str(e)}")


def _normalize_opencage_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize OpenCage result to standard format"""
    geom = result.get("geometry", {})
    components = result.get("components", {})
    
    return {
        "lat": geom.get("lat"),
        "lng": geom.get("lng"),
        "city": (
            components.get("city")
            or components.get("town")
            or components.get("village")
            or components.get("municipality")
        ),
        "state": components.get("state") or components.get("state_district"),
        "country": components.get("country"),
        "country_code": components.get("country_code", "").upper(),
        "formatted": result.get("formatted"),
        "postcode": components.get("postcode"),
    }


def _call_google_geocoding(query: str) -> Dict[str, Any]:
    """Call Google Geocoding API (optional, premium)"""
    if not GOOGLE_GEOCODING_API_KEY:
        raise GeocodingError("GOOGLE_GEOCODING_API_KEY not configured")
    
    try:
        resp = requests.get(
            GOOGLE_GEOCODING_URL,
            params={
                "address": query,
                "key": GOOGLE_GEOCODING_API_KEY,
            },
            timeout=10,
        )
        
        if resp.status_code != 200:
            raise GeocodingError(f"Google error: {resp.status_code}")
        
        data = resp.json()
        
        if data.get("status") != "OK" or not data.get("results"):
            raise GeocodingError(f"Google status: {data.get('status')}")
        
        result = data["results"][0]
        geom = result.get("geometry", {}).get("location", {})
        components = {}
        
        for component in result.get("address_components", []):
            types = component.get("types", [])
            if "locality" in types:
                components["city"] = component.get("long_name")
            elif "administrative_area_level_1" in types:
                components["state"] = component.get("long_name")
            elif "country" in types:
                components["country"] = component.get("long_name")
                components["country_code"] = component.get("short_name", "").upper()
            elif "postal_code" in types:
                components["postcode"] = component.get("long_name")
        
        return {
            "lat": geom.get("lat"),
            "lng": geom.get("lng"),
            "city": components.get("city"),
            "state": components.get("state"),
            "country": components.get("country"),
            "country_code": components.get("country_code", ""),
            "formatted": result.get("formatted_address"),
            "postcode": components.get("postcode"),
        }
    except requests.RequestException as e:
        raise GeocodingError(f"Google request failed: {str(e)}")


@lru_cache(maxsize=10000)
def geocode_text(query: str, use_google: bool = False) -> Dict[str, Any]:
    """
    Geocode a text query (address, city name, etc.)
    
    Args:
        query: Address or location string
        use_google: If True and Google key available, use Google instead of OpenCage
    
    Returns:
        Dict with lat, lng, city, state, country, country_code, formatted, postcode
    """
    if not query or len(query.strip()) < 2:
        raise GeocodingError("Query too short")
    
    query = query.strip()
    
    # Try Google first if requested and available
    if use_google and GOOGLE_GEOCODING_API_KEY:
        try:
            return _call_google_geocoding(query)
        except GeocodingError as e:
            logger.warning(f"Google geocoding failed, falling back to OpenCage: {e}")
            # Fall through to OpenCage
    
    # Use OpenCage as primary/fallback
    result = _call_opencage(query)
    return _normalize_opencage_result(result)


def geocode_address(
    address: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    use_google: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Geocode an address from components
    
    Args:
        address: Street address
        city: City name
        country: Country name
        use_google: Use Google if available
    
    Returns:
        Geocoded result or None if failed
    """
    # Build query string
    query_parts = []
    if address:
        query_parts.append(address)
    if city:
        query_parts.append(city)
    if country:
        query_parts.append(country)
    
    if not query_parts:
        return None
    
    query = ", ".join(query_parts)
    
    try:
        return geocode_text(query, use_google=use_google)
    except GeocodingError as e:
        logger.error(f"Geocoding failed for '{query}': {e}")
        return None


def reverse_geocode(lat: float, lng: float) -> Optional[Dict[str, Any]]:
    """
    Reverse geocode: lat/lng -> address
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Address components or None if failed
    """
    query = f"{lat},{lng}"
    
    try:
        return geocode_text(query)
    except GeocodingError as e:
        logger.error(f"Reverse geocoding failed for {lat},{lng}: {e}")
        return None

