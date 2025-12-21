"""Job-based API routes with database persistence"""
import logging
from typing import Any, Dict, List, Union

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.routes_auth import get_current_user
from app.api.routes_workspaces import get_current_workspace
from app.api.schemas import ScrapeRequest, LeadOut
from app.core.db import get_db
from app.core.orm import ActivityLogORM, JobStatus, LeadORM, ScrapeJobORM, UserORM
from app.core.orm_workspaces import WorkspaceORM

router = APIRouter()
logger = logging.getLogger(__name__)


def _normalize_tech_stack(tech_stack: Union[List[str], Dict[str, Any], None]) -> List[str]:
    """Convert tech_stack from dict or list to list format (matches LeadOut schema)."""
    if tech_stack is None:
        return []

    if isinstance(tech_stack, list):
        return [str(item) for item in tech_stack if item]

    if isinstance(tech_stack, dict):
        result: List[str] = []
        for key, value in tech_stack.items():
            if key and str(key) not in result:
                result.append(str(key))
            if isinstance(value, list):
                for item in value:
                    if item and str(item) not in result:
                        result.append(str(item))
            elif value and str(value) not in result:
                result.append(str(value))
        return result

    return [str(tech_stack)] if tech_stack else []


def _update_job_progress(db: Session, job_id: int, processed: int, total: int):
    """Update job progress (called from async context, so we need to handle DB carefully)"""
    try:
        # Get fresh job instance
        from app.core.orm import ScrapeJobORM
        job = db.query(ScrapeJobORM).filter(ScrapeJobORM.id == job_id).first()
        if job:
            job.processed_targets = processed
            job.total_targets = total
            # Update result_count from current leads
            from app.core.orm import LeadORM
            lead_count = db.query(LeadORM).filter(LeadORM.job_id == job_id).count()
            job.result_count = lead_count
            db.commit()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to update job progress: {e}")
        try:
            db.rollback()
        except:
            pass


def _require_org_and_workspace(
    current_user: UserORM,
    workspace: WorkspaceORM,
) -> tuple[int, int]:
    """
    Ensure the user has an organization and the workspace belongs to it.
    Returns (organization_id, workspace_id).
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an organization.",
        )

    if workspace.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace does not belong to your organization.",
        )

    return current_user.organization_id, workspace.id


def _get_job_for_workspace(
    db: Session,
    job_id: int,
    org_id: int,
    workspace_id: int,
):
    """Fetch a job ensuring it belongs to the organization/workspace context."""
    job = (
        db.query(ScrapeJobORM)
        .filter(
            ScrapeJobORM.id == job_id,
            ScrapeJobORM.organization_id == org_id,
            or_(
                ScrapeJobORM.workspace_id == workspace_id,
                ScrapeJobORM.workspace_id.is_(None),
            ),
        )
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/logs")
def get_job_logs(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Fetch recent activity logs for a job."""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    _get_job_for_workspace(db, job_id, org_id, workspace_id)

    logs = (
        db.query(ActivityLogORM)
        .filter(
            ActivityLogORM.job_id == job_id,
            ActivityLogORM.organization_id == org_id,
        )
        .order_by(ActivityLogORM.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "id": log.id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "activity_type": log.activity_type,
            "description": log.description,
            "meta": log.meta or {},
        }
        for log in logs
    ]


