"""Deals/Opportunities API routes"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.db import get_db
from app.core.orm_deals import DealORM, DealStage
from app.core.orm import LeadORM, OrganizationORM
from app.core.orm_companies import CompanyORM
from app.api.routes_auth import get_current_user
from app.api.routes_workspaces import get_current_workspace, get_current_user_optional, get_current_workspace_optional
from app.core.orm import UserORM
from app.core.orm_workspaces import WorkspaceORM
from app.services.activity_logger import log_activity, ActivityType
from app.services.notification_service import create_notification, NotificationType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/deals", tags=["deals"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class DealOut(BaseModel):
    id: int
    name: str
    company_id: Optional[int]
    primary_lead_id: Optional[int]
    owner_user_id: Optional[int]
    stage: DealStage
    value: Optional[float]
    currency: str
    expected_close_date: Optional[datetime]
    source_campaign_id: Optional[int]
    source_segment_id: Optional[int]
    lost_reason: Optional[str]
    lost_at: Optional[datetime]
    won_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode = True


class DealListResponse(BaseModel):
    items: List[DealOut]
    total: int
    page: int
    page_size: int


class CreateDealRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    company_id: Optional[int] = None
    primary_lead_id: Optional[int] = None
    owner_user_id: Optional[int] = None
    stage: DealStage = DealStage.new
    value: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD", max_length=10)
    expected_close_date: Optional[datetime] = None
    source_campaign_id: Optional[int] = None
    source_segment_id: Optional[int] = None


class UpdateDealRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    company_id: Optional[int] = None
    primary_lead_id: Optional[int] = None
    owner_user_id: Optional[int] = None
    stage: Optional[DealStage] = None
    value: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    expected_close_date: Optional[datetime] = None
    lost_reason: Optional[str] = None


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=DealListResponse)
def list_deals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    stage: Optional[str] = None,  # "new", "in_progress", "won", "lost", etc.
    owner_user_id: Optional[int] = None,
    company_id: Optional[int] = None,
    segment_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """List deals for current workspace"""
    q = db.query(DealORM).filter(DealORM.workspace_id == workspace.id)
    
    # Stage filter
    if stage:
        if stage == "in_progress":
            # All stages except won/lost
            q = q.filter(~DealORM.stage.in_([DealStage.won, DealStage.lost]))
        elif stage == "won":
            q = q.filter(DealORM.stage == DealStage.won)
        elif stage == "lost":
            q = q.filter(DealORM.stage == DealStage.lost)
        else:
            try:
                stage_enum = DealStage(stage)
                q = q.filter(DealORM.stage == stage_enum)
            except ValueError:
                pass
    
    # Owner filter
    if owner_user_id is not None:
        q = q.filter(DealORM.owner_user_id == owner_user_id)
    
    # Company filter
    if company_id is not None:
        q = q.filter(DealORM.company_id == company_id)
    
    # Segment filter
    if segment_id is not None:
        q = q.filter(DealORM.source_segment_id == segment_id)
    
    # Search filter
    if search:
        like = f"%{search}%"
        q = q.filter(DealORM.name.ilike(like))
    
    total = q.count()
    
    items = (
        q.order_by(desc(DealORM.updated_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return DealListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{deal_id}", response_model=DealOut)
def get_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get deal detail"""
    deal = db.query(DealORM).filter(
        DealORM.id == deal_id,
        DealORM.workspace_id == workspace.id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return deal


@router.post("", response_model=DealOut, status_code=201)
def create_deal(
    body: CreateDealRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Create a new deal"""
    # Get organization from workspace
    org = db.query(OrganizationORM).filter(OrganizationORM.id == workspace.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Validate lead if provided
    if body.primary_lead_id:
        lead = db.query(LeadORM).filter(
            LeadORM.id == body.primary_lead_id,
            LeadORM.workspace_id == workspace.id
        ).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        # Auto-set company_id from lead if not provided
        if not body.company_id and lead.company_id:
            body.company_id = lead.company_id
    
    # Validate company if provided
    if body.company_id:
        company = db.query(CompanyORM).filter(CompanyORM.id == body.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
    
    # Default owner to current user if not specified
    owner_user_id = body.owner_user_id or current_user.id
    
    deal = DealORM(
        workspace_id=workspace.id,
        organization_id=org.id,
        name=body.name,
        company_id=body.company_id,
        primary_lead_id=body.primary_lead_id,
        owner_user_id=owner_user_id,
        stage=body.stage,
        value=body.value,
        currency=body.currency,
        expected_close_date=body.expected_close_date,
        source_campaign_id=body.source_campaign_id,
        source_segment_id=body.source_segment_id,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    
    # Log activity
    log_activity(
        db,
        organization_id=org.id,
        workspace_id=workspace.id,
        type=ActivityType.deal_created,
        actor_user_id=current_user.id,
        lead_id=body.primary_lead_id,
        deal_id=deal.id,
        meta={
            "deal_name": deal.name,
            "stage": deal.stage.value,
            "value": float(deal.value) if deal.value else None,
        }
    )
    
    # Create notification for owner
    if owner_user_id != current_user.id:
        create_notification(
            db,
            workspace_id=workspace.id,
            user_id=owner_user_id,
            type=NotificationType.lead_assigned,  # Reuse this type
            title="New deal assigned",
            body=f"{deal.name}",
            target_url=f"/deals/{deal.id}",
            meta={"deal_id": deal.id},
        )
    
    logger.info(f"Created deal {deal.id}: {deal.name} in workspace {workspace.id}")
    return deal


@router.patch("/{deal_id}", response_model=DealOut)
def update_deal(
    deal_id: int,
    body: UpdateDealRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Update a deal"""
    deal = db.query(DealORM).filter(
        DealORM.id == deal_id,
        DealORM.workspace_id == workspace.id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    old_stage = deal.stage
    
    # Update fields
    if body.name is not None:
        deal.name = body.name
    if body.company_id is not None:
        deal.company_id = body.company_id
    if body.primary_lead_id is not None:
        deal.primary_lead_id = body.primary_lead_id
    if body.owner_user_id is not None:
        deal.owner_user_id = body.owner_user_id
    if body.stage is not None:
        deal.stage = body.stage
        # Auto-set won_at/lost_at when stage changes
        if body.stage == DealStage.won and not deal.won_at:
            deal.won_at = datetime.utcnow()
        elif body.stage == DealStage.lost and not deal.lost_at:
            deal.lost_at = datetime.utcnow()
            if body.lost_reason:
                deal.lost_reason = body.lost_reason
    if body.value is not None:
        deal.value = body.value
    if body.currency is not None:
        deal.currency = body.currency
    if body.expected_close_date is not None:
        deal.expected_close_date = body.expected_close_date
    if body.lost_reason is not None:
        deal.lost_reason = body.lost_reason
    
    deal.updated_at = datetime.utcnow()
    db.add(deal)
    db.commit()
    db.refresh(deal)
    
    # Log stage change activity
    if body.stage is not None and body.stage != old_stage:
        log_activity(
            db,
            organization_id=deal.organization_id,
            workspace_id=workspace.id,
            type=ActivityType.deal_stage_changed,
            actor_user_id=current_user.id,
            lead_id=deal.primary_lead_id,
            deal_id=deal.id,
            meta={
                "old_stage": old_stage.value,
                "new_stage": body.stage.value,
                "deal_name": deal.name,
            }
        )
        
        # Log won/lost events
        if body.stage == DealStage.won:
            log_activity(
                db,
                organization_id=deal.organization_id,
                workspace_id=workspace.id,
                type=ActivityType.deal_won,
                actor_user_id=current_user.id,
                lead_id=deal.primary_lead_id,
                deal_id=deal.id,
                meta={
                    "deal_name": deal.name,
                    "value": float(deal.value) if deal.value else None,
                }
            )
        elif body.stage == DealStage.lost:
            log_activity(
                db,
                organization_id=deal.organization_id,
                workspace_id=workspace.id,
                type=ActivityType.deal_lost,
                actor_user_id=current_user.id,
                lead_id=deal.primary_lead_id,
                deal_id=deal.id,
                meta={
                    "deal_name": deal.name,
                    "lost_reason": body.lost_reason,
                }
            )
    
    logger.info(f"Updated deal {deal.id}: {deal.name}")
    return deal


@router.get("/pipeline/summary")
def get_pipeline_summary(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get pipeline summary (value by stage, counts, etc.)"""
    deals = db.query(DealORM).filter(DealORM.workspace_id == workspace.id).all()
    
    # Calculate totals by stage
    stage_totals = {}
    stage_counts = {}
    for stage in DealStage:
        stage_deals = [d for d in deals if d.stage == stage]
        stage_counts[stage.value] = len(stage_deals)
        stage_totals[stage.value] = sum(float(d.value or 0) for d in stage_deals)
    
    # In-progress (all except won/lost)
    in_progress_deals = [d for d in deals if d.stage not in [DealStage.won, DealStage.lost]]
    in_progress_value = sum(float(d.value or 0) for d in in_progress_deals)
    
    # Won deals (last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    won_recent = [d for d in deals if d.stage == DealStage.won and d.won_at and d.won_at >= thirty_days_ago]
    won_recent_value = sum(float(d.value or 0) for d in won_recent)
    
    # Win rate (last 90 days)
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    closed_recent = [d for d in deals if (d.won_at or d.lost_at) and (d.won_at or d.lost_at) >= ninety_days_ago]
    won_recent_90 = [d for d in closed_recent if d.stage == DealStage.won]
    win_rate = (len(won_recent_90) / len(closed_recent) * 100) if closed_recent else 0
    
    # Average days to close (won deals)
    won_deals = [d for d in deals if d.stage == DealStage.won and d.won_at and d.created_at]
    avg_days_to_close = None
    if won_deals:
        days_list = [(d.won_at - d.created_at).days for d in won_deals if d.won_at and d.created_at]
        if days_list:
            avg_days_to_close = sum(days_list) / len(days_list)
    
    return {
        "stage_counts": stage_counts,
        "stage_totals": stage_totals,
        "in_progress_value": in_progress_value,
        "in_progress_count": len(in_progress_deals),
        "won_recent_value": won_recent_value,
        "won_recent_count": len(won_recent),
        "win_rate": round(win_rate, 1),
        "avg_days_to_close": round(avg_days_to_close, 1) if avg_days_to_close else None,
        "total_deals": len(deals),
    }

