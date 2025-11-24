"""Playbook Job ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, func, ForeignKey, 
    Enum as SQLEnum, Text, Index, Numeric
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.core.db import Base
from app.core.orm import JsonType


class PlaybookJobStatus(str, PyEnum):
    """Playbook job status"""
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class PlaybookJobType(str, PyEnum):
    """Playbook job types"""
    linkedin_campaign = "linkedin_campaign"


class PlaybookJobORM(Base):
    """Playbook execution job"""
    __tablename__ = "playbook_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)  # Workspace for team collaboration
    
    # Job info
    type = Column(String(50), nullable=False, index=True)  # "linkedin_campaign"
    status = Column(String(20), nullable=False, default=PlaybookJobStatus.queued.value, index=True)
    error_message = Column(Text, nullable=True)
    
    # Parameters (JSON)
    params = Column(JsonType, nullable=False, default=dict)  # {days, include_risky, min_score, list_name}
    
    # Progress tracking (meta JSON)
    meta = Column(JsonType, nullable=False, default=dict)  # {total_leads, processed_leads, emails_found, etc.}
    
    # Output
    output_list_id = Column(Integer, ForeignKey("lead_lists.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Credits
    estimated_credits = Column(Integer, nullable=True)
    credits_used = Column(Integer, nullable=False, default=0)
    
    # Relationships
    organization = relationship("OrganizationORM")
    output_list = relationship("LeadListORM", foreign_keys=[output_list_id])
    
    __table_args__ = (
        Index("idx_playbook_job_org_status", "organization_id", "status"),
        Index("idx_playbook_job_created", "created_at"),
    )

