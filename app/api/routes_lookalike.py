"""AI Lookalike & Expansion Engine API routes"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.db import get_db
from app.core.orm_lookalike import LookalikeJobORM, LookalikeCandidateORM, LookalikeJobStatus
from app.core.orm_workspaces import WorkspaceORM
from app.core.orm import UserORM, OrganizationORM
from app.api.routes_auth import get_current_user
from app.api.routes_workspaces import get_current_workspace, get_current_user_optional, get_current_workspace_optional
from app.services.lookalike_service import build_lookalike_profile, find_lookalikes
from app.services.activity_logger import log_activity, ActivityType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lookalike", tags=["lookalike"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class LookalikeCandidateOut(BaseModel):
    id: int
    lead_id: Optional[int]
    company_id: Optional[int]
    score: float
    reason_vector: Optional[Dict[str, float]]
    
    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode = True


class LookalikeJobOut(BaseModel):
    id: int
    workspace_id: int
    started_by_user_id: int
    source_segment_id: Optional[int]
    source_list_id: Optional[int]
    source_campaign_id: Optional[int]
    status: str
    positive_lead_count: int
    candidates_found: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    
    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode = True


class LookalikeJobDetailOut(LookalikeJobOut):
    candidates: List[LookalikeCandidateOut]


class CreateLookalikeJobRequest(BaseModel):
    source_segment_id: Optional[int] = None
    source_list_id: Optional[int] = None
    source_campaign_id: Optional[int] = None
    min_score: float = Field(0.7, ge=0.0, le=1.0)
    max_results: int = Field(1000, ge=1, le=5000)
    filters: Optional[Dict[str, Any]] = None


# ============================================================================
# Background Task
# ============================================================================

def process_lookalike_job(job_id: int):
    """Background task to process lookalike job"""
    from app.core.db import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(LookalikeJobORM).filter(LookalikeJobORM.id == job_id).first()
        if not job:
            logger.error(f"Lookalike job {job_id} not found")
            return
        
        job.status = LookalikeJobStatus.running
        job.started_at = datetime.utcnow()
        db.add(job)
        db.commit()
        
        # Build profile from positive examples
        profile = build_lookalike_profile(db, job)
        
        if not profile:
            job.status = LookalikeJobStatus.failed
            job.meta = {"error": "No positive examples found"}
            db.add(job)
            db.commit()
            return
        
        # Find lookalikes
        filters = job.meta.get("filters") if job.meta else None
        min_score = job.meta.get("min_score", 0.7) if job.meta else 0.7
        max_results = job.meta.get("max_results", 1000) if job.meta else 1000
        
        candidates = find_lookalikes(
            db,
            job,
            min_score=min_score,
            max_results=max_results,
            filters=filters,
        )
        
        # Save candidates
        for candidate in candidates:
            db.add(candidate)
        
        job.candidates_found = len(candidates)
        job.status = LookalikeJobStatus.completed
        job.completed_at = datetime.utcnow()
        db.add(job)
        db.commit()
        
        logger.info(f"Lookalike job {job_id} completed: found {len(candidates)} candidates")
        
    except Exception as e:
        logger.error(f"Error processing lookalike job {job_id}: {e}", exc_info=True)
        job = db.query(LookalikeJobORM).filter(LookalikeJobORM.id == job_id).first()
        if job:
            job.status = LookalikeJobStatus.failed
            job.meta = job.meta or {}
            job.meta["error"] = str(e)
            db.add(job)
            db.commit()
    finally:
        db.close()


# ============================================================================
# Routes
# ============================================================================

@router.post("/jobs", response_model=LookalikeJobOut, status_code=201)
def create_lookalike_job(
    body: CreateLookalikeJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Create a new lookalike job"""
    # Validate that at least one source is provided
    if not body.source_segment_id and not body.source_list_id and not body.source_campaign_id:
        raise HTTPException(status_code=400, detail="Must provide source_segment_id, source_list_id, or source_campaign_id")
    
    # Get organization
    org = db.query(OrganizationORM).filter(OrganizationORM.id == workspace.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Create job
    job = LookalikeJobORM(
        workspace_id=workspace.id,
        organization_id=org.id,
        started_by_user_id=current_user.id,
        source_segment_id=body.source_segment_id,
        source_list_id=body.source_list_id,
        source_campaign_id=body.source_campaign_id,
        status=LookalikeJobStatus.pending,
        meta={
            "min_score": body.min_score,
            "max_results": body.max_results,
            "filters": body.filters or {},
        },
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start background task
    background_tasks.add_task(process_lookalike_job, job.id)
    
    # Log activity
    log_activity(
        db,
        organization_id=org.id,
        workspace_id=workspace.id,
        type=ActivityType.playbook_run,  # Reuse this type or add new one
        actor_user_id=current_user.id,
        job_id=job.id,
        meta={
            "job_type": "lookalike",
            "source_segment_id": body.source_segment_id,
            "source_list_id": body.source_list_id,
        }
    )
    
    logger.info(f"Created lookalike job {job.id} by user {current_user.id}")
    return job


@router.get("/jobs/{job_id}", response_model=LookalikeJobDetailOut)
def get_lookalike_job(
    job_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get lookalike job with candidates"""
    job = db.query(LookalikeJobORM).filter(
        LookalikeJobORM.id == job_id,
        LookalikeJobORM.workspace_id == workspace.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Lookalike job not found")
    
    # Get candidates (sorted by score)
    candidates = (
        db.query(LookalikeCandidateORM)
        .filter(LookalikeCandidateORM.job_id == job_id)
        .order_by(desc(LookalikeCandidateORM.score))
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return LookalikeJobDetailOut(
        id=job.id,
        workspace_id=job.workspace_id,
        started_by_user_id=job.started_by_user_id,
        source_segment_id=job.source_segment_id,
        source_list_id=job.source_list_id,
        source_campaign_id=job.source_campaign_id,
        status=job.status.value,
        positive_lead_count=job.positive_lead_count,
        candidates_found=job.candidates_found,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        candidates=candidates,
    )


@router.get("/jobs", response_model=List[LookalikeJobOut])
def list_lookalike_jobs(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """List lookalike jobs for current workspace"""
    jobs = (
        db.query(LookalikeJobORM)
        .filter(LookalikeJobORM.workspace_id == workspace.id)
        .order_by(desc(LookalikeJobORM.created_at))
        .limit(50)
        .all()
    )
    
    return jobs

