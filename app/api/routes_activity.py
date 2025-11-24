"""Activity timeline API routes"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.db import get_db
from app.core.orm import LeadORM, OrganizationORM
from app.core.orm_activity import ActivityORM, ActivityType
from app.api.routes_settings import get_or_create_default_org
from app.api.routes_workspaces import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter()


class ActivityOut(BaseModel):
    """Activity response"""
    id: int
    type: str
    actor_user_id: Optional[int] = None
    actor_user_name: Optional[str] = None
    lead_id: Optional[int] = None
    list_id: Optional[int] = None
    campaign_id: Optional[int] = None
    task_id: Optional[int] = None
    job_id: Optional[int] = None
    note_id: Optional[int] = None
    meta: dict
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/leads/{lead_id}/activity", response_model=List[ActivityOut])
def get_lead_activity(
    lead_id: int,
    limit: int = Query(50, ge=1, le=200),
    before: Optional[int] = Query(None, description="Cursor: activity ID to fetch before"),
    db: Session = Depends(get_db),
):
    """Get activity timeline for a specific lead"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    query = db.query(ActivityORM).filter(
        ActivityORM.lead_id == lead_id,
        ActivityORM.organization_id == org.id
    )
    
    if before:
        query = query.filter(ActivityORM.id < before)
    
    activities = query.order_by(ActivityORM.created_at.desc()).limit(limit).all()
    
    result = []
    for activity in activities:
        actor_user_name = None
        if activity.actor_user:
            actor_user_name = activity.actor_user.full_name or activity.actor_user.email
        
        result.append(ActivityOut(
            id=activity.id,
            type=activity.type.value,
            actor_user_id=activity.actor_user_id,
            actor_user_name=actor_user_name,
            lead_id=activity.lead_id,
            list_id=activity.list_id,
            campaign_id=activity.campaign_id,
            task_id=activity.task_id,
            job_id=activity.job_id,
            note_id=activity.note_id,
            meta=activity.meta or {},
            created_at=activity.created_at.isoformat(),
        ))
    
    return result


@router.get("/activity", response_model=List[ActivityOut])
def get_workspace_activity(
    workspace_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    before: Optional[int] = Query(None, description="Cursor: activity ID to fetch before"),
    type_filter: Optional[str] = Query(None, description="Filter by activity type"),
    user_id: Optional[int] = Query(None, description="Filter by actor user ID"),
    db: Session = Depends(get_db),
):
    """Get workspace activity feed"""
    org = get_or_create_default_org(db)
    
    query = db.query(ActivityORM).filter(
        ActivityORM.organization_id == org.id
    )
    
    if workspace_id:
        query = query.filter(ActivityORM.workspace_id == workspace_id)
    
    if type_filter:
        try:
            activity_type = ActivityType(type_filter)
            query = query.filter(ActivityORM.type == activity_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid activity type: {type_filter}")
    
    if user_id:
        query = query.filter(ActivityORM.actor_user_id == user_id)
    
    if before:
        query = query.filter(ActivityORM.id < before)
    
    activities = query.order_by(ActivityORM.created_at.desc()).limit(limit).all()
    
    result = []
    for activity in activities:
        actor_user_name = None
        if activity.actor_user:
            actor_user_name = activity.actor_user.full_name or activity.actor_user.email
        
        result.append(ActivityOut(
            id=activity.id,
            type=activity.type.value,
            actor_user_id=activity.actor_user_id,
            actor_user_name=actor_user_name,
            lead_id=activity.lead_id,
            list_id=activity.list_id,
            campaign_id=activity.campaign_id,
            task_id=activity.task_id,
            job_id=activity.job_id,
            note_id=activity.note_id,
            meta=activity.meta or {},
            created_at=activity.created_at.isoformat(),
        ))
    
    return result

