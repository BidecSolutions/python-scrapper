"""Tasks and Notes ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey, 
    Enum as SQLEnum, Text, Index, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.core.db import Base


class TaskStatus(str, PyEnum):
    """Task status"""
    open = "open"
    done = "done"
    cancelled = "cancelled"


class TaskType(str, PyEnum):
    """Task type"""
    follow_up = "follow_up"
    call = "call"
    email = "email"
    enrich = "enrich"
    add_to_campaign = "add_to_campaign"
    custom = "custom"


class LeadNoteORM(Base):
    """Lead note model"""
    __tablename__ = "lead_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationships
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True)  # Made nullable for deal notes
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True)  # Link to deal
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)  # Up to 2000 chars
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    organization = relationship("OrganizationORM", foreign_keys=[organization_id])
    lead = relationship("LeadORM", back_populates="notes")
    user = relationship("UserORM", foreign_keys=[user_id])
    
    __table_args__ = (
        Index("idx_lead_note_lead", "lead_id"),
        Index("idx_lead_note_user", "user_id"),
        Index("idx_lead_note_created", "created_at"),
    )


class LeadTaskORM(Base):
    """Lead task model"""
    __tablename__ = "lead_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationships
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True)  # Made nullable for deal tasks
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True)  # Link to deal
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # Can assign to different user
    
    # Task details
    title = Column(String(255), nullable=False)
    type = Column(SQLEnum(TaskType), nullable=False, default=TaskType.custom, index=True)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.open, index=True)
    
    # Dates
    due_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional description
    description = Column(Text, nullable=True)
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    organization = relationship("OrganizationORM", foreign_keys=[organization_id])
    lead = relationship("LeadORM", back_populates="tasks")
    user = relationship("UserORM", foreign_keys=[user_id])
    assigned_to = relationship("UserORM", foreign_keys=[assigned_to_user_id])
    
    __table_args__ = (
        Index("idx_lead_task_lead", "lead_id"),
        Index("idx_lead_task_user", "user_id"),
        Index("idx_lead_task_status", "status"),
        Index("idx_lead_task_due", "due_at"),
        Index("idx_lead_task_workspace_status", "workspace_id", "status"),
    )

