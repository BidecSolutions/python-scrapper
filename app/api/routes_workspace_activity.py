"""Workspace-scoped activity routes"""
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
from app.api.routes_workspaces import get_current_workspace
from app.core.orm import UserORM
from app.core.orm_workspaces import WorkspaceORM

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/activity", tags=["activity"])


class WorkspaceActivityItem(BaseModel):
    id: int
    actor_user_id: Optional[int]
    type: ActivityType
    meta: dict
    created_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode = True


class WorkspaceActivityListResponse(BaseModel):
    items: List[WorkspaceActivityItem]
    total: int
    page: int
    page_size: int


@router.get("", response_model=WorkspaceActivityListResponse)
def list_workspace_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    type: Optional[str] = None,  # ActivityType as string
    actor_user_id: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """List activity for current workspace"""
    q = db.query(ActivityORM).filter(ActivityORM.workspace_id == workspace.id)
    
    if type is not None:
        try:
            activity_type = ActivityType(type)
            q = q.filter(ActivityORM.type == activity_type)
        except ValueError:
            pass  # Invalid type, ignore

    if actor_user_id is not None:
        q = q.filter(ActivityORM.actor_user_id == actor_user_id)

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
    
    return WorkspaceActivityListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/workspace", response_model=WorkspaceActivityListResponse)
def list_workspace_activity_alias(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    type: Optional[str] = None,
    actor_user_id: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Alias for list_workspace_activity (frontend compatibility)."""
    return list_workspace_activity(
        page=page,
        page_size=page_size,
        type=type,
        actor_user_id=actor_user_id,
        since=since,
        until=until,
        db=db,
        current_user=current_user,
        workspace=workspace,
    )


@router.get("/export/csv")
def export_activity_csv(
    type: Optional[str] = None,
    actor_user_id: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Export workspace activity to CSV."""
    q = db.query(ActivityORM).filter(ActivityORM.workspace_id == workspace.id)

    if type is not None:
        try:
            activity_type = ActivityType(type)
            q = q.filter(ActivityORM.type == activity_type)
        except ValueError:
            pass

    if actor_user_id is not None:
        q = q.filter(ActivityORM.actor_user_id == actor_user_id)

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

    rows = ["id,type,actor_user_id,lead_id,job_id,created_at,meta"]
    for item in items:
        meta_text = (item.meta or {})
        rows.append(
            f"{item.id},{item.type.value},{item.actor_user_id or ''},{item.lead_id or ''},{item.job_id or ''},{item.created_at.isoformat()},{str(meta_text).replace(',', ';')}"
        )

    csv_content = "\n".join(rows)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=activity.csv"},
    )

