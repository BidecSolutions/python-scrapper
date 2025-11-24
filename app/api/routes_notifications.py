"""Notification routes"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from pydantic import BaseModel
from datetime import datetime

from app.core.db import get_db
from app.core.orm_notifications import NotificationORM, NotificationType
from app.api.routes_auth import get_current_user
from app.api.routes_workspaces import get_current_workspace, get_current_user_optional, get_current_workspace_optional
from app.core.orm import UserORM
from app.core.orm_workspaces import WorkspaceORM

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationItem(BaseModel):
    id: int
    type: NotificationType
    title: str
    body: Optional[str]
    target_url: Optional[str]
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode = True


class NotificationListResponse(BaseModel):
    items: List[NotificationItem]
    unread_count: int


class NotificationUpdateRequest(BaseModel):
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    only_unread: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """List notifications for current user"""
    q = db.query(NotificationORM).filter(
        NotificationORM.workspace_id == workspace.id,
        # Show user-specific or workspace-level (user_id is null)
        or_(
            NotificationORM.user_id == current_user.id,
            NotificationORM.user_id.is_(None),
        ),
        NotificationORM.is_archived.is_(False),
    )
    
    if only_unread:
        q = q.filter(NotificationORM.is_read.is_(False))
    
    items = (
        q.order_by(desc(NotificationORM.created_at))
        .limit(limit)
        .all()
    )
    
    # Unread count
    unread_count = (
        db.query(NotificationORM)
        .filter(
            NotificationORM.workspace_id == workspace.id,
            or_(
                NotificationORM.user_id == current_user.id,
                NotificationORM.user_id.is_(None),
            ),
            NotificationORM.is_archived.is_(False),
            NotificationORM.is_read.is_(False),
        )
        .count()
    )
    
    return NotificationListResponse(
        items=items,
        unread_count=unread_count,
    )


@router.patch("/{notification_id}", response_model=NotificationItem)
def update_notification(
    notification_id: int,
    body: NotificationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Update notification (mark read/archived)"""
    notif = db.query(NotificationORM).filter(
        NotificationORM.id == notification_id,
        NotificationORM.workspace_id == workspace.id,
    ).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Security: ensure user can access this notification
    if notif.user_id is not None and notif.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if body.is_read is not None:
        notif.is_read = body.is_read
    if body.is_archived is not None:
        notif.is_archived = body.is_archived
    
    db.add(notif)
    db.commit()
    db.refresh(notif)
    
    return notif


@router.post("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Mark all notifications as read"""
    (
        db.query(NotificationORM)
        .filter(
            NotificationORM.workspace_id == workspace.id,
            or_(
                NotificationORM.user_id == current_user.id,
                NotificationORM.user_id.is_(None),
            ),
            NotificationORM.is_read.is_(False),
            NotificationORM.is_archived.is_(False),
        )
        .update({"is_read": True}, synchronize_session=False)
    )
    db.commit()
    return {"ok": True}

