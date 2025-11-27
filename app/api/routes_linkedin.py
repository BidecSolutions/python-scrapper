"""LinkedIn capture API routes"""
import logging
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, HttpUrl

from app.core.db import get_db
from app.core.orm import OrganizationORM
from app.services.api_key_auth import get_api_key_context, ApiKeyContext
from app.schemas.linkedin import (
    LinkedInCaptureRequest,
    LinkedInCaptureResponse,
    LeadEmailStatus,
    JobRef,
)
from app.services.linkedin_capture import (
    normalize_name,
    get_or_create_lead_from_linkedin,
    build_email_status,
    enqueue_finder_and_verifier,
)
from app.api.routes_settings import get_or_create_default_org
from app.services.api_key_auth import get_api_key_context, ApiKeyContext
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()


# Schema for Playwright scraping request
class LinkedInScrapeRequest(BaseModel):
    """Request to scrape LinkedIn profile using Playwright"""
    linkedin_url: HttpUrl
    auto_find_email: bool = True
    skip_smtp: bool = False
    headless: bool = True


class LinkedInScrapeResponse(BaseModel):
    """Response from Playwright scraping"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    linkedin_url: str


@router.post(
    "/leads/linkedin-capture",
    response_model=LinkedInCaptureResponse,
    status_code=status.HTTP_201_CREATED,
)
def linkedin_capture(
    payload: LinkedInCaptureRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Capture a lead from LinkedIn profile
    
    Creates or updates a lead from LinkedIn profile data.
    Optionally runs email finder and verifier automatically.
    
    Supports both API key auth (for extension) and user JWT auth.
    """
    # Try API key auth first (for extension)
    api_context: Optional[ApiKeyContext] = None
    try:
        api_context = get_api_key_context(request, db, required_scopes=["leads:write"])
    except HTTPException:
        # If API key auth fails, fall back to user auth
        pass
    
    # Get current user ID (for ownership attribution)
    current_user_id = None
    try:
        from app.api.routes_workspaces import get_current_user_id
        current_user_id = get_current_user_id(db=db)
    except:
        pass
    
    if api_context:
        # Use workspace from API key
        org = api_context.organization
        workspace_id = api_context.workspace.id if api_context.workspace else None
        # For API key, use workspace owner or first member as owner
        if not current_user_id and workspace_id:
            from app.core.orm_workspaces import WorkspaceMemberORM, WorkspaceRole
            owner_member = db.query(WorkspaceMemberORM).filter(
                WorkspaceMemberORM.workspace_id == workspace_id,
                WorkspaceMemberORM.role == WorkspaceRole.owner
            ).first()
            if owner_member:
                current_user_id = owner_member.user_id
    else:
        # Fall back to default org (user auth)
        org = get_or_create_default_org(db)
        workspace_id = None
    
    # 1. Normalize names
    first_name, last_name = normalize_name(
        payload.full_name,
        payload.first_name,
        payload.last_name
    )
    
    if not first_name:
        raise HTTPException(
            status_code=400,
            detail="full_name is required and must contain at least a first name"
        )
    
    # 2. Extract domain
    company_domain = payload.company_domain
    if not company_domain and payload.company_name:
        # Try to derive domain from company name
        from app.services.linkedin_capture import extract_domain_from_company
        company_domain = extract_domain_from_company(payload.company_name)
    
    # 3. Create or update lead
    lead = get_or_create_lead_from_linkedin(
        db=db,
        organization_id=org.id,
        workspace_id=workspace_id,
        owner_user_id=current_user_id,  # Set owner for rep performance tracking
        first_name=first_name,
        last_name=last_name,
        full_name=payload.full_name,
        title=payload.title,
        headline=payload.headline,
        company_name=payload.company_name,
        company_domain=company_domain,
        linkedin_url=str(payload.linkedin_url),
    )
    
    # 3.5. Add to list if specified
    if payload.list_id:
        from app.core.orm_lists import LeadListORM, LeadListLeadORM
        # Verify list exists and belongs to org
        list_obj = db.query(LeadListORM).filter(
            LeadListORM.id == payload.list_id,
            LeadListORM.organization_id == org.id
        ).first()
        
        if list_obj:
            # Check if already in list
            existing = db.query(LeadListLeadORM).filter(
                LeadListLeadORM.list_id == payload.list_id,
                LeadListLeadORM.lead_id == lead.id
            ).first()
            
            if not existing:
                list_lead = LeadListLeadORM(
                    list_id=payload.list_id,
                    lead_id=lead.id,
                )
                db.add(list_lead)
                db.commit()
    
    job_ref = None
    
    # 4. Optionally auto-run Email Finder + Verifier
    if payload.auto_find_email:
        # Check if lead already has email
        from app.core.orm import EmailORM
        existing_email = db.query(EmailORM).filter(
            EmailORM.organization_id == org.id,
            EmailORM.lead_id == lead.id,
            EmailORM.verify_status == "valid"
        ).first()
        
        if not existing_email:
            # Try to find email
            finder_job = enqueue_finder_and_verifier(
                db=db,
                organization_id=org.id,
                lead=lead,
                skip_smtp=payload.skip_smtp,
            )
            
            # For now, we don't create a separate job - email finder runs synchronously
            # In the future, if we want async jobs, we'd return a job_ref here
            # job_ref = JobRef(id=finder_job.id, type="finder_and_verify", status=finder_job.status.value) if finder_job else None
    
    # 5. Build email_status from lead
    email_status_dict = build_email_status(db, lead)
    email_status = LeadEmailStatus(**email_status_dict) if email_status_dict else None
    
    # 6. Build response
    return LinkedInCaptureResponse(
        id=lead.id,
        first_name=first_name,
        last_name=last_name,
        full_name=payload.full_name,
        title=payload.title or payload.headline,
        headline=payload.headline,
        company_name=payload.company_name,
        company_domain=company_domain,
        linkedin_url=payload.linkedin_url,
        email_status=email_status,
        score=float(lead.quality_score) if lead.quality_score else None,
        source="linkedin_extension",
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        job=job_ref,
    )


