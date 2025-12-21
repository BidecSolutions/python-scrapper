"""Bulk AI enrichment queue API routes."""
import asyncio
from typing import List, Optional, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, case, or_
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.api.routes_auth import get_current_user
from app.api.routes_workspaces import get_current_workspace
from app.core.orm import LeadORM, UserORM
from app.core.orm_workspaces import WorkspaceORM
from app.workers.ai_tasks import ai_enrich_lead_task

router = APIRouter()


class BulkEnrichRequest(BaseModel):
    lead_ids: List[int] = Field(..., min_items=1)
    force: bool = False


class RetryEnrichRequest(BaseModel):
    lead_ids: List[int] = Field(..., min_items=1)


def _run_enrich_task(lead_id: int) -> None:
    asyncio.run(ai_enrich_lead_task(lead_id))


@router.post("/enrichment/jobs")
def enqueue_bulk_enrichment(
    payload: BulkEnrichRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Queue AI enrichment for selected leads."""
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(status_code=400, detail="User is not associated with an organization.")
    workspace_id = workspace.id

    leads = db.query(LeadORM).filter(
        LeadORM.id.in_(payload.lead_ids),
        LeadORM.organization_id == org_id,
        or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
    ).all()

    if not leads:
        raise HTTPException(status_code=404, detail="No leads found for enrichment")

    queued = 0
    skipped = 0

    for lead in leads:
        if lead.ai_status == "success" and not payload.force:
            skipped += 1
            continue
        lead.ai_status = "pending"
        lead.ai_last_error = None
        queued += 1
        background_tasks.add_task(_run_enrich_task, lead.id)

    db.commit()

    return {
        "queued": queued,
        "skipped": skipped,
        "total": len(leads),
        "lead_ids": [lead.id for lead in leads],
    }


@router.get("/enrichment/queue")
def get_enrichment_queue(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> Dict[str, int]:
    """Get enrichment queue status counts for the workspace."""
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(status_code=400, detail="User is not associated with an organization.")
    workspace_id = workspace.id

    counts = (
        db.query(
            func.sum(case((LeadORM.ai_status == "pending", 1), else_=0)).label("pending"),
            func.sum(case((LeadORM.ai_status == "processing", 1), else_=0)).label("processing"),
            func.sum(case((LeadORM.ai_status == "success", 1), else_=0)).label("success"),
            func.sum(case((LeadORM.ai_status == "failed", 1), else_=0)).label("failed"),
            func.count(LeadORM.id).label("total"),
        )
        .filter(
            LeadORM.organization_id == org_id,
            or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
        )
        .first()
    )

    return {
        "pending": int(counts.pending or 0),
        "processing": int(counts.processing or 0),
        "success": int(counts.success or 0),
        "failed": int(counts.failed or 0),
        "total": int(counts.total or 0),
    }


@router.get("/enrichment/failed")
def list_failed_enrichment(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """List failed enrichment leads with error reasons."""
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(status_code=400, detail="User is not associated with an organization.")

    leads = (
        db.query(LeadORM)
        .filter(
            LeadORM.organization_id == org_id,
            or_(LeadORM.workspace_id == workspace.id, LeadORM.workspace_id.is_(None)),
            LeadORM.ai_status == "failed",
        )
        .order_by(LeadORM.updated_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": lead.id,
            "name": lead.name,
            "website": lead.website,
            "ai_last_error": lead.ai_last_error,
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
        }
        for lead in leads
    ]


@router.post("/enrichment/retry")
def retry_enrichment(
    payload: RetryEnrichRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Retry AI enrichment for selected leads."""
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(status_code=400, detail="User is not associated with an organization.")

    leads = db.query(LeadORM).filter(
        LeadORM.id.in_(payload.lead_ids),
        LeadORM.organization_id == org_id,
        or_(LeadORM.workspace_id == workspace.id, LeadORM.workspace_id.is_(None)),
    ).all()

    if not leads:
        raise HTTPException(status_code=404, detail="No leads found for retry")

    queued = 0
    for lead in leads:
        lead.ai_status = "pending"
        lead.ai_last_error = None
        queued += 1
        background_tasks.add_task(_run_enrich_task, lead.id)

    db.commit()

    return {
        "queued": queued,
        "total": len(leads),
        "lead_ids": [lead.id for lead in leads],
    }
