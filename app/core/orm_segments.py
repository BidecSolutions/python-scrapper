"""Segment ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey, 
    Text, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db import Base
from app.core.orm import JsonType


class SegmentORM(Base):
    """Saved segment (ICP filter)"""
    __tablename__ = "segments"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)  # Workspace for team collaboration
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Segment info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Filter criteria (JSON)
    filter_json = Column(JsonType, nullable=False, default=dict)
    # Example:
    # {
    #   "sources": ["linkedin_extension"],
    #   "countries": ["United States"],
    #   "min_score": 70,
    #   "roles_contains": ["founder", "ceo"],
    #   "company_sizes": ["11-50", "51-200"]
    # }
    
    # Relationships
    organization = relationship("OrganizationORM")
    created_by = relationship("UserORM")
    
    __table_args__ = (
        Index("idx_segment_org", "organization_id"),
        Index("idx_segment_name", "name"),
    )