@router.post(
    "/leads/linkedin-scrape",
    response_model=LinkedInScrapeResponse,
    status_code=status.HTTP_200_OK,
)
async def linkedin_scrape_playwright(
    payload: LinkedInScrapeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Scrape LinkedIn profile using Playwright browser automation
    
    This endpoint uses headless browser automation to scrape LinkedIn profiles,
    which is more reliable than DOM scraping for JS-heavy pages.
    
    Supports both API key auth (for extension) and user JWT auth.
    """
    try:
        # Try API key auth first (for extension)
        api_context: Optional[ApiKeyContext] = None
        try:
            api_context = get_api_key_context(request, db, required_scopes=["leads:write"])
        except HTTPException:
            # If API key auth fails, fall back to user auth
            pass
        
        # Get organization
        if api_context:
            org = api_context.organization
        else:
            org = get_or_create_default_org(db)
        
        # Import Playwright scraper
        try:
            from app.services.linkedin_playwright_scraper import scrape_linkedin_profile
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Playwright scraper not available. Please install playwright: pip install playwright && playwright install chromium"
            )
        
        # Scrape profile using Playwright
        logger.info(f"Scraping LinkedIn profile with Playwright: {payload.linkedin_url}")
        profile_data = await scrape_linkedin_profile(
            str(payload.linkedin_url),
            headless=payload.headless
        )
        
        if not profile_data or profile_data.get('error'):
            return LinkedInScrapeResponse(
                success=False,
                error=profile_data.get('error', 'Failed to scrape profile') if profile_data else 'No data returned',
                linkedin_url=str(payload.linkedin_url)
            )
        
        # Create or update lead from scraped data
        first_name = profile_data.get('first_name') or ''
        last_name = profile_data.get('last_name') or ''
        full_name = profile_data.get('full_name') or f"{first_name} {last_name}".strip()
        
        if not full_name or full_name == 'Unknown':
            # Try to extract from URL as fallback
            url_parts = str(payload.linkedin_url).split('/in/')
            if len(url_parts) > 1:
                username = url_parts[-1].split('/')[0].replace('-', ' ').title()
                full_name = username
                first_name = username.split()[0] if username.split() else ''
                last_name = ' '.join(username.split()[1:]) if len(username.split()) > 1 else ''
        
        # Extract domain from company
        company_domain = None
        if profile_data.get('company_name'):
            from app.services.linkedin_capture import extract_domain_from_company
            company_domain = extract_domain_from_company(profile_data.get('company_name'))
        
        # Create or update lead
        lead = get_or_create_lead_from_linkedin(
            db=db,
            organization_id=org.id,
            workspace_id=api_context.workspace.id if api_context and api_context.workspace else None,
            owner_user_id=None,  # Will be set by API key context if available
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            title=profile_data.get('headline'),
            headline=profile_data.get('headline'),
            company_name=profile_data.get('company_name'),
            company_domain=company_domain,
            linkedin_url=str(payload.linkedin_url),
        )
        
        # Optionally find email
        if payload.auto_find_email:
            from app.core.orm import EmailORM
            existing_email = db.query(EmailORM).filter(
                EmailORM.organization_id == org.id,
                EmailORM.lead_id == lead.id,
                EmailORM.verify_status == "valid"
            ).first()
            
            if not existing_email:
                enqueue_finder_and_verifier(
                    db=db,
                    organization_id=org.id,
                    lead=lead,
                    skip_smtp=payload.skip_smtp,
                )
        
        return LinkedInScrapeResponse(
            success=True,
            data={
                **profile_data,
                'lead_id': lead.id,
            },
            linkedin_url=str(payload.linkedin_url)
        )
        
    except Exception as e:
        logger.error(f"Error scraping LinkedIn profile: {e}", exc_info=True)
        return LinkedInScrapeResponse(
            success=False,
            error=str(e),
            linkedin_url=str(payload.linkedin_url)
        )


@router.post(
    "/leads/linkedin-scrape-batch",
    response_model=List[LinkedInScrapeResponse],
    status_code=status.HTTP_200_OK,
)
async def linkedin_scrape_batch(
    linkedin_urls: List[HttpUrl],
    request: Request,
    auto_find_email: bool = True,
    headless: bool = True,
    db: Session = Depends(get_db),
):
    """
    Scrape multiple LinkedIn profiles using Playwright
    
    Args:
        linkedin_urls: List of LinkedIn profile URLs to scrape
        auto_find_email: Automatically find emails for scraped profiles
        headless: Run browser in headless mode
    """
    try:
        # Try API key auth first
        api_context: Optional[ApiKeyContext] = None
        try:
            api_context = get_api_key_context(request, db, required_scopes=["leads:write"])
        except HTTPException:
            pass
        
        # Get organization
        if api_context:
            org = api_context.organization
        else:
            org = get_or_create_default_org(db)
        
        # Import Playwright scraper
        try:
            from app.services.linkedin_playwright_scraper import LinkedInPlaywrightScraper
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Playwright scraper not available. Please install playwright: pip install playwright && playwright install chromium"
            )
        
        # Scrape all profiles
        results = []
        async with LinkedInPlaywrightScraper(headless=headless) as scraper:
            for url in linkedin_urls:
                try:
                    profile_data = await scraper.scrape_profile(str(url))
                    
                    if profile_data and not profile_data.get('error'):
                        # Create lead
                        first_name = profile_data.get('first_name') or ''
                        last_name = profile_data.get('last_name') or ''
                        full_name = profile_data.get('full_name') or f"{first_name} {last_name}".strip()
                        
                        if full_name and full_name != 'Unknown':
                            from app.services.linkedin_capture import extract_domain_from_company
                            company_domain = None
                            if profile_data.get('company_name'):
                                company_domain = extract_domain_from_company(profile_data.get('company_name'))
                            
                            lead = get_or_create_lead_from_linkedin(
                                db=db,
                                organization_id=org.id,
                                workspace_id=api_context.workspace.id if api_context and api_context.workspace else None,
                                owner_user_id=None,
                                first_name=first_name,
                                last_name=last_name,
                                full_name=full_name,
                                title=profile_data.get('headline'),
                                headline=profile_data.get('headline'),
                                company_name=profile_data.get('company_name'),
                                company_domain=company_domain,
                                linkedin_url=str(url),
                            )
                            
                            # Auto-find email if requested
                            if auto_find_email:
                                from app.core.orm import EmailORM
                                existing_email = db.query(EmailORM).filter(
                                    EmailORM.organization_id == org.id,
                                    EmailORM.lead_id == lead.id,
                                    EmailORM.verify_status == "valid"
                                ).first()
                                
                                if not existing_email:
                                    enqueue_finder_and_verifier(
                                        db=db,
                                        organization_id=org.id,
                                        lead=lead,
                                        skip_smtp=False,
                                    )
                            
                            results.append(LinkedInScrapeResponse(
                                success=True,
                                data={**profile_data, 'lead_id': lead.id},
                                linkedin_url=str(url)
                            ))
                        else:
                            results.append(LinkedInScrapeResponse(
                                success=False,
                                error="Could not extract name from profile",
                                linkedin_url=str(url)
                            ))
                    else:
                        results.append(LinkedInScrapeResponse(
                            success=False,
                            error=profile_data.get('error', 'Failed to scrape') if profile_data else 'No data',
                            linkedin_url=str(url)
                        ))
                    
                    # Small delay between requests
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    results.append(LinkedInScrapeResponse(
                        success=False,
                        error=str(e),
                        linkedin_url=str(url)
                    ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error in batch scraping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

