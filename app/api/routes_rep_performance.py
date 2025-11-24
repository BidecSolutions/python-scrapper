"""Rep Performance & Leaderboard API routes"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.db import get_db
from app.api.routes_settings import get_or_create_default_org
from app.api.routes_workspaces import get_current_user_id
from app.services.rep_performance_service import get_rep_performance, get_rep_leaderboard, RepPerformance
from app.services.workspace_permissions import require_workspace_member

logger = logging.getLogger(__name__)
router = APIRouter()


class RepPerformanceOut(BaseModel):
    """Rep performance response"""
    user_id: int
    name: str
    email: str
    role: Optional[str] = None
    
    new_leads_owned: int
    leads_worked: int
    
    tasks_created: int
    tasks_completed: int
    task_completion_rate: float
    
    campaign_leads_sent: int
    campaign_opens: int
    campaign_replies: int
    campaign_bounces: int
    campaign_reply_rate: float
    campaign_open_rate: float
    campaign_bounce_rate: float
    
    source_breakdown: dict
    
    class Config:
        from_attributes = True


@router.get("/reports/rep-performance", response_model=List[RepPerformanceOut])
def get_rep_performance_report(
    workspace_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[int] = Query(None, description="Get specific user's performance"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Get rep performance metrics for workspace members
    
    Returns performance data for all members or a specific user.
    """
    org = get_or_create_default_org(db)
    
    # Verify workspace membership if workspace_id provided
    if workspace_id:
        from app.services.workspace_permissions import require_workspace_member
        require_workspace_member(db, workspace_id, current_user_id)
    
    # If user_id provided and not current user, verify permissions
    if user_id and user_id != current_user_id:
        # Only allow if user is admin/owner or viewing own stats
        if workspace_id:
            from app.services.workspace_permissions import require_role, WorkspaceRole
            try:
                require_role(db, workspace_id, current_user_id, [WorkspaceRole.owner, WorkspaceRole.admin])
            except HTTPException:
                raise HTTPException(status_code=403, detail="Only admins can view other users' performance")
    
    results = get_rep_performance(
        db=db,
        organization_id=org.id,
        workspace_id=workspace_id,
        days=days,
        user_id=user_id,
    )
    
    return [
        RepPerformanceOut(
            user_id=r.user_id,
            name=r.name,
            email=r.email,
            role=r.role,
            new_leads_owned=r.new_leads_owned,
            leads_worked=r.leads_worked,
            tasks_created=r.tasks_created,
            tasks_completed=r.tasks_completed,
            task_completion_rate=r.task_completion_rate,
            campaign_leads_sent=r.campaign_leads_sent,
            campaign_opens=r.campaign_opens,
            campaign_replies=r.campaign_replies,
            campaign_bounces=r.campaign_bounces,
            campaign_reply_rate=r.campaign_reply_rate,
            campaign_open_rate=r.campaign_open_rate,
            campaign_bounce_rate=r.campaign_bounce_rate,
            source_breakdown=r.source_breakdown,
        )
        for r in results
    ]


@router.get("/reports/leaderboard", response_model=List[RepPerformanceOut])
def get_leaderboard(
    workspace_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    sort_by: str = Query("replies", description="Sort by: replies, leads_worked, tasks_completed, reply_rate"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Get rep leaderboard sorted by specified metric
    
    Returns sorted list of reps by performance metric.
    """
    org = get_or_create_default_org(db)
    
    # Verify workspace membership if workspace_id provided
    if workspace_id:
        from app.services.workspace_permissions import require_workspace_member
        require_workspace_member(db, workspace_id, current_user_id)
    
    results = get_rep_leaderboard(
        db=db,
        organization_id=org.id,
        workspace_id=workspace_id,
        days=days,
        sort_by=sort_by,
    )
    
    return [
        RepPerformanceOut(
            user_id=r.user_id,
            name=r.name,
            email=r.email,
            role=r.role,
            new_leads_owned=r.new_leads_owned,
            leads_worked=r.leads_worked,
            tasks_created=r.tasks_created,
            tasks_completed=r.tasks_completed,
            task_completion_rate=r.task_completion_rate,
            campaign_leads_sent=r.campaign_leads_sent,
            campaign_opens=r.campaign_opens,
            campaign_replies=r.campaign_replies,
            campaign_bounces=r.campaign_bounces,
            campaign_reply_rate=r.campaign_reply_rate,
            campaign_open_rate=r.campaign_open_rate,
            campaign_bounce_rate=r.campaign_bounce_rate,
            source_breakdown=r.source_breakdown,
        )
        for r in results
    ]


@router.get("/reports/users/{user_id}/performance", response_model=RepPerformanceOut)
def get_user_performance(
    user_id: int,
    workspace_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Get performance metrics for a specific user
    
    Users can view their own stats, admins/owners can view anyone's.
    """
    org = get_or_create_default_org(db)
    
    # Verify permissions
    if user_id != current_user_id:
        if workspace_id:
            from app.services.workspace_permissions import require_role, WorkspaceRole
            require_role(db, workspace_id, current_user_id, [WorkspaceRole.owner, WorkspaceRole.admin])
        else:
            raise HTTPException(status_code=403, detail="Cannot view other users' performance without workspace context")
    
    results = get_rep_performance(
        db=db,
        organization_id=org.id,
        workspace_id=workspace_id,
        days=days,
        user_id=user_id,
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="User not found or no performance data")
    
    r = results[0]
    return RepPerformanceOut(
        user_id=r.user_id,
        name=r.name,
        email=r.email,
        role=r.role,
        new_leads_owned=r.new_leads_owned,
        leads_worked=r.leads_worked,
        tasks_created=r.tasks_created,
        tasks_completed=r.tasks_completed,
        task_completion_rate=r.task_completion_rate,
        campaign_leads_sent=r.campaign_leads_sent,
        campaign_opens=r.campaign_opens,
        campaign_replies=r.campaign_replies,
        campaign_bounces=r.campaign_bounces,
        campaign_reply_rate=r.campaign_reply_rate,
        campaign_open_rate=r.campaign_open_rate,
        campaign_bounce_rate=r.campaign_bounce_rate,
        source_breakdown=r.source_breakdown,
    )