@router.get("/jobs", response_model=List[dict])
def get_jobs(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> List[dict]:
    """Get all jobs for the current workspace"""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    jobs = (
        db.query(ScrapeJobORM)
        .filter(
            ScrapeJobORM.organization_id == org_id,
            or_(
                ScrapeJobORM.workspace_id == workspace_id,
                ScrapeJobORM.workspace_id.is_(None),
            ),
        )
        .order_by(ScrapeJobORM.created_at.desc())
        .all()
    )
    
    return [
        {
            "id": job.id,
            "niche": job.niche,
            "location": job.location,
            "status": job.status.value,
            "result_count": job.result_count,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
            "sites_crawled": job.sites_crawled,
            "sites_failed": job.sites_failed,
            "total_pages_crawled": job.total_pages_crawled,
            "sources_used": job.sources_used or [],
            "error_message": job.error_message,
            "max_results": job.max_results,
            "max_pages_per_site": job.max_pages_per_site,
            "total_targets": job.total_targets,
            "processed_targets": job.processed_targets or 0,
            "extract_config": job.extract_config or {},
            "ai_status": job.ai_status or "idle",
            "ai_summary": job.ai_summary,
            "ai_segments": job.ai_segments or [],
            "ai_error": job.ai_error,
        }
        for job in jobs
    ]


# AI Insights endpoint - must come BEFORE /jobs/{job_id} to avoid route conflicts
@router.post("/jobs/{job_id}/ai-insights")
async def trigger_job_ai_insights(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> dict:
    """Trigger AI insights generation for a completed job"""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    job = _get_job_for_workspace(db, job_id, org_id, workspace_id)
    
    if job.status != JobStatus.completed and job.status != JobStatus.completed_with_warnings:
        raise HTTPException(
            status_code=400,
            detail="Job must be completed before generating AI insights."
        )
    
    # Mark as running and clear previous error
    job.ai_status = "running"
    job.ai_error = None
    db.commit()
    
    # Run in background
    from app.services.ai_insights_service import generate_job_ai_insights
    background_tasks.add_task(generate_job_ai_insights, db, job_id, org_id)
    
    # Return updated job
    return {
        "id": job.id,
        "ai_status": job.ai_status,
        "ai_summary": job.ai_summary,
        "ai_segments": job.ai_segments or [],
        "ai_error": job.ai_error,
    }


@router.get("/jobs/{job_id}", response_model=dict)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> dict:
    """Get a single job by ID"""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    job = _get_job_for_workspace(db, job_id, org_id, workspace_id)
    
    return {
        "id": job.id,
        "niche": job.niche,
        "location": job.location,
        "status": job.status.value,
        "result_count": job.result_count,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "duration_seconds": job.duration_seconds,
        "sites_crawled": job.sites_crawled,
        "sites_failed": job.sites_failed,
        "total_pages_crawled": job.total_pages_crawled,
        "sources_used": job.sources_used or [],
        "error_message": job.error_message,
        "max_results": job.max_results,
        "max_pages_per_site": job.max_pages_per_site,
        "total_targets": job.total_targets,
        "processed_targets": job.processed_targets or 0,
        "extract_config": job.extract_config or {},
        "ai_status": job.ai_status or "idle",
        "ai_summary": job.ai_summary,
        "ai_segments": job.ai_segments or [],
        "ai_error": job.ai_error,
    }


@router.post("/jobs/{job_id}/ai-segments/{segment_index}/saved-view")
async def create_ai_segment_saved_view(
    job_id: int,
    segment_index: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> dict:
    """Create a Saved View from an AI segment"""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    job = _get_job_for_workspace(db, job_id, org_id, workspace_id)
    
    if job.ai_status != "ready" or not job.ai_segments:
        raise HTTPException(
            status_code=400,
            detail="AI segments not available for this job."
        )
    
    segments = job.ai_segments or []
    if segment_index < 0 or segment_index >= len(segments):
        raise HTTPException(status_code=400, detail="Invalid segment index.")
    
    segment = segments[segment_index]
    
    # Get workspace_id if available
    workspace_id = job.workspace_id or workspace_id
    
    from app.services.ai_segment_actions import create_saved_view_from_ai_segment
    view = create_saved_view_from_ai_segment(
        db,
        org_id=org_id,
        workspace_id=workspace_id,
        user_id=job.created_by_user_id,
        job=job,
        segment=segment,
        segment_index=segment_index,
    )
    
    return {
        "id": view.id,
        "name": view.name,
        "page_type": view.page_type,
        "filters": view.filters,
        "is_shared": view.is_shared,
        "created_at": view.created_at.isoformat() if view.created_at else None,
    }


@router.post("/jobs/{job_id}/ai-segments/{segment_index}/playbook")
async def create_ai_segment_playbook(
    job_id: int,
    segment_index: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> dict:
    """Create a Playbook Blueprint from an AI segment"""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    job = _get_job_for_workspace(db, job_id, org_id, workspace_id)
    
    if job.ai_status != "ready" or not job.ai_segments:
        raise HTTPException(
            status_code=400,
            detail="AI segments not available for this job."
        )
    
    segments = job.ai_segments or []
    if segment_index < 0 or segment_index >= len(segments):
        raise HTTPException(status_code=400, detail="Invalid segment index.")
    
    segment = segments[segment_index]
    
    # Get workspace_id if available
    workspace_id = job.workspace_id or workspace_id
    
    from app.services.ai_segment_actions import create_playbook_from_ai_segment
    playbook = create_playbook_from_ai_segment(
        db,
        org_id=org_id,
        workspace_id=workspace_id,
        user_id=job.created_by_user_id,
        job=job,
        segment=segment,
        segment_index=segment_index,
    )
    
    return {
        "id": playbook.id,
        "name": playbook.name,
        "description": playbook.description,
        "status": playbook.status.value if hasattr(playbook.status, "value") else str(playbook.status),
        "created_at": playbook.created_at.isoformat() if playbook.created_at else None,
    }


@router.get("/jobs/{job_id}/leads", response_model=List[LeadOut])
def get_job_leads(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> List[LeadOut]:
    """Get leads for a specific job"""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    job = _get_job_for_workspace(db, job_id, org_id, workspace_id)
    
    # Get leads
    leads = db.query(LeadORM).filter(LeadORM.job_id == job_id).order_by(LeadORM.quality_score.desc().nulls_last()).all()
    
    return [
        LeadOut(
            id=lead.id,
            name=lead.name,
            niche=lead.niche,
            website=lead.website,
            emails=lead.emails or [],
            phones=lead.phones or [],
            address=lead.address,
            source=lead.source,
            city=lead.city,
            country=lead.country,
            quality_score=float(lead.quality_score) if lead.quality_score else None,
            quality_label=lead.quality_label,
            tags=lead.tags or [],
            cms=lead.cms,
            tech_stack=_normalize_tech_stack(lead.tech_stack),
            social_links=lead.social_links or {},
            metadata=lead.meta or {},
            ai_status=lead.ai_status,
            ai_last_error=lead.ai_last_error,
        )
        for lead in leads
    ]


@router.post("/jobs/run-once", response_model=dict)
async def run_scrape_job(
    payload: ScrapeRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> dict:
    """Create a scrape job and run it in the background - returns immediately"""
    from datetime import datetime, timezone
    
    job = None
    try:
        org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
        
        # Create job with "pending" status (will change to "running" when background task starts)
        extract_config_dict = payload.extract.dict() if payload.extract else {}
        job = ScrapeJobORM(
            organization_id=org_id,
            workspace_id=workspace_id,
            created_by_user_id=current_user.id,
            niche=payload.niche,
            location=payload.location,
            max_results=payload.max_results,
            max_pages_per_site=payload.max_pages_per_site,
            status=JobStatus.pending,  # Start as pending, will change to running in background
            extract_config=extract_config_dict,
            processed_targets=0,
        )
        db.add(job)
        db.flush()  # Get job.id (sync, no await)
        logger.info(f"Created job {job.id}, scheduling background execution")
        
        # Prepare payload dict for background task
        payload_dict = {
            "niche": payload.niche,
            "location": payload.location,
            "max_results": payload.max_results,
            "max_pages_per_site": payload.max_pages_per_site,
            "sources": payload.sources,
            "extract": extract_config_dict,
        }
        
        # Commit before spawning the worker so it's visible
        db.commit()
        
        # Run job in background (in-process async task to avoid Windows spawn issues)
        try:
            import asyncio
            from app.api.background_job_executor import execute_job_background
            asyncio.create_task(execute_job_background(job.id, org_id, payload_dict))
        except Exception as worker_error:
            logger.error(f"Failed to start background task for job {job.id}: {worker_error}", exc_info=True)
            job.status = JobStatus.failed
            job.error_message = "Unable to start background task"
            db.commit()
            raise HTTPException(
                status_code=500,
                detail="Unable to start background task for this job. Please try again.",
            )
        
        # Return job immediately (scraping will happen in background)
        return {
            "id": job.id,
            "niche": job.niche,
            "location": job.location,
            "max_results": job.max_results,
            "max_pages_per_site": job.max_pages_per_site,
            "status": job.status.value,
            "error_message": job.error_message,
            "result_count": job.result_count,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
            "sites_crawled": job.sites_crawled or 0,
            "sites_failed": job.sites_failed or 0,
            "total_pages_crawled": job.total_pages_crawled or 0,
            "sources_used": job.sources_used or [],
            "total_targets": job.total_targets,
            "processed_targets": job.processed_targets or 0,
            "extract_config": job.extract_config or {},
        }
    
    except Exception as e:
        import traceback
        error_msg = str(e)[:500]
        error_trace = traceback.format_exc()
        
        # Log the full error for debugging
        logger.error(f"Job {job.id if job else 'unknown'} failed: {error_trace}")
        
        # Try to save error to job
        if job:
            try:
                job.status = JobStatus.failed
                job.error_message = error_msg
                db.commit()
            except Exception as save_error:
                logger.error(f"Failed to save error to job: {save_error}")
                try:
                    db.rollback()
                except:
                    pass
        
        # Provide helpful error message
        if "relation" in str(e).lower() or "does not exist" in str(e).lower():
            raise HTTPException(
                status_code=500,
                detail=f"Database tables not found. Please run 'python init_db.py' to create them. Error: {error_msg}"
            )
        raise HTTPException(
            status_code=500, 
            detail=f"Job failed: {error_msg}"
        )


@router.post("/jobs/{job_id}/retry", response_model=dict)
async def retry_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> dict:
    """Retry a scrape job with the same parameters."""
    import asyncio
    from datetime import timezone, datetime
    from app.api.background_job_executor import execute_job_background

    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    job = _get_job_for_workspace(db, job_id, org_id, workspace_id)

    # Reset job state
    job.status = JobStatus.pending
    job.error_message = None
    job.result_count = 0
    job.started_at = None
    job.completed_at = None
    job.duration_seconds = None
    job.processed_targets = 0
    job.total_targets = None
    job.sites_crawled = 0
    job.sites_failed = 0
    job.total_pages_crawled = 0
    job.sources_used = job.sources_used or []

    payload_dict = {
        "niche": job.niche,
        "location": job.location,
        "max_results": job.max_results,
        "max_pages_per_site": job.max_pages_per_site,
        "sources": job.sources_used or ["google_search", "google_places", "web_search"],
        "extract": job.extract_config or {},
    }

    db.commit()
    try:
        activity = ActivityLogORM(
            job_id=job.id,
            organization_id=org_id,
            activity_type="job.retry",
            description="Retry requested",
            meta={"requested_by": current_user.id},
        )
        db.add(activity)
        db.commit()
    except Exception:
        db.rollback()

    try:
        asyncio.create_task(execute_job_background(job.id, org_id, payload_dict))
    except Exception as worker_error:
        logger.error(f"Failed to start background task for retry {job.id}: {worker_error}", exc_info=True)
        job.status = JobStatus.failed
        job.error_message = "Unable to start background task"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail="Unable to start background task for retry. Please try again.",
        )

    return {
        "id": job.id,
        "niche": job.niche,
        "location": job.location,
        "max_results": job.max_results,
        "max_pages_per_site": job.max_pages_per_site,
        "status": job.status.value,
        "error_message": job.error_message,
        "result_count": job.result_count,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "duration_seconds": job.duration_seconds,
        "sites_crawled": job.sites_crawled or 0,
        "sites_failed": job.sites_failed or 0,
        "total_pages_crawled": job.total_pages_crawled or 0,
        "sources_used": job.sources_used or [],
        "total_targets": job.total_targets,
        "processed_targets": job.processed_targets or 0,
        "extract_config": job.extract_config or {},
    }
