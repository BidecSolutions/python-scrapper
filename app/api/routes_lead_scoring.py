"""Lead scoring and NBA API routes"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.db import get_db
from app.core.orm import LeadORM
from app.api.routes_settings import get_or_create_default_org
from app.services.lead_scoring_service import recompute_lead_score
from app.services.next_best_action_service import recompute_next_action_for_lead

logger = logging.getLogger(__name__)
router = APIRouter()


class RecomputeScoresRequest(BaseModel):
    """Request to recompute scores"""
    lead_ids: Optional[List[int]] = None  # If None, recompute all leads
    workspace_id: Optional[int] = None


class RecomputeScoresResponse(BaseModel):
    """Response for score recomputation"""
    message: str
    leads_processed: int


@router.post("/leads/{lead_id}/recompute-score", status_code=status.HTTP_200_OK)
def recompute_single_lead_score(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Recompute health score and next action for a single lead"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Recompute score
    score = recompute_lead_score(db, lead)
    
    # Recompute next action
    action, reason = recompute_next_action_for_lead(db, lead)
    
    return {
        "lead_id": lead.id,
        "health_score": float(score),
        "next_action": action.value,
        "next_action_reason": reason,
    }


@router.post("/leads/recompute-scores", response_model=RecomputeScoresResponse, status_code=status.HTTP_202_ACCEPTED)
def recompute_scores_batch(
    request: RecomputeScoresRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Recompute health scores and next actions for multiple leads
    
    If lead_ids is None, recomputes all leads in the organization/workspace.
    This runs in the background.
    """
    org = get_or_create_default_org(db)
    
    # Build query
    query = db.query(LeadORM).filter(LeadORM.organization_id == org.id)
    
    if request.workspace_id:
        query = query.filter(LeadORM.workspace_id == request.workspace_id)
    
    if request.lead_ids:
        query = query.filter(LeadORM.id.in_(request.lead_ids))
    
    leads = query.all()
    
    if not leads:
        return RecomputeScoresResponse(
            message="No leads found to process",
            leads_processed=0
        )
    
    # Process in background
    def process_scores():
        from app.core.db import SessionLocal
        db_local = SessionLocal()
        try:
            processed = 0
            for lead in leads:
                try:
                    recompute_lead_score(db_local, lead)
                    recompute_next_action_for_lead(db_local, lead)
                    processed += 1
                except Exception as e:
                    logger.error(f"Error processing lead {lead.id}: {e}", exc_info=True)
            logger.info(f"Processed {processed} leads for score recomputation")
        finally:
            db_local.close()
    
    background_tasks.add_task(process_scores)
    
    return RecomputeScoresResponse(
        message=f"Score recomputation started for {len(leads)} leads",
        leads_processed=len(leads)
    )

