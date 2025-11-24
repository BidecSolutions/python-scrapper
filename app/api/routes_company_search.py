"""Company Search API routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.core.db import get_db
from app.core.orm_company_search import CompanySearchJobORM, CompanySearchJobStatus
from app.api.routes_settings import get_or_create_default_org
from app.services.company_search import process_company_search_job

logger = logging.getLogger(__name__)
router = APIRouter()


class CompanySearchRequest(BaseModel):
    """Request to search for people at a company"""
    query: str = Field(..., description="Company domain or name (e.g., 'acme.com' or 'Acme Inc')")
    roles: List[str] = Field(default_factory=list, description="Target roles (e.g., ['founder', 'ceo', 'cmo'])")
    min_company_size: Optional[int] = Field(None, description="Minimum company size")
    max_company_size: Optional[int] = Field(None, description="Maximum company size")
    country: Optional[str] = Field(None, description="Country filter")
    list_name: Optional[str] = Field(None, description="Custom list name")
    max_leads: int = Field(50, ge=1, le=500, description="Maximum number of leads to generate")


class CompanySearchResponse(BaseModel):
    """Response from company search job creation"""
    id: int
    type: str = "company_search"
    status: str
    estimated_leads: Optional[int] = None
    list_id: Optional[int] = None
    created_at: str


@router.post("/company-search", response_model=CompanySearchResponse)
def create_company_search(
    request: CompanySearchRequest,
    db: Session = Depends(get_db),
):
    """
    Create a company search job
    
    Finds people at a company matching the criteria, creates leads,
    runs email finder/verifier, and adds them to a list.
    """
    org = get_or_create_default_org(db)
    
    # Create job
    job = CompanySearchJobORM(
        organization_id=org.id,
        status=CompanySearchJobStatus.queued.value,
        params={
            "query": request.query,
            "roles": request.roles,
            "min_company_size": request.min_company_size,
            "max_company_size": request.max_company_size,
            "country": request.country,
            "list_name": request.list_name,
            "max_leads": request.max_leads,
        },
        meta={},
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start processing (synchronous for now, can be moved to background worker)
    try:
        process_company_search_job(db, job.id)
    except Exception as e:
        logger.error(f"Company search job {job.id} failed: {e}", exc_info=True)
        job.status = CompanySearchJobStatus.failed.value
        job.error_message = str(e)
        db.commit()
    
    return CompanySearchResponse(
        id=job.id,
        status=job.status,
        estimated_leads=job.meta.get("estimated_leads") if job.meta else None,
        list_id=job.output_list_id,
        created_at=job.created_at.isoformat(),
    )


@router.get("/company-search/jobs/{job_id}")
def get_company_search_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get a company search job by ID"""
    org = get_or_create_default_org(db)
    
    job = db.query(CompanySearchJobORM).filter(
        CompanySearchJobORM.id == job_id,
        CompanySearchJobORM.organization_id == org.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Company search job not found")
    
    return {
        "id": job.id,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "error_message": job.error_message,
        "meta": job.meta,
        "output_list_id": job.output_list_id,
    }

