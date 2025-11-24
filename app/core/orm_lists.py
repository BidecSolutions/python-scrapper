"""LeadList ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, func, ForeignKey, 
    Enum as SQLEnum, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db import Base


class LeadListORM(Base):
    """Lead list model for organizing leads"""
    __tablename__ = "lead_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)  # Workspace for team collaboration
    
    # List info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Metadata
    is_campaign_ready = Column(Boolean, nullable=False, default=False)  # Marked as ready for campaigns
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Relationships
    organization = relationship("OrganizationORM", back_populates="lead_lists")
    list_leads = relationship("LeadListLeadORM", back_populates="list", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_lead_list_org_name", "organization_id", "name"),
    )


class LeadListLeadORM(Base):
    """Junction table for leads in lists"""
    __tablename__ = "lead_list_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Foreign keys
    list_id = Column(Integer, ForeignKey("lead_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metadata
    added_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)  # Optional notes about this lead in this list
    
    # Relationships
    list = relationship("LeadListORM", back_populates="list_leads")
    lead = relationship("LeadORM", back_populates="list_memberships")
    added_by = relationship("UserORM")
    
    __table_args__ = (
        UniqueConstraint("list_id", "lead_id", name="uq_lead_list_lead"),
        Index("idx_lead_list_lead_list", "list_id"),
        Index("idx_lead_list_lead_lead", "lead_id"),
    )

