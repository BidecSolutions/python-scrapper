"""Notification ORM model"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, func, ForeignKey, 
    Enum as SQLEnum, Text, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.core.db import Base
from app.core.orm import JsonType


class NotificationType(str, PyEnum):
    """Notification types"""
    task_assigned = "task_assigned"
    task_due_soon = "task_due_soon"
    lead_assigned = "lead_assigned"
    reply_received = "reply_received"
    bounce_detected = "bounce_detected"
    playbook_failed = "playbook_failed"
    playbook_completed = "playbook_completed"
    critical_audit = "critical_audit"


class NotificationORM(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Multi-tenant
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Who is this for? (null = workspace-level, show to admins)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Notification content
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    
    # Where clicking should send the user
    target_url = Column(String(500), nullable=True)
    
    # Extra context
    meta = Column(JsonType, nullable=False, default=dict)
    
    # Status
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    is_archived = Column(Boolean, nullable=False, default=False, index=True)
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    user = relationship("UserORM", foreign_keys=[user_id])
    
    __table_args__ = (
        Index("idx_notification_workspace_user_read", "workspace_id", "user_id", "is_read"),
        Index("idx_notification_created", "created_at"),
    )

