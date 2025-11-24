"""Campaign ORM models"""
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Text, func, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db import Base
from app.core.orm import JsonType


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    sending = "sending"
    completed = "completed"
    paused = "paused"
    cancelled = "cancelled"


class TemplateType(str, enum.Enum):
    subject = "subject"
    body = "body"


class CampaignORM(Base):
    """Campaign model"""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    status = Column(Enum(CampaignStatus), nullable=False, default=CampaignStatus.draft, index=True)
    
    # Targeting
    segment_id = Column(Integer, ForeignKey("segments.id", ondelete="SET NULL"), nullable=True)
    list_id = Column(Integer, ForeignKey("lead_lists.id", ondelete="SET NULL"), nullable=True)
    
    # Timing
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    settings = Column(JsonType, nullable=False, default=dict)  # ESP config, tracking, etc.
    
    # Relationships
    workspace = relationship("WorkspaceORM")
    organization = relationship("OrganizationORM")
    segment = relationship("SegmentORM")
    list = relationship("LeadListORM")
    created_by = relationship("UserORM")
    templates = relationship("CampaignTemplateORM", back_populates="campaign", cascade="all, delete-orphan")
    campaign_leads = relationship("CampaignLeadORM", back_populates="campaign", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_campaign_workspace_status", "workspace_id", "status"),
        Index("idx_campaign_org", "organization_id"),
    )


class CampaignTemplateORM(Base):
    """Email template for campaigns (subject or body variants)"""
    __tablename__ = "campaign_templates"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)

    type = Column(Enum(TemplateType), nullable=False, index=True)  # subject or body
    name = Column(String(255), nullable=False)  # "Subject A", "Body v1"
    content = Column(Text, nullable=False)
    
    ai_generated = Column(Boolean, nullable=False, default=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    workspace = relationship("WorkspaceORM")
    campaign = relationship("CampaignORM", back_populates="templates")
    created_by = relationship("UserORM")
    campaign_leads_subject = relationship("CampaignLeadORM", foreign_keys="CampaignLeadORM.subject_template_id", back_populates="subject_template")
    campaign_leads_body = relationship("CampaignLeadORM", foreign_keys="CampaignLeadORM.body_template_id", back_populates="body_template")
    
    __table_args__ = (
        Index("idx_template_campaign_type", "campaign_id", "type"),
    )


class CampaignLeadORM(Base):
    """Junction table for campaigns and leads with outcome tracking"""
    __tablename__ = "campaign_leads"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Template variants used for this send
    subject_template_id = Column(Integer, ForeignKey("campaign_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    body_template_id = Column(Integer, ForeignKey("campaign_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Outcome tracking
    sent = Column(Boolean, nullable=False, default=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    opened = Column(Boolean, nullable=False, default=False, index=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    open_count = Column(Integer, nullable=False, default=0)
    
    clicked = Column(Boolean, nullable=False, default=False, index=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    click_count = Column(Integer, nullable=False, default=0)
    
    replied = Column(Boolean, nullable=False, default=False, index=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    reply_snippet = Column(Text, nullable=True)  # First few lines of reply
    
    bounced = Column(Boolean, nullable=False, default=False, index=True)
    bounced_at = Column(DateTime(timezone=True), nullable=True)
    bounce_reason = Column(Text, nullable=True)
    
    unsubscribed = Column(Boolean, nullable=False, default=False, index=True)
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)
    
    last_event_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    campaign = relationship("CampaignORM", back_populates="campaign_leads")
    lead = relationship("LeadORM")
    subject_template = relationship("CampaignTemplateORM", foreign_keys=[subject_template_id], back_populates="campaign_leads_subject")
    body_template = relationship("CampaignTemplateORM", foreign_keys=[body_template_id], back_populates="campaign_leads_body")
    
    __table_args__ = (
        Index("idx_campaign_lead_unique", "campaign_id", "lead_id", unique=True),
        Index("idx_campaign_lead_sent", "campaign_id", "sent"),
        Index("idx_campaign_lead_replied", "campaign_id", "replied"),
    )

