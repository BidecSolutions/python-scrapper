"""Template Library & Governance ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey, 
    Enum as SQLEnum, Text, Boolean, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.core.db import Base
from app.core.orm import JsonType


class TemplateScope(str, PyEnum):
    """Template visibility scope"""
    workspace = "workspace"
    global_scope = "global"


class TemplateStatus(str, PyEnum):
    """Template approval status"""
    draft = "draft"
    pending_approval = "pending_approval"
    approved = "approved"
    deprecated = "deprecated"
    rejected = "rejected"


class TemplateKind(str, PyEnum):
    """Template type"""
    email = "email"
    subject = "subject"
    sequence_step = "sequence_step"


class TemplateORM(Base):
    """Email template model"""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    scope = Column(SQLEnum(TemplateScope), nullable=False, default=TemplateScope.workspace, index=True)
    
    # Template info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    kind = Column(SQLEnum(TemplateKind), nullable=False, default=TemplateKind.email, index=True)
    
    # Content
    subject = Column(String(255), nullable=True)  # For email templates
    body = Column(Text, nullable=True)  # Main template content
    
    # Status & governance
    status = Column(SQLEnum(TemplateStatus), nullable=False, default=TemplateStatus.draft, index=True)
    locked = Column(Boolean, nullable=False, default=False)
    
    # Ownership & approval
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Metadata
    tags = Column(JsonType, nullable=True)  # ["outbound", "cold", "followup"]
    meta = Column(JsonType, nullable=True)  # Rejection reason, notes, etc.
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    created_by = relationship("UserORM", foreign_keys=[created_by_user_id])
    approved_by = relationship("UserORM", foreign_keys=[approved_by_user_id])
    
    __table_args__ = (
        Index("idx_template_workspace_status", "workspace_id", "status"),
        Index("idx_template_created_by", "created_by_user_id"),
    )


class TemplateGovernanceORM(Base):
    """Template governance rules per workspace"""
    __tablename__ = "template_governance"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Governance rules
    require_approval_for_new_templates = Column(Boolean, nullable=False, default=False)
    restrict_to_approved_only = Column(Boolean, nullable=False, default=False)
    allow_personal_templates = Column(Boolean, nullable=False, default=True)
    require_unsubscribe = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])

