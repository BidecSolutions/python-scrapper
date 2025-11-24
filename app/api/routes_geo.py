"""Geocoding API endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from app.services.geocoding import geocode_text, geocode_address, reverse_geocode, GeocodingError

router = APIRouter()


@router.get("/geo/search")
def search_location(
    q: str = Query(..., min_length=2, description="Location query string"),
    use_google: bool = Query(False, description="Use Google Geocoding if available"),
):
    """Search and geocode a location"""
    try:
        result = geocode_text(q, use_google=use_google)
        return {"result": result}
    except GeocodingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")


@router.get("/geo/reverse")
def reverse_geocode_endpoint(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """Reverse geocode: lat/lng -> address"""
    try:
        result = reverse_geocode(lat, lng)
        if not result:
            raise HTTPException(status_code=404, detail="No address found")
        return {"result": result}
    except GeocodingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reverse geocoding failed: {str(e)}")

