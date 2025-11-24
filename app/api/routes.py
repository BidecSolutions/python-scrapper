"""FastAPI routes"""
from fastapi import APIRouter, Depends
from typing import List
from app.api.schemas import ScrapeRequest, ScrapeResponse, LeadOut
from app.core.models import Lead
from app.scraper.crawler import SimpleCrawler
from app.scraper.async_crawler import AsyncCrawler
from app.services.lead_service import LeadService
from app.services.async_lead_service import AsyncLeadService
from app.sources.google_places import GooglePlacesSource
from app.sources.web_search import WebSearchSource

router = APIRouter()


def get_lead_service(req: ScrapeRequest) -> LeadService:
    """Create a lead service instance for sync operations"""
    sources = []
    
    # Add Google Places if API key is available
    try:
        sources.append(GooglePlacesSource())
    except ValueError:
        pass  # No API key, skip
    
    # Add Web Search if API key is available
    try:
        sources.append(WebSearchSource())
    except Exception:
        pass
    
    crawler = SimpleCrawler(max_pages=req.max_pages_per_site)
    return LeadService(sources=sources, crawler=crawler)


@router.post("/scrape", response_model=ScrapeResponse)
def scrape_leads(payload: ScrapeRequest) -> ScrapeResponse:
    """Synchronous endpoint for scraping leads"""
    service = get_lead_service(payload)
    leads: List[Lead] = service.search_leads(
        niche=payload.niche,
        location=payload.location,
        max_results=payload.max_results,
    )

    lead_out = [
        LeadOut(
            name=l.name,
            niche=l.niche,
            website=l.website,
            emails=l.emails,
            phones=l.phones,
            address=l.address,
            source=l.source,
            city=l.city,
            country=l.country,
        )
        for l in leads
    ]
    return ScrapeResponse(total=len(lead_out), leads=lead_out)


@router.post("/scrape-async", response_model=ScrapeResponse)
async def scrape_leads_async(payload: ScrapeRequest) -> ScrapeResponse:
    """Asynchronous endpoint for scraping leads"""
    sources = []
    
    # Add Google Places if API key is available
    try:
        sources.append(GooglePlacesSource())
    except ValueError:
        pass  # No API key, skip
    
    # Add Web Search if API key is available
    try:
        sources.append(WebSearchSource())
    except Exception:
        pass
    
    crawler = AsyncCrawler(max_pages=payload.max_pages_per_site)
    service = AsyncLeadService(sources=sources, crawler=crawler)

    leads: List[Lead] = await service.search_leads(
        niche=payload.niche,
        location=payload.location,
        max_results=payload.max_results,
    )

    lead_out = [
        LeadOut(
            name=l.name,
            niche=l.niche,
            website=l.website,
            emails=l.emails,
            phones=l.phones,
            address=l.address,
            source=l.source,
            city=l.city,
            country=l.country,
        )
        for l in leads
    ]
    return ScrapeResponse(total=len(lead_out), leads=lead_out)

