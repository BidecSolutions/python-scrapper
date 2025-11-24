"""Health & Quality metrics ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, func, ForeignKey, 
    Numeric, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db import Base
from app.core.orm import JsonType


class WorkspaceDailyMetricsORM(Base):
    """Daily aggregated metrics per workspace"""
    __tablename__ = "workspace_daily_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)  # YYYY-MM-DD
    
    # Email sending
    emails_sent = Column(Integer, nullable=False, default=0)
    emails_bounced = Column(Integer, nullable=False, default=0)
    emails_spam_complaints = Column(Integer, nullable=False, default=0)
    emails_unsubscribed = Column(Integer, nullable=False, default=0)
    
    # Verification
    emails_verified = Column(Integer, nullable=False, default=0)
    ver_valid = Column(Integer, nullable=False, default=0)
    ver_invalid = Column(Integer, nullable=False, default=0)
    ver_risky = Column(Integer, nullable=False, default=0)
    ver_unknown = Column(Integer, nullable=False, default=0)
    
    # Campaigns
    campaign_sends = Column(Integer, nullable=False, default=0)
    campaign_opens = Column(Integer, nullable=False, default=0)
    campaign_replies = Column(Integer, nullable=False, default=0)
    
    # LinkedIn / scraping
    linkedin_success = Column(Integer, nullable=False, default=0)
    linkedin_failed = Column(Integer, nullable=False, default=0)
    
    # Jobs
    jobs_started = Column(Integer, nullable=False, default=0)
    jobs_failed = Column(Integer, nullable=False, default=0)
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    
    __table_args__ = (
        Index("idx_workspace_daily_metrics_workspace_date", "workspace_id", "date", unique=True),
    )


class WorkspaceHealthSnapshotORM(Base):
    """Health score snapshots per workspace"""
    __tablename__ = "workspace_health_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    health_score = Column(Integer, nullable=False)  # 0-100
    details = Column(JsonType, nullable=True)  # Breakdown: {"bounce_rate": 0.05, "verification_quality": 0.72, ...}
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    
    __table_args__ = (
        Index("idx_workspace_health_workspace_date", "workspace_id", "date", unique=True),
    )

