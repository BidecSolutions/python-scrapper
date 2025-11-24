"""Activity timeline ORM model"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey, 
    Enum as SQLEnum, Text, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.core.db import Base
from app.core.orm import JsonType


class ActivityType(str, PyEnum):
    """Activity event types"""
    # Lead events
    lead_created = "lead_created"
    lead_updated = "lead_updated"
    lead_added_to_list = "lead_added_to_list"
    lead_removed_from_list = "lead_removed_from_list"
    
    # Email events
    email_found = "email_found"
    email_verified = "email_verified"
    
    # Campaign events
    campaign_sent = "campaign_sent"
    campaign_outcome_imported = "campaign_outcome_imported"
    campaign_event = "campaign_event"  # opened / replied / bounced
    
    # Task events
    task_created = "task_created"
    task_completed = "task_completed"
    task_cancelled = "task_cancelled"
    
    # Note events
    note_added = "note_added"
    
    # Playbook events
    playbook_run = "playbook_run"
    playbook_completed = "playbook_completed"
    
    # List events
    list_created = "list_created"
    list_marked_campaign_ready = "list_marked_campaign_ready"
    
    # Job events
    job_created = "job_created"
    job_completed = "job_completed"
    job_failed = "job_failed"
    
    # Integration events
    integration_connected = "integration_connected"
    integration_disconnected = "integration_disconnected"
    
    # Workspace events
    workspace_created = "workspace_created"
    member_invited = "member_invited"
    member_joined = "member_joined"
    
    # Deal events
    deal_created = "deal_created"
    deal_stage_changed = "deal_stage_changed"
    deal_won = "deal_won"
    deal_lost = "deal_lost"
    deal_updated = "deal_updated"


class ActivityORM(Base):
    """Generic activity/event log model"""
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Multi-tenant
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event type
    type = Column(SQLEnum(ActivityType), nullable=False, index=True)
    
    # Actor (who did it, optional for system events)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Related objects (nullable, depending on event type)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True)
    list_id = Column(Integer, ForeignKey("lead_lists.id", ondelete="CASCADE"), nullable=True, index=True)
    campaign_id = Column(Integer, nullable=True, index=True)  # CampaignORM may not exist yet
    task_id = Column(Integer, ForeignKey("lead_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    note_id = Column(Integer, ForeignKey("lead_notes.id", ondelete="CASCADE"), nullable=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Flexible JSON payload for extra info
    meta = Column(JsonType, nullable=False, default=dict)
    # Examples:
    # { "email": "john@acme.com", "status": "valid", "confidence": 0.95 }
    # { "list_name": "LinkedIn – Week 47 Campaign", "leads_count": 243 }
    # { "event": "replied", "campaign_name": "LinkedIn founders – Week 47" }
    
    # Relationships
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])
    organization = relationship("OrganizationORM", foreign_keys=[organization_id])
    actor_user = relationship("UserORM", foreign_keys=[actor_user_id])
    lead = relationship("LeadORM", back_populates="activities")
    list_obj = relationship("LeadListORM", foreign_keys=[list_id])
    task = relationship("LeadTaskORM", foreign_keys=[task_id])
    job = relationship("ScrapeJobORM", foreign_keys=[job_id])
    note = relationship("LeadNoteORM", foreign_keys=[note_id])
    deal = relationship("app.core.orm_deals.DealORM", foreign_keys=[deal_id])
    
    __table_args__ = (
        Index("idx_activity_workspace_created", "workspace_id", "created_at"),
        Index("idx_activity_lead_created", "lead_id", "created_at"),
        Index("idx_activity_type_created", "type", "created_at"),
    )

