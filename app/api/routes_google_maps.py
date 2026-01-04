"""Google Maps scraping API routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.services.google_maps_scraper import GoogleMapsScraper
from app.sources.google_places import GooglePlacesSource
from app.core.config import settings
from app.api.routes_workspaces import get_current_user_optional, get_current_workspace_optional
from app.core.orm import UserORM
from app.core.orm_workspaces import WorkspaceORM
from app.core.orm import LeadORM, LeadStatus
from app.api.routes_settings import get_or_create_default_org
from app.utils.geo import parse_location
from app.utils.http import make_request
from app.scraper.extractor import extract_from_soup
from app.scraper.normalizer import normalize_emails, normalize_phones
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
from app.core.db import SessionLocal
from app.core.models import Lead as LeadModel
from app.services.enrichment_service import EnrichmentService
from fastapi.responses import Response

logger = logging.getLogger(__name__)
router = APIRouter()


class GoogleMapsSearchRequest(BaseModel):
    """Request model for Google Maps search"""
    query: str = Field(..., description="Search query (e.g., 'orthopedic doctor', 'find doctor')")
    location: Optional[str] = Field(None, description="Location (e.g., 'New York', 'New York, NY')")
    max_results: int = Field(20, ge=1, le=100, description="Maximum number of results to return")
    headless: bool = Field(True, description="Run browser in headless mode (recommended on servers)")
    extract_emails: bool = Field(True, description="Extract emails from business websites")
    use_places_api: bool = Field(False, description="Use Google Places API instead of scraping (requires API key)")
    aggressive_scroll: bool = Field(True, description="Retry scrolling to collect more results")
    debug_keep_browser_open: bool = Field(
        False,
        description="Debug only: keep the Chrome window open after the request (leaks a process).",
    )


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
    open_status: Optional[str] = None


class GoogleMapsSearchResponse(BaseModel):
    """Response model for Google Maps search"""
    success: bool
    results: List[BusinessInfo]
    total_found: int
    query: str
    location: Optional[str] = None


class GoogleMapsImportItem(BaseModel):
    name: Optional[str] = None
    detail_url: str
    place_key: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    rating: Optional[float] = None
    reviews: Optional[int] = None
    meta_line: Optional[str] = None
    collected_at: Optional[str] = None


class GoogleMapsImportRequest(BaseModel):
    items: List[GoogleMapsImportItem]
    niche: Optional[str] = None
    location: Optional[str] = None


class GoogleMapsImportResponse(BaseModel):
    success: bool
    imported: int
    updated: int
    skipped: int
    lead_ids: List[int]


class ExtractContactsRequest(BaseModel):
    url: str


class ExtractContactsResponse(BaseModel):
    emails: List[str]
    phones: List[str]


class RecentImportedLead(BaseModel):
    id: int
    name: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None


class EnrichLeadsRequest(BaseModel):
    lead_ids: List[int] = Field(..., min_items=1)
    emails: bool = True
    phones: bool = True
    social_links: bool = True


class EnrichLeadsResponse(BaseModel):
    queued: int
    skipped: int
    lead_ids: List[int]


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
            # Perform search via scraper
            results = scraper.search_places(
                query=request.query,
                location=request.location,
                max_results=request.max_results,
                aggressive_scroll=request.aggressive_scroll,
            )

            # Optional fallback to Places API when scraping is thin
            should_use_places_api = request.use_places_api or (
                len(results) < request.max_results and settings.GOOGLE_PLACES_API_KEY
            )
            if should_use_places_api:
                try:
                    places_source = GooglePlacesSource(settings.GOOGLE_PLACES_API_KEY)
                    seen = {(r.get("name"), r.get("address")) for r in results}
                    for lead in places_source.search(request.query, request.location):
                        key = (lead.name, lead.address)
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append({
                            "name": lead.name,
                            "address": lead.address,
                            "phone": None,
                            "email": None,
                            "website": lead.website,
                            "rating": None,
                            "reviews": None,
                            "category": None,
                        })
                        if len(results) >= request.max_results:
                            break
                    logger.info("Places API fallback added %s results", len(results))
                except Exception as e:
                    logger.warning("Places API fallback failed: %s", e)
            
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
                        finally:
                            scraper._cooldown(1.5)
            
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
                    category=result.get("category"),
                    open_status=result.get("open_status")
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
            # Clean up scraper (unless debugging)
            if request.debug_keep_browser_open:
                logger.warning("debug_keep_browser_open=true; leaving Chrome running for inspection.")
            else:
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


@router.post("/google-maps/import", response_model=GoogleMapsImportResponse)
def import_google_maps_results(
    request: GoogleMapsImportRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserORM] = Depends(get_current_user_optional),
    workspace: Optional[WorkspaceORM] = Depends(get_current_workspace_optional),
):
    """
    Import Google Maps results captured by the Chrome extension as Leads.

    This is intended for user-driven collection (you scroll in Google Maps, then import).
    """
    org = get_or_create_default_org(db)
    city, country = (None, None)
    if request.location:
        city, country = parse_location(request.location)

    imported = 0
    updated = 0
    skipped = 0
    lead_ids: List[int] = []

    for item in request.items:
        # Deduplicate by website (business website if available, else maps URL)
        dedupe_website = item.website or item.detail_url
        existing = db.query(LeadORM).filter(
            LeadORM.organization_id == org.id,
            LeadORM.website == dedupe_website,
        ).first()
        if existing:
            changed = False
            if not existing.name and item.name:
                existing.name = item.name
                changed = True
            if not existing.niche and request.niche:
                existing.niche = request.niche
                changed = True
            if not existing.address and item.address:
                existing.address = item.address
                changed = True
            if (not existing.city and city) or (not existing.country and country):
                existing.city = existing.city or city
                existing.country = existing.country or country
                changed = True

            existing_emails = set(existing.emails or [])
            incoming_emails = set(item.emails or [])
            merged_emails = sorted(existing_emails | incoming_emails)
            if merged_emails != (existing.emails or []):
                existing.emails = merged_emails
                changed = True

            existing_phones = set(existing.phones or [])
            if item.phone:
                existing_phones.add(item.phone)
            merged_phones = sorted(existing_phones)
            if merged_phones != (existing.phones or []):
                existing.phones = merged_phones
                changed = True

            meta = dict(existing.meta or {})
            meta.setdefault("google_maps_url", item.detail_url)
            if item.place_key:
                meta["google_maps_place_key"] = item.place_key
            if item.rating is not None:
                meta["google_maps_rating"] = item.rating
            if item.reviews is not None:
                meta["google_maps_reviews"] = item.reviews
            if item.meta_line:
                meta["google_maps_meta_line"] = item.meta_line
            if item.collected_at:
                meta["google_maps_collected_at"] = item.collected_at
            if item.website:
                meta["google_maps_business_website"] = item.website
            if meta != (existing.meta or {}):
                existing.meta = meta
                changed = True

            if changed:
                updated += 1
                lead_ids.append(existing.id)
            else:
                skipped += 1
            continue

        meta: dict[str, Any] = {
            "google_maps_url": item.detail_url,
            "google_maps_place_key": item.place_key,
            "google_maps_rating": item.rating,
            "google_maps_reviews": item.reviews,
            "google_maps_meta_line": item.meta_line,
            "google_maps_collected_at": item.collected_at,
            "google_maps_business_website": item.website,
        }

        lead = LeadORM(
            organization_id=org.id,
            workspace_id=workspace.id if workspace else None,
            name=item.name,
            niche=request.niche,
            website=dedupe_website,
            address=item.address,
            emails=item.emails or [],
            phones=[item.phone] if item.phone else [],
            city=city,
            country=country,
            source="google_maps_extension",
            sources=["google_maps_extension"],
            status=LeadStatus.new,
            meta=meta,
        )
        db.add(lead)
        db.flush()
        lead_ids.append(lead.id)
        imported += 1

    db.commit()

    return GoogleMapsImportResponse(
        success=True,
        imported=imported,
        updated=updated,
        skipped=skipped,
        lead_ids=lead_ids,
    )


@router.post("/google-maps/extract-contacts", response_model=ExtractContactsResponse)
def extract_contacts_from_website(payload: ExtractContactsRequest):
    """
    Fetch a public website and extract emails/phones from its HTML.

    Used by the Chrome extension to enrich Google Maps results with email addresses.
    """
    parsed = urlparse(payload.url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only http/https URLs are allowed")
    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid URL")

    resp = make_request(payload.url)
    if not resp:
        raise HTTPException(status_code=400, detail="Failed to fetch URL")

    soup = BeautifulSoup(resp.text, "html.parser")
    emails_set, phones_set = extract_from_soup(soup)
    emails = normalize_emails(list(emails_set))
    phones = normalize_phones(list(phones_set))
    return ExtractContactsResponse(emails=emails, phones=phones)


@router.get("/google-maps/imports/recent", response_model=List[RecentImportedLead])
def list_recent_google_maps_imports(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Optional[UserORM] = Depends(get_current_user_optional),
    workspace: Optional[WorkspaceORM] = Depends(get_current_workspace_optional),
):
    org = get_or_create_default_org(db)
    q = db.query(LeadORM).filter(
        LeadORM.organization_id == org.id,
        LeadORM.source == "google_maps_extension",
    )
    if workspace:
        q = q.filter(LeadORM.workspace_id == workspace.id)
    leads = q.order_by(LeadORM.created_at.desc()).limit(min(limit, 200)).all()
    return [
        RecentImportedLead(
            id=lead.id,
            name=lead.name,
            website=lead.website,
            address=lead.address,
            emails=lead.emails or [],
            phones=lead.phones or [],
            created_at=lead.created_at.isoformat() if lead.created_at else None,
        )
        for lead in leads
    ]


@router.get("/google-maps/imports/export/csv")
def export_recent_google_maps_imports_csv(
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: Optional[UserORM] = Depends(get_current_user_optional),
    workspace: Optional[WorkspaceORM] = Depends(get_current_workspace_optional),
):
    org = get_or_create_default_org(db)
    q = db.query(LeadORM).filter(
        LeadORM.organization_id == org.id,
        LeadORM.source == "google_maps_extension",
    )
    if workspace:
        q = q.filter(LeadORM.workspace_id == workspace.id)
    leads = q.order_by(LeadORM.created_at.desc()).limit(min(limit, 10000)).all()

    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "address", "phone", "emails", "website", "created_at"])
    for lead in leads:
        writer.writerow(
            [
                lead.id,
                lead.name or "",
                lead.address or "",
                "; ".join(lead.phones or []),
                "; ".join(lead.emails or []),
                lead.website or "",
                lead.created_at.isoformat() if lead.created_at else "",
            ]
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=google-maps-imports.csv"},
    )


@router.get("/google-maps/imports/export/xlsx")
def export_recent_google_maps_imports_xlsx(
    limit: int = 5000,
    db: Session = Depends(get_db),
    current_user: Optional[UserORM] = Depends(get_current_user_optional),
    workspace: Optional[WorkspaceORM] = Depends(get_current_workspace_optional),
):
    org = get_or_create_default_org(db)
    q = db.query(LeadORM).filter(
        LeadORM.organization_id == org.id,
        LeadORM.source == "google_maps_extension",
    )
    if workspace:
        q = q.filter(LeadORM.workspace_id == workspace.id)
    leads = q.order_by(LeadORM.created_at.desc()).limit(min(limit, 20000)).all()

    try:
        from openpyxl import Workbook
    except Exception:
        raise HTTPException(status_code=500, detail="openpyxl not installed")

    wb = Workbook()
    ws = wb.active
    ws.title = "Google Maps Imports"
    ws.append(["id", "name", "address", "phone", "emails", "website", "created_at"])
    for lead in leads:
        ws.append(
            [
                lead.id,
                lead.name or "",
                lead.address or "",
                "; ".join(lead.phones or []),
                "; ".join(lead.emails or []),
                lead.website or "",
                lead.created_at.isoformat() if lead.created_at else "",
            ]
        )

    import io

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=google-maps-imports.xlsx"},
    )


def _is_http_url(value: Optional[str]) -> bool:
    if not value:
        return False
    try:
        u = urlparse(value)
        return u.scheme in {"http", "https"} and bool(u.netloc)
    except Exception:
        return False


def _enrich_lead_contacts_task(lead_id: int, emails: bool, phones: bool, social_links: bool) -> None:
    db = SessionLocal()
    try:
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return

        meta = dict(lead.meta or {})
        target_url = meta.get("google_maps_business_website") or lead.website
        if not _is_http_url(target_url) or "google.com/maps" in target_url:
            return

        resp = make_request(target_url)
        if not resp:
            return

        soup = BeautifulSoup(resp.text, "html.parser")
        emails_set, phones_set = extract_from_soup(soup)
        new_emails = normalize_emails(list(emails_set)) if emails else []
        new_phones = normalize_phones(list(phones_set)) if phones else []

        if emails:
            merged = sorted(set(lead.emails or []) | set(new_emails))
            lead.emails = merged
            lead.has_email = len(merged) > 0
        if phones:
            merged = sorted(set(lead.phones or []) | set(new_phones))
            lead.phones = merged
            lead.has_phone = len(merged) > 0

        if social_links:
            model = LeadModel(
                id=lead.id,
                name=lead.name,
                niche=lead.niche,
                website=target_url,
                emails=lead.emails or [],
                phones=lead.phones or [],
                address=lead.address,
                source=lead.source,
                city=lead.city,
                country=lead.country,
                social_links=lead.social_links or {},
                tags=list(lead.tags or []),
                service_tags=list(lead.service_tags or []),
                meta=dict(lead.meta or {}),
            )
            enriched = EnrichmentService.enrich_lead(model, resp.text, target_url)
            lead.social_links = enriched.social_links or {}
            lead.has_social = bool(enriched.social_links)
            lead.company_size = enriched.company_size
            lead.service_tags = enriched.service_tags or []
            lead.contact_person_name = enriched.contact_person_name
            lead.contact_person_role = enriched.contact_person_role
            lead.contact_person_email = enriched.contact_person_email
            lead.is_multi_location = bool(enriched.is_multi_location)
            lead.branch_locations = enriched.branch_locations or []
            # Keep existing meta and merge enrichment meta
            merged_meta = dict(lead.meta or {})
            merged_meta.update(enriched.meta or {})
            lead.meta = merged_meta
            if enriched.quality_score is not None:
                lead.quality_score = enriched.quality_score

        lead.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


@router.post("/google-maps/enrich-leads", response_model=EnrichLeadsResponse)
def enrich_google_maps_leads(
    payload: EnrichLeadsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[UserORM] = Depends(get_current_user_optional),
    workspace: Optional[WorkspaceORM] = Depends(get_current_workspace_optional),
):
    org = get_or_create_default_org(db)
    q = db.query(LeadORM).filter(
        LeadORM.organization_id == org.id,
        LeadORM.id.in_(payload.lead_ids),
    )
    if workspace:
        q = q.filter(LeadORM.workspace_id == workspace.id)
    leads = q.all()
    if not leads:
        raise HTTPException(status_code=404, detail="No leads found")

    queued = 0
    skipped = 0
    for lead in leads:
        target_url = (lead.meta or {}).get("google_maps_business_website") or lead.website
        if not _is_http_url(target_url) or "google.com/maps" in target_url:
            skipped += 1
            continue
        queued += 1
        background_tasks.add_task(_enrich_lead_contacts_task, lead.id, payload.emails, payload.phones, payload.social_links)

    return EnrichLeadsResponse(queued=queued, skipped=skipped, lead_ids=[l.id for l in leads])


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

