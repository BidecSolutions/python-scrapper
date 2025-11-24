"""Deals/Opportunities ORM model"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey, 
    Enum as SQLEnum, Text, Numeric, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.core.db import Base
from app.core.orm import JsonType


class DealStage(str, PyEnum):
    """Deal pipeline stages"""
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    meeting_scheduled = "meeting_scheduled"
    proposal = "proposal"
    won = "won"
    lost = "lost"


class DealORM(Base):
    """Deal/Opportunity model"""
    __tablename__ = "deals"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Deal info
    name = Column(String(255), nullable=False, index=True)
    
    # Related entities
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    primary_lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Ownership
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Pipeline
    stage = Column(SQLEnum(DealStage), nullable=False, default=DealStage.new, index=True)
    value = Column(Numeric(12, 2), nullable=True)  # Estimated deal value
    currency = Column(String(10), nullable=False, default="USD")
    expected_close_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Source tracking
    source_campaign_id = Column(Integer, nullable=True, index=True)  # CampaignORM may not exist yet
    source_segment_id = Column(Integer, ForeignKey("segments.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Loss tracking
    lost_reason = Column(Text, nullable=True)
    lost_at = Column(DateTime(timezone=True), nullable=True)
    won_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    organization = relationship("OrganizationORM", foreign_keys=[organization_id])
    company = relationship("CompanyORM", foreign_keys=[company_id])
    primary_lead = relationship("LeadORM", foreign_keys=[primary_lead_id])
    owner = relationship("UserORM", foreign_keys=[owner_user_id])
    source_segment = relationship("SegmentORM", foreign_keys=[source_segment_id])
    
    __table_args__ = (
        Index("idx_deal_workspace_stage", "workspace_id", "stage"),
        Index("idx_deal_owner_stage", "owner_user_id", "stage"),
        Index("idx_deal_expected_close", "expected_close_date"),
    )

