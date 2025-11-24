"""Workspace Integration ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey, 
    Text, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db import Base


class OrganizationIntegrationORM(Base):
    """Organization-level integration (CRM, etc.)"""
    __tablename__ = "organization_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)  # Workspace for team collaboration
    
    # Integration info
    type = Column(String(50), nullable=False, index=True)  # "hubspot", "salesforce", etc.
    
    # Credentials (should be encrypted in production)
    access_token = Column(String(512), nullable=False)  # Store encrypted
    refresh_token = Column(String(512), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(String(20), nullable=False, default="active")  # "active", "inactive", "error"
    error_message = Column(Text, nullable=True)
    
    # Additional config (JSON)
    config = Column(Text, nullable=True)  # Store as JSON string for flexibility
    
    # Relationships
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        Index("idx_integration_org_type", "organization_id", "type"),
        UniqueConstraint("organization_id", "type", name="uq_org_integration_type"),
    )

