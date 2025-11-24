"""Activity logging service"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.orm_activity import ActivityORM, ActivityType

logger = logging.getLogger(__name__)


def log_activity(
    db: Session,
    *,
    organization_id: int,
    workspace_id: Optional[int] = None,
    type: ActivityType,
    actor_user_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    list_id: Optional[int] = None,
    campaign_id: Optional[int] = None,
    task_id: Optional[int] = None,
    job_id: Optional[int] = None,
    note_id: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> ActivityORM:
    """
    Log an activity event
    
    Args:
        db: Database session
        organization_id: Organization ID (required)
        workspace_id: Workspace ID (optional, for workspace-scoped events)
        type: Activity type
        actor_user_id: User who performed the action (optional for system events)
        lead_id: Related lead ID (optional)
        list_id: Related list ID (optional)
        campaign_id: Related campaign ID (optional)
        task_id: Related task ID (optional)
        job_id: Related job ID (optional)
        note_id: Related note ID (optional)
        meta: Additional metadata (dict)
    
    Returns:
        Created ActivityORM instance
    """
    activity = ActivityORM(
        organization_id=organization_id,
        workspace_id=workspace_id,
        type=type,
        actor_user_id=actor_user_id,
        lead_id=lead_id,
        list_id=list_id,
        campaign_id=campaign_id,
        task_id=task_id,
        job_id=job_id,
        note_id=note_id,
        meta=meta or {},
    )
    
    db.add(activity)
    db.commit()
    db.refresh(activity)
    
    logger.debug(f"Logged activity: {type.value} for lead {lead_id} in workspace {workspace_id}")
    
    return activity

