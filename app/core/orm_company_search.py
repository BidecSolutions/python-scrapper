"""Company Search Job ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey, 
    Enum as SQLEnum, Text, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.core.db import Base
from app.core.orm import JsonType


class CompanySearchJobStatus(str, PyEnum):
    """Company search job status"""
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class CompanySearchJobORM(Base):
    """Company search job"""
    __tablename__ = "company_search_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)  # Workspace for team collaboration
    
    # Job info
    status = Column(String(20), nullable=False, default=CompanySearchJobStatus.queued.value, index=True)
    error_message = Column(Text, nullable=True)
    
    # Search parameters (JSON)
    params = Column(JsonType, nullable=False, default=dict)  # {query, roles, min_company_size, max_company_size, country, list_name, max_leads}
    
    # Progress tracking (meta JSON)
    meta = Column(JsonType, nullable=False, default=dict)  # {estimated_leads, leads_found, emails_found, emails_verified, list_id}
    
    # Output
    output_list_id = Column(Integer, ForeignKey("lead_lists.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    output_list = relationship("LeadListORM", foreign_keys=[output_list_id])
    company = relationship("CompanyORM", foreign_keys=[company_id])
    
    __table_args__ = (
        Index("idx_company_search_org_status", "organization_id", "status"),
        Index("idx_company_search_created", "created_at"),
    )

