"""Duplicate Detection ORM - For tracking and merging duplicate leads"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text, Index, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base


class DuplicateGroupORM(Base):
    """Group of leads that are potential duplicates"""
    __tablename__ = "duplicate_groups"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)

    # Group metadata
    confidence_score = Column(Float, nullable=False, default=0.0)  # 0.0-1.0, how confident we are these are duplicates
    match_reason = Column(String(255), nullable=True)  # "same_email", "same_domain_name", "similar_company", etc.
    status = Column(String(50), nullable=False, default="pending", index=True)  # "pending", "merged", "resolved", "ignored"
    
    # Canonical lead (the one we keep after merge)
    canonical_lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    organization = relationship("OrganizationORM", back_populates="duplicate_groups")
    workspace = relationship("WorkspaceORM", back_populates="duplicate_groups")
    canonical_lead = relationship("LeadORM", foreign_keys=[canonical_lead_id])
    duplicates = relationship("DuplicateLeadORM", back_populates="group", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_duplicate_groups_org_status", "organization_id", "status"),
        Index("idx_duplicate_groups_confidence", "confidence_score"),
    )


class DuplicateLeadORM(Base):
    """Individual lead in a duplicate group"""
    __tablename__ = "duplicate_leads"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Foreign keys
    duplicate_group_id = Column(Integer, ForeignKey("duplicate_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    # Match metadata
    similarity_score = Column(Float, nullable=False, default=0.0)  # How similar this lead is to the canonical
    matched_fields = Column(JSON, nullable=False, default=list)  # ["email", "name", "website"] - which fields matched

    # Relationships
    group = relationship("DuplicateGroupORM", back_populates="duplicates")
    lead = relationship("LeadORM", back_populates="duplicate_entries")

    __table_args__ = (
        Index("idx_duplicate_leads_group", "duplicate_group_id"),
        Index("idx_duplicate_leads_lead", "lead_id"),
        Index("idx_duplicate_leads_unique", "duplicate_group_id", "lead_id", unique=True),
    )

