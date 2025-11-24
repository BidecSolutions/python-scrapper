"""Notification service for creating notifications"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.orm_notifications import NotificationORM, NotificationType

logger = logging.getLogger(__name__)


def create_notification(
    db: Session,
    *,
    workspace_id: int,
    type: NotificationType,
    title: str,
    body: Optional[str] = None,
    user_id: Optional[int] = None,
    target_url: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> NotificationORM:
    """Create a notification"""
    notif = NotificationORM(
        workspace_id=workspace_id,
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        target_url=target_url,
        meta=meta or {},
    )
    db.add(notif)
    db.flush()
    logger.info(f"Created notification: {type} for user {user_id} in workspace {workspace_id}")
    return notif

