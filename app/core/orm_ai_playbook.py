"""AI Playbook Builder ORM models"""
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Text, func, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db import Base
from app.core.orm import JsonType


class PlaybookBlueprintStatus(str, enum.Enum):
    draft = "draft"
    reviewed = "reviewed"
    executing = "executing"
    completed = "completed"
    cancelled = "cancelled"


class AIPlaybookBlueprintORM(Base):
    """AI-generated playbook blueprint"""
    __tablename__ = "ai_playbook_blueprints"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # User's original prompt
    user_prompt = Column(Text, nullable=False)
    
    # AI-generated blueprint (JSON)
    blueprint_json = Column(JsonType, nullable=False)  # Full blueprint structure
    
    status = Column(Enum(PlaybookBlueprintStatus), nullable=False, default=PlaybookBlueprintStatus.draft, index=True)
    
    # Execution results
    segment_id = Column(Integer, ForeignKey("segments.id", ondelete="SET NULL"), nullable=True)
    playbook_id = Column(Integer, ForeignKey("playbook_jobs.id", ondelete="SET NULL"), nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    list_id = Column(Integer, ForeignKey("lead_lists.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspace = relationship("WorkspaceORM")
    organization = relationship("OrganizationORM")
    created_by = relationship("UserORM")
    segment = relationship("SegmentORM")
    playbook = relationship("PlaybookJobORM")
    campaign = relationship("CampaignORM")
    list = relationship("LeadListORM")
    
    __table_args__ = (
        Index("idx_playbook_blueprint_workspace_status", "workspace_id", "status"),
        Index("idx_playbook_blueprint_org", "organization_id"),
    )

