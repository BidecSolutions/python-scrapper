"""AI Lookalike & Expansion Engine ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey, 
    Enum as SQLEnum, Float, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.core.db import Base
from app.core.orm import JsonType


class LookalikeJobStatus(str, PyEnum):
    """Lookalike job status"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class LookalikeJobORM(Base):
    """Lookalike job model"""
    __tablename__ = "lookalike_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Multi-tenant
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Job info
    started_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # Input source: segment / list / campaign
    source_segment_id = Column(Integer, ForeignKey("segments.id", ondelete="SET NULL"), nullable=True, index=True)
    source_list_id = Column(Integer, ForeignKey("lead_lists.id", ondelete="SET NULL"), nullable=True, index=True)
    source_campaign_id = Column(Integer, nullable=True, index=True)  # CampaignORM may not exist yet
    
    # Job status
    status = Column(SQLEnum(LookalikeJobStatus), nullable=False, default=LookalikeJobStatus.pending, index=True)
    
    # Results summary
    positive_lead_count = Column(Integer, nullable=False, default=0)  # How many "examples"
    candidates_found = Column(Integer, nullable=False, default=0)  # How many lookalikes found
    
    # Profile embedding (stored as JSON array for SQLite compatibility)
    profile_embedding = Column(JsonType, nullable=True)  # Centroid embedding of positive examples
    
    # Metadata
    meta = Column(JsonType, nullable=True)  # Error messages, filters applied, etc.
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    organization = relationship("OrganizationORM", foreign_keys=[organization_id])
    started_by = relationship("UserORM", foreign_keys=[started_by_user_id])
    source_segment = relationship("SegmentORM", foreign_keys=[source_segment_id])
    source_list = relationship("LeadListORM", foreign_keys=[source_list_id])
    candidates = relationship("LookalikeCandidateORM", back_populates="job", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_lookalike_job_workspace_status", "workspace_id", "status"),
        Index("idx_lookalike_job_created", "created_at"),
    )


class LookalikeCandidateORM(Base):
    """Lookalike candidate result"""
    __tablename__ = "lookalike_candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Job reference
    job_id = Column(Integer, ForeignKey("lookalike_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Multi-tenant
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Candidate lead/company
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Similarity score (0-1 or 0-100)
    score = Column(Float, nullable=False, index=True)
    
    # Reason vector: which features contributed most
    # e.g. {"industry": 0.9, "size": 0.7, "tech": 0.8, "geo": 0.6}
    reason_vector = Column(JsonType, nullable=True)
    
    # Relationships
    job = relationship("LookalikeJobORM", back_populates="candidates")
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    lead = relationship("LeadORM", foreign_keys=[lead_id])
    company = relationship("CompanyORM", foreign_keys=[company_id])
    
    __table_args__ = (
        Index("idx_lookalike_candidate_job_score", "job_id", "score"),
        Index("idx_lookalike_candidate_lead", "lead_id"),
        Index("idx_lookalike_candidate_company", "company_id"),
    )

