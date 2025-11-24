"""API Keys ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, func, ForeignKey, 
    Text, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.core.db import Base


class ApiKeyScope(str, PyEnum):
    """API key scopes"""
    leads_read = "leads:read"
    leads_write = "leads:write"
    jobs_read = "jobs:read"
    jobs_write = "jobs:write"
    lists_read = "lists:read"
    lists_write = "lists:write"
    playbooks_read = "playbooks:read"
    playbooks_write = "playbooks:write"
    segments_read = "segments:read"
    segments_write = "segments:write"
    email_verify = "email:verify"
    email_find = "email:find"
    company_search = "company:search"
    # Admin scopes
    workspace_read = "workspace:read"
    workspace_write = "workspace:write"


class APIKeyORM(Base):
    """API Key model (workspace-scoped)"""
    __tablename__ = "api_keys"  # Using same table name as original for compatibility
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Workspace (replaces organization_id for new keys)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)  # For backward compatibility
    
    # Key info
    name = Column(String(255), nullable=False, index=True)  # "LinkedIn extension", "Reporting script"
    key_hash = Column(String(255), nullable=False, unique=True, index=True)  # SHA-256 hash of the key
    key_prefix = Column(String(20), nullable=True)  # First 8 chars for display (e.g., "bidec_liv...")
    
    # Scopes (comma-separated or JSON)
    scopes = Column(Text, nullable=False, default="")  # "leads:read,leads:write,jobs:write"
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, nullable=True)  # null = use default
    rate_limit_per_hour = Column(Integer, nullable=True)  # Optional hourly limit
    rate_limit_per_day = Column(Integer, nullable=True)  # Optional daily limit
    
    # Status
    active = Column(Boolean, nullable=False, default=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_used_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    total_requests = Column(Integer, nullable=False, default=0)
    
    # Metadata
    description = Column(Text, nullable=True)  # Optional description
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    organization = relationship("OrganizationORM", foreign_keys=[organization_id], back_populates="api_keys")
    created_by = relationship("UserORM", foreign_keys=[created_by_user_id])
    usage_records = relationship("UsageRecordORM", back_populates="api_key")
    
    __table_args__ = (
        Index("idx_api_key_workspace", "workspace_id"),
        Index("idx_api_key_hash", "key_hash"),
        Index("idx_api_key_active", "active"),
    )

