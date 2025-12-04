"""Google Maps scraping API routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.services.google_maps_scraper import GoogleMapsScraper
from app.api.routes_workspaces import get_current_user_optional, get_current_workspace_optional
from app.core.orm import UserORM
from app.core.orm_workspaces import WorkspaceORM

logger = logging.getLogger(__name__)
router = APIRouter()


class GoogleMapsSearchRequest(BaseModel):
    """Request model for Google Maps search"""
    query: str = Field(..., description="Search query (e.g., 'orthopedic doctor', 'find doctor')")
    location: Optional[str] = Field(None, description="Location (e.g., 'New York', 'New York, NY')")
    max_results: int = Field(20, ge=1, le=100, description="Maximum number of results to return")
    headless: bool = Field(True, description="Run browser in headless mode")
    extract_emails: bool = Field(True, description="Extract emails from business websites")


class BusinessInfo(BaseModel):
    """Business information model"""
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    category: Optional[str] = None


class GoogleMapsSearchResponse(BaseModel):
    """Response model for Google Maps search"""
    success: bool
    results: List[BusinessInfo]
    total_found: int
    query: str
    location: Optional[str] = None


@router.post("/google-maps/search", response_model=GoogleMapsSearchResponse)
def search_google_maps(
    request: GoogleMapsSearchRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserORM] = Depends(get_current_user_optional),
    workspace: Optional[WorkspaceORM] = Depends(get_current_workspace_optional),
):
    """
    Search Google Maps for businesses and extract their information
    
    This endpoint searches Google Maps for businesses matching the query and extracts:
    - Business name
    - Address
    - Phone number
    - Email (from website if available)
    - Website URL
    - Rating and reviews
    - Category
    
    ⚠️ IMPORTANT NOTES:
    - This uses web scraping which may violate Google's Terms of Service
    - For production use, consider using the official Google Places API
    - Rate limiting is recommended to avoid being blocked
    - Email extraction requires visiting each business website
    
    Example requests:
    - {"query": "orthopedic doctor", "location": "New York"}
    - {"query": "find doctor", "location": "Los Angeles, CA", "max_results": 50}
    """
    try:
        logger.info(f"Starting Google Maps search: {request.query} in {request.location}")
        
        # Initialize scraper
        scraper = GoogleMapsScraper(headless=request.headless, use_stealth=True)
        
        try:
            # Perform search
            results = scraper.search_places(
                query=request.query,
                location=request.location,
                max_results=request.max_results
            )
            
            # Extract emails from websites if requested
            if request.extract_emails:
                logger.info(f"Extracting emails from {len(results)} business websites...")
                for result in results:
                    if result.get("website") and not result.get("email"):
                        try:
                            email = scraper._extract_email_from_website(result["website"])
                            if email:
                                result["email"] = email
                                logger.info(f"Found email for {result.get('name')}: {email}")
                        except Exception as e:
                            logger.warning(f"Error extracting email from {result.get('website')}: {e}")
            
            # Convert to response models
            business_results = [
                BusinessInfo(
                    name=result.get("name"),
                    address=result.get("address"),
                    phone=result.get("phone"),
                    email=result.get("email"),
                    website=result.get("website"),
                    rating=result.get("rating"),
                    reviews=result.get("reviews"),
                    category=result.get("category")
                )
                for result in results
            ]
            
            return GoogleMapsSearchResponse(
                success=True,
                results=business_results,
                total_found=len(business_results),
                query=request.query,
                location=request.location
            )
            
        finally:
            # Clean up scraper
            scraper.close()
    
    except ValueError as e:
        logger.error(f"Validation error in Google Maps search: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during Google Maps search: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search Google Maps: {str(e)}"
        )


@router.get("/google-maps/health")
def google_maps_health():
    """
    Health check endpoint for Google Maps scraper
    
    Tests if the scraper can initialize successfully
    """
    try:
        scraper = GoogleMapsScraper(headless=True, use_stealth=True)
        scraper._get_driver()
        scraper.close()
        return {
            "status": "healthy",
            "message": "Google Maps scraper is ready"
        }
    except Exception as e:
        logger.error(f"Google Maps scraper health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Google Maps scraper initialization failed: {str(e)}"
        }

