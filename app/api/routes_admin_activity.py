"""Admin activity routes (super admin only - global view)"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from datetime import datetime

from app.core.db import get_db
from app.core.orm_activity import ActivityORM, ActivityType
from app.api.routes_auth import get_current_user
from app.api.dependencies import require_super_admin
from app.core.orm import UserORM

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/activity", tags=["admin-activity"])


class AdminActivityItem(BaseModel):
    id: int
    workspace_id: Optional[int]
    actor_user_id: Optional[int]
    type: ActivityType
    meta: dict
    created_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode = True


class AdminActivityListResponse(BaseModel):
    items: List[AdminActivityItem]
    total: int
    page: int
    page_size: int


@router.get("", response_model=AdminActivityListResponse)
def list_global_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    workspace_id: Optional[int] = None,
    actor_user_id: Optional[int] = None,
    type: Optional[str] = None,  # ActivityType as string
    since: Optional[str] = None,
    until: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_super_admin),
):
    """List all activity across all workspaces (super admin only)"""
    q = db.query(ActivityORM)
    
    if workspace_id is not None:
        q = q.filter(ActivityORM.workspace_id == workspace_id)
    
    if actor_user_id is not None:
        q = q.filter(ActivityORM.actor_user_id == actor_user_id)
    
    if type is not None:
        try:
            activity_type = ActivityType(type)
            q = q.filter(ActivityORM.type == activity_type)
        except ValueError:
            pass  # Invalid type, ignore

    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            q = q.filter(ActivityORM.created_at >= since_dt)
        except ValueError:
            pass

    if until:
        try:
            until_dt = datetime.fromisoformat(until)
            q = q.filter(ActivityORM.created_at <= until_dt)
        except ValueError:
            pass
    
    total = q.count()
    
    items = (
        q.order_by(desc(ActivityORM.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    # Convert ORM objects to Pydantic models (Pydantic v2)
    admin_activities = [AdminActivityItem.model_validate(item) for item in items]
    
    return AdminActivityListResponse(
        items=admin_activities,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/export/csv")
def export_admin_activity_csv(
    workspace_id: Optional[int] = None,
    actor_user_id: Optional[int] = None,
    type: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_super_admin),
):
    """Export global activity for super admins to CSV."""
    q = db.query(ActivityORM)

    if workspace_id is not None:
        q = q.filter(ActivityORM.workspace_id == workspace_id)

    if actor_user_id is not None:
        q = q.filter(ActivityORM.actor_user_id == actor_user_id)

    if type is not None:
        try:
            activity_type = ActivityType(type)
            q = q.filter(ActivityORM.type == activity_type)
        except ValueError:
            pass

    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            q = q.filter(ActivityORM.created_at >= since_dt)
        except ValueError:
            pass

    if until:
        try:
            until_dt = datetime.fromisoformat(until)
            q = q.filter(ActivityORM.created_at <= until_dt)
        except ValueError:
            pass

    items = q.order_by(desc(ActivityORM.created_at)).limit(5000).all()

    rows = ["id,workspace_id,actor_user_id,type,lead_id,job_id,created_at,meta"]
    for item in items:
        meta_text = (item.meta or {})
        rows.append(
            f"{item.id},{item.workspace_id or ''},{item.actor_user_id or ''},{item.type.value},{item.lead_id or ''},{item.job_id or ''},{item.created_at.isoformat()},{str(meta_text).replace(',', ';')}"
        )

    csv_content = "\n".join(rows)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=admin_activity.csv"},
    )

