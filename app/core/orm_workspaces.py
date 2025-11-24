"""Workspace and Team ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey, 
    Enum as SQLEnum, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.core.db import Base


class WorkspaceRole(str, PyEnum):
    """Workspace member roles"""
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class WorkspaceORM(Base):
    """Workspace model (team collaboration unit)"""
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Links to organization (for billing/credits)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Optional workspace-level plan override (inherits from org if null)
    plan_tier = Column(String(50), nullable=True)  # "free", "starter", "pro", etc.
    
    # Settings
    settings = Column(Text, nullable=True)  # JSON string for workspace-specific settings
    
    # Agency (if this is a client workspace under an agency)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    organization = relationship("OrganizationORM", foreign_keys=[organization_id])
    members = relationship("WorkspaceMemberORM", back_populates="workspace", cascade="all, delete-orphan")
    agency = relationship("app.core.orm_agency.AgencyORM", foreign_keys=[agency_id], back_populates="client_workspaces")
    saved_views = relationship("app.core.orm_saved_views.SavedViewORM", back_populates="workspace", cascade="all, delete-orphan")
    duplicate_groups = relationship("app.core.orm_duplicates.DuplicateGroupORM", back_populates="workspace", cascade="all, delete-orphan")
    
    # Shared resources (will be added via foreign keys in other models)
    # leads = relationship("LeadORM", back_populates="workspace")
    # lists = relationship("LeadListORM", back_populates="workspace")
    # jobs = relationship("ScrapeJobORM", back_populates="workspace")
    
    __table_args__ = (
        Index("idx_workspace_org", "organization_id"),
        Index("idx_workspace_slug", "slug"),
    )


class WorkspaceMemberORM(Base):
    """Workspace membership (user-workspace relationship with role)"""
    __tablename__ = "workspace_members"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # Nullable for pending invites
    
    role = Column(SQLEnum(WorkspaceRole), nullable=False, default=WorkspaceRole.member, index=True)
    
    # Invite system
    invited_email = Column(String(255), nullable=True, index=True)  # For pending invites (user not yet created)
    invited_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    invite_token = Column(String(255), nullable=True, unique=True, index=True)  # Token for invite acceptance
    invited_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Last active (for display)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspace = relationship("WorkspaceORM", back_populates="members")
    user = relationship("app.core.orm.UserORM", foreign_keys=[user_id])
    invited_by = relationship("app.core.orm.UserORM", foreign_keys=[invited_by_user_id])
    
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
        UniqueConstraint("workspace_id", "invited_email", name="uq_workspace_invite_email"),
        Index("idx_workspace_member_workspace", "workspace_id"),
        Index("idx_workspace_member_user", "user_id"),
        Index("idx_workspace_member_role", "role"),
    )

