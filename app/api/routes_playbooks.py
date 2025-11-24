"""Playbooks API routes"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from sqlalchemy import func

from app.core.db import get_db
from app.core.orm import OrganizationORM, LeadORM, EmailORM, EmailVerificationStatus
from app.core.orm_lists import LeadListORM, LeadListLeadORM
from app.core.orm_playbooks import PlaybookJobORM, PlaybookJobStatus, PlaybookJobType
from app.api.routes_settings import get_or_create_default_org
from app.services.playbook_processor import (
    process_linkedin_campaign_playbook,
    estimate_playbook_credits
)

logger = logging.getLogger(__name__)
router = APIRouter()


class PlaybookRequest(BaseModel):
    """Request to run a LinkedIn → Campaign playbook"""
    days: int = Field(default=7, ge=1, le=90, description="Number of days to look back")
    include_risky: bool = Field(default=False, description="Include risky emails in output")
    min_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Minimum quality score")
    list_name: Optional[str] = Field(None, description="Custom list name (auto-generated if not provided)")


class PlaybookJobResponse(BaseModel):
    """Response from playbook job creation"""
    id: int
    type: str
    status: str
    estimated_credits: Optional[int] = None
    output_list_id: Optional[int] = None
    created_at: str
    meta: dict = {}


class PlaybookJobDetailResponse(BaseModel):
    """Detailed playbook job response"""
    id: int
    type: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error_message: Optional[str] = None
    estimated_credits: Optional[int] = None
    credits_used: int
    meta: dict
    output_list_id: Optional[int] = None
    output_list_name: Optional[str] = None


@router.post("/playbooks/linkedin-campaign", response_model=PlaybookJobResponse)
def create_linkedin_campaign_playbook(
    request: PlaybookRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create and start a LinkedIn → Campaign playbook job
    
    This playbook:
    1. Finds all LinkedIn leads from the last N days
    2. Runs Email Finder on leads without emails
    3. Runs Verifier on all emails
    4. Filters to Valid (and optionally Risky) emails
    5. Filters by minimum quality score
    6. Creates a campaign-ready list
    
    Returns the job info (status will update as it processes)
    """
    org = get_or_create_default_org(db)
    
    # Estimate credits
    estimated_credits = estimate_playbook_credits(
        db=db,
        organization_id=org.id,
        days=request.days,
        min_score=request.min_score
    )
    
    # Create job
    job = PlaybookJobORM(
        organization_id=org.id,
        type=PlaybookJobType.linkedin_campaign.value,
        status=PlaybookJobStatus.queued.value,
        params={
            "days": request.days,
            "include_risky": request.include_risky,
            "min_score": request.min_score,
            "list_name": request.list_name,
        },
        meta={},
        estimated_credits=estimated_credits,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start background processing
    # For now, run synchronously (in production, use Celery/background worker)
    try:
        process_linkedin_campaign_playbook(db, job.id)
    except Exception as e:
        logger.error(f"Playbook job {job.id} failed: {e}", exc_info=True)
        job.status = PlaybookJobStatus.failed.value
        job.error_message = str(e)
        db.commit()
    
    return PlaybookJobResponse(
        id=job.id,
        type=job.type,
        status=job.status,
        estimated_credits=job.estimated_credits,
        output_list_id=job.output_list_id,
        created_at=job.created_at.isoformat(),
        meta=job.meta,
    )


@router.get("/playbooks/jobs", response_model=List[PlaybookJobDetailResponse])
def get_playbook_jobs(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of jobs to return"),
    db: Session = Depends(get_db),
):
    """Get recent playbook jobs"""
    org = get_or_create_default_org(db)
    
    jobs = db.query(PlaybookJobORM).filter(
        PlaybookJobORM.organization_id == org.id
    ).order_by(PlaybookJobORM.created_at.desc()).limit(limit).all()
    
    return [
        PlaybookJobDetailResponse(
            id=job.id,
            type=job.type or "",
            status=job.status or "queued",
            created_at=job.created_at.isoformat() if job.created_at else datetime.utcnow().isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            finished_at=job.finished_at.isoformat() if job.finished_at else None,
            error_message=job.error_message,
            estimated_credits=job.estimated_credits,
            credits_used=job.credits_used or 0,
            meta=job.meta or {},
            output_list_id=job.output_list_id,
            output_list_name=(job.meta or {}).get("output_list_name") if job.meta else None,
        )
        for job in jobs
    ]


@router.get("/playbooks/jobs/{job_id}", response_model=PlaybookJobDetailResponse)
def get_playbook_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific playbook job by ID"""
    org = get_or_create_default_org(db)
    
    job = db.query(PlaybookJobORM).filter(
        PlaybookJobORM.id == job_id,
        PlaybookJobORM.organization_id == org.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Playbook job not found")
    
    return PlaybookJobDetailResponse(
        id=job.id,
        type=job.type,
        status=job.status,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        error_message=job.error_message,
        estimated_credits=job.estimated_credits,
        credits_used=job.credits_used,
        meta=job.meta,
        output_list_id=job.output_list_id,
        output_list_name=job.meta.get("output_list_name") if job.meta else None,
    )
